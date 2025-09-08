from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    native_language = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.Date)



class User_Languages(db.Model):
    __tablename__ = 'user_languages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language_code = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.Date)


class Sentences(db.Model):
    __tablename__ = 'sentences'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_text = db.Column(db.String(200), nullable=False)
    language_code = db.Column(db.String(5), nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.Date)


class Translations(db.Model):
    __tablename__ = 'translations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id'), nullable=False)
    translated_text = db.Column(db.String(200))
    target_language_code = db.Column(db.String(5))
    created_at = db.Column(db.Date)
    group_id = db.Column(db.Integer, db.ForeignKey('progress_groups.id'))


class Learning_Progress(db.Model):
    __tablename__ = 'learning_progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    translation_id = db.Column(db.Integer, db.ForeignKey('translations.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('progress_groups.id'))
    score = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.Date)
    next_review = db.Column(db.Date)
    review_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Integer, default=0)
    # every user has for every translation only one progressdataset
    __table_args__ = (db.UniqueConstraint('user_id', 'translation_id'),)

class Progress_Groups(db.Model):
    __tablename__ = 'progress_groups'
    id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_score = db.Column(db.Float, default=0.0)
    next_review = db.Column(db.Date)
    last_reviewed = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



