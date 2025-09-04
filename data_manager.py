from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
from data_models import db, User, User_Languages, Sentences, Translations, Learning_Progress


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

    def get_user(self, user_id):
        return User.query.get(user_id)

    def add_target_language(self, user_id, language_code):
        if not self.get_user(user_id):
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
    def create_sentence(self, user_id, original_text, category=None):
        user = self.get_user(user_id)
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
            # Cascade delete translations and progress? Or handle explicitly.
            self.db.session.delete(sentence)
            self._commit()
            return True
        return False

        # Translations Management (AI call would happen in app.py or service layer)
    def create_translation(self, sentence_id, translated_text, target_language, confidence=None):
        sentence = Sentences.query.get(sentence_id)
        if not sentence:
            raise ValueError("Sentence not found")
        translation = Translations(
            sentence_id=sentence_id,
            translated_text=translated_text,
            target_language_code=target_language,
            created_at=datetime.utcnow()
        )
        if confidence:
            translation.translation_confidence = confidence  # Add this field to model if missing
        self.db.session.add(translation)
        self._commit()
        # Also create initial Learning_Progress
        self.create_learning_progress(sentence.user_id, translation.id)
        return translation

    # Learning Progress
    def create_learning_progress(self, user_id, translation_id):
        if Learning_Progress.query.filter_by(user_id=user_id, translation_id=translation_id).first():
            return  # Already exists
        progress = Learning_Progress(
            user_id=user_id,
            translation_id=translation_id,
            score=0.0,  # Use float
            last_reviewed=None,
            next_review=datetime.utcnow().date(),
            review_count=0,
            success_rate=0.0,
            # Add: ease_factor=2.5, interval_days=1, repetitions=0
        )
        self.db.session.add(progress)
        self._commit()
        return progress

    def update_learning_progress(self, translation_id, new_score, is_success):
        progress = Learning_Progress.query.filter_by(translation_id=translation_id).first()
        if not progress:
            raise ValueError("Progress not found")
        progress.score = new_score
        progress.review_count += 1
        progress.success_rate = ((progress.success_rate * (progress.review_count - 1)) + (100 if is_success else 0)) / progress.review_count
        progress.last_reviewed = datetime.utcnow()
        # Simple interval update (expand with Anki logic or AI)
        if is_success:
            progress.next_review = progress.last_reviewed + timedelta(days=progress.interval_days * 2)  # Example
        else:
            progress.next_review = progress.last_reviewed + timedelta(days=1)
        self._commit()
        return progress

    def get_due_reviews(self, user_id):
        today = datetime.utcnow().date()
        return Learning_Progress.query.filter(and_(Learning_Progress.user_id == user_id, Learning_Progress.next_review <= today)).all()

    def get_learning_stats(self, user_id):
        stats = {
            'total_reviews': Learning_Progress.query.filter_by(user_id=user_id).count(),
            'avg_success_rate': db.session.query(func.avg(Learning_Progress.success_rate)).filter_by(user_id=user_id).scalar() or 0,
            # Add more: e.g., by category via joins
        }
        return stats

    # Additional: For Anki scheduling (call AI with all progress data, then update next_review etc.)
    def schedule_reviews(self, user_id, ai_schedule_data):
        # ai_schedule_data: list of dicts from LLM JSON
        for item in ai_schedule_data:
            progress = Learning_Progress.query.filter_by(translation_id=item['translation_id']).first()
            if progress:
                progress.next_review = datetime.strptime(item['next_review'], '%Y-%m-%d').date()
                # Update other fields like priority if added
        self._commit()