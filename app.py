from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from datetime import datetime
from data_models import db
from data_manager import DataManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# api = Api(app)

app.config['SWAGGER'] = {
	'title': 'My API',
	'uiversion': 3
}
swagger = Swagger(app)

# Link database and app
db.init_app(app)
print("TEST")

with app.app_context():
	db.create_all()

manager = DataManager(db)

# TODO pydentic nutzen
# @app.route('/')
# def index():
#     """Render the index page for test-reasons to see all users"""
#     users = manager.get_users()
#     print(f"Users found: {users}")
#     return jsonify(users)

@app.route('/')
def index():
	"""
	Get all users
	---
	tags:
	  - Users
	summary: List all users
	description: Returns a list of all user profiles.
	responses:
	  200:
		description: A list of user objects
		schema:
		  type: array
		  items:
			type: object
			properties:
			  id:
				type: integer
			  username:
				type: string
			  native_language:
				type: string
			  created_at:
				type: string
	"""
	users = manager.get_users()
	return jsonify(users), 200

@app.route('/api/user', methods=['POST'])
def create_user():
	"""
	Creates a User profile
	---
	tags:
	  - Users
	summary: Create a new user
	description: Creates a new user profile and returns the user details.
	parameters:
	  - name: username
		in: formData
		type: string
		required: true
		description: The name of the user
	  - name: native_language
		in: formData
		type: string
		required: true
		description: The user's native language
	responses:
	  201:
		description: User created successfully
		schema:
		  type: object
		  properties:
			id:
			  type: integer
			username:
			  type: string
			native_language:
			  type: string
			created_at:
			  type: string
	"""
	username = request.form['username']
	native_language = request.form['native_language']
	# TODO maybe also "N-Target languages" from a form
	user = manager.create_user(username, native_language)
	return jsonify({
		'id': user.id,
		'username': user.username,
		'native_language': user.native_language,
		'created_at': user.created_at.isoformat() if user.created_at else None
	}), 201

@app.route('/user/<int:user_id>/languages', methods=['POST'])
def add_user_languages(user_id):
	"""
	REST-Prinzip
     /user/123/languages/fr ist idempotent

        Mehrmaliges Aufrufen hat den gleichen Effekt wie einmaliges Aufrufen

        Wenn Französisch schon existiert → Error, sonst wird es hinzugefügt
	"""
	language_code = request.form['language_to_learn']
	lang = manager.add_target_language(user_id, language_code)
	return jsonify({
		'id': lang.id,
		'user_id': lang.user_id,
		'language_code': lang.language_code,
		'created_at': lang.created_at.isoformat() if lang.created_at else None
	}), 201

@app.route('/user/<int:user_id>/languages', methods=['GET'])
def get_user_languages(user_id):
	user_languages = manager.get_user_languages(user_id)
	list_user_languages = []
	for lang in user_languages:
		list_user_languages.append({
			'id': lang.id,
			'user_id': lang.user_id,
			'language_code': lang.language_code,
			'created_at': lang.created_at.isoformat() if lang.created_at else None
		})
	return jsonify(list_user_languages)

@app.route('/api/sentences', methods=['POST'])
def add_sentences():
	original_text = request.form['original_text']
	user_id = request.form['user_id']
	category = request.form['category']
	user = manager.get_user_by_id(user_id)
	sentence_db = manager.create_sentence(user_id, original_text, category)
	return jsonify({
		'id': sentence_db.id,
		'user_id': sentence_db.user_id,
		'original_text': sentence_db.original_text,
		'language_code': sentence_db.language_code,
		'category': sentence_db.created_at.isoformat() if sentence_db.created_at else None
	})
if __name__ == '__main__':
	app.run(host="0.0.0.0", port=5002, debug=True)