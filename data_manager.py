from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
from data_models import db, User, User_Languages, Sentences, Translations, Learning_Progress, Progress_Groups


class DataManager:
    def __init__(self, db):
        self.db = db

    def _commit(self):
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e

    # User Management
    def create_user(self, username, native_language):
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        user = User(username=username, native_language=native_language, created_at=datetime.utcnow())
        self.db.session.add(user)
        self._commit()
        return user

    def get_user_by_id(self, user_id):
        return User.query.get(user_id)

    def get_user_by_username(self, username):
        return User.query.filter_by(username=username).first()

    # get all users for test reasons
    def get_users(self):
        users = User.query.all()
        return [{
            'id': user.id,
            'username': user.username,
            'native_language': user.native_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]

    def add_target_language(self, user_id, language_code):
        if not self.get_user_by_id(user_id):
            raise ValueError("User not found")
        if User_Languages.query.filter_by(user_id=user_id, language_code=language_code).first():
            raise ValueError("Language already added")
        lang = User_Languages(user_id=user_id, language_code=language_code, created_at=datetime.utcnow())
        self.db.session.add(lang)
        self._commit()
        return lang

    def get_user_languages(self, user_id):
        return User_Languages.query.filter_by(user_id=user_id).all()

    # Sentences Management

    def get_user_categories(self, user_id):
    # Gibt alle eindeutigen Kategorien eines Benutzers zurück
    categories = Sentences.query.filter_by(user_id=user_id).with_entities(Sentences.category).distinct().all()
    return [category[0] for category in categories if category[0]]

    def create_sentence(self, user_id, original_text, category=None):
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        sentence = Sentences(
            user_id=user_id,
            original_text=original_text,
            language_code=user.native_language,
            category=category,
            created_at=datetime.utcnow()
        )
        self.db.session.add(sentence)
        self._commit()
        return sentence

    def get_sentences_for_user(self, user_id):
        return Sentences.query.filter_by(user_id=user_id).all()

    def get_sentences_by_category(self, user_id, category):
        return Sentences.query.filter_by(user_id=user_id, category=category).all()

    def delete_sentence(self, sentence_id):
        sentence = Sentences.query.get(sentence_id)
        if sentence:
            # delete all dependent translations
            Translations.query.filter_by(sentence_id=sentence_id).delete()
            Progress_Groups.query.filter_by(sentence_id=sentence_id).delete()
            self.db.session.delete(sentence)
            self._commit()
            return True
        return False


    def delete_user(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Lösche alle abhängigen Daten in der richtigen Reihenfolge
        # Learning_Progress User
        Learning_Progress.query.filter_by(user_id=user_id).delete()
        
        # User_Languages User
        User_Languages.query.filter_by(user_id=user_id).delete()
        
        # all Sentences User
        user_sentences = Sentences.query.filter_by(user_id=user_id).all()
        
        # Deleting Translations and Progress
        for sentence in user_sentences:
            Translations.query.filter_by(sentence_id=sentence.id).delete()
            Progress_Groups.query.filter_by(sentence_id=sentence.id).delete()
            self.db.session.delete(sentence)
        
        # Delete user
        self.db.session.delete(user)
        self._commit()
        return True
            

    # Translations Management
    def create_translation(self, sentence_id, translated_text, target_language, group_id, confidence=None):
        sentence = Sentences.query.get(sentence_id)
        if not sentence:
            raise ValueError("Sentence not found")
        translation = Translations(
            sentence_id=sentence_id,
            translated_text=translated_text,
            target_language_code=target_language,
            group_id=group_id,
            created_at=datetime.utcnow()
        )
        if confidence:
            translation.translation_confidence = confidence
        self.db.session.add(translation)
        self._commit()
        # progress will be administrated on group level
        return translation

    def get_translations_by_sentence(self, sentence_id):
    return Translations.query.filter_by(sentence_id=sentence_id).all()

    def get_translations_by_group(self, group_id):
        return Translations.query.filter_by(group_id=group_id).all()

    # Progress Groups Management
    def create_progress_group(self, sentence_id, user_id):
        group = Progress_Groups(
            sentence_id=sentence_id,
            user_id=user_id,
            group_score=0.0,
            next_review=datetime.utcnow().date(),
            created_at=datetime.utcnow()
        )
        self.db.session.add(group)
        self._commit()
        return group

    def get_progress_group(self, group_id):
        return Progress_Groups.query.get(group_id)

    def get_due_progress_groups(self, user_id):
        today = datetime.utcnow().date()
        return Progress_Groups.query.filter(
            and_(Progress_Groups.user_id == user_id, 
                 Progress_Groups.next_review <= today)
        ).all()

    def update_progress_group(self, group_id, group_score, is_success):
        group = Progress_Groups.query.get(group_id)
        if not group:
            raise ValueError("Progress group not found")
        
        group.group_score = group_score
        group.review_count += 1
        group.last_reviewed = datetime.utcnow()
        
        # simple anki logic
        if is_success:
            # make the learningintervall bigger
            interval_days = max(1, group.review_count * 2)
        else:
            # make the learningintervall smaller
            interval_days = 1
            
        group.next_review = (datetime.utcnow() + timedelta(days=interval_days)).date()
        self._commit()
        return group

    # Learning Progress 
    def create_learning_progress(self, user_id, group_id):
        if Learning_Progress.query.filter_by(user_id=user_id, group_id=group_id).first():
            return 
            
        progress = Learning_Progress(
            user_id=user_id,
            group_id=group_id,
            score=0.0,
            last_reviewed=None,
            next_review=datetime.utcnow().date(),
            review_count=0,
            success_rate=0.0
        )
        self.db.session.add(progress)
        self._commit()
        return progress

    def update_learning_progress(self, group_id, new_score, is_success):
        progress = Learning_Progress.query.filter_by(group_id=group_id).first()
        if not progress:
            raise ValueError("Progress not found")
            
        progress.score = new_score
        progress.review_count += 1
        progress.success_rate = ((progress.success_rate * (progress.review_count - 1)) + (100 if is_success else 0)) / progress.review_count
        progress.last_reviewed = datetime.utcnow()
        
        # simple Intervalllogic
        if is_success:
            progress.next_review = progress.last_reviewed + timedelta(days=progress.review_count * 2)
        else:
            progress.next_review = progress.last_reviewed + timedelta(days=1)
            
        self._commit()
        return progress

    def get_learning_stats(self, user_id):
        stats = {
            'total_reviews': Learning_Progress.query.filter_by(user_id=user_id).count(),
            'avg_success_rate': db.session.query(func.avg(Learning_Progress.success_rate)).filter_by(user_id=user_id).scalar() or 0,
        }
        return stats

    # Helpermethods
    def get_translations_for_group(self, group_id):
        return Translations.query.filter_by(group_id=group_id).all()

    def get_group_for_sentence(self, sentence_id):
        return Progress_Groups.query.filter_by(sentence_id=sentence_id).first()