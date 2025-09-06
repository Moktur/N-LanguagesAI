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
    print(f"Users found: {users}")
    return jsonify(users)

@app.route('/create_user', methods=['POST'])
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
    user = manager.create_user(username, native_language)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'native_language': user.native_language,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 201


# @app.route('/create_user', methods=['POST'])
# def create_user():
#     """Creates a User profile"""
#     username = request.form['username']
#     native_language = request.form['native_language']
#     user = manager.create_user(username, native_language)
#     # Return created user data
#     return jsonify({
#         'id': user.id,
#         'username': user.username,
#         'native_language': user.native_language,
#         'created_at': user.created_at.isoformat() if user.created_at else None
#     }), 201


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)