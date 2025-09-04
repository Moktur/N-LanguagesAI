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
            ## Cascade delete translations and progress? Or handle explicitly.
            self.db.session.delete(sentence)
            self._commit()
            return True
        return False

