from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from datetime import datetime
from src.server.models.data_models import db
from data_manager import DataManager
from src.server.api.routes import api_bp



def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SWAGGER'] = {
        'title': 'N-LanguagesAI API',
        'uiversion': 3,
        'description': 'API for multilingual language learning application'
    }
    # create data manager for the app
    app.manager = DataManager()

    # initial extensions
    swagger = Swagger(app)
    db.init_app(app)

    # register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # import models for database creation
    from src.server.models import data_models
    with app.app_context():
        db.create_all()
        

    return app