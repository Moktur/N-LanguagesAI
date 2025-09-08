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

app.config['SWAGGER'] = {
    'title': 'N-LanguagesAI API',
    'uiversion': 3,
    'description': 'API for multilingual language learning application'
}
swagger = Swagger(app)

# Link database and app
db.init_app(app)

with app.app_context():
    db.create_all()

manager = DataManager(db)

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

# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.route('/api/users', methods=['POST'])
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
      400:
        description: Invalid input
    """
    try:
        username = request.form.get('username')
        native_language = request.form.get('native_language')
        
        if not username or not native_language:
            return jsonify({'error': 'Username and native_language are required'}), 400
            
        user = manager.create_user(username, native_language)
        return jsonify({
            'id': user.id,
            'username': user.username,
            'native_language': user.native_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user details
    ---
    tags:
      - Users
    summary: Get user by ID
    description: Returns details of a specific user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user to retrieve
    responses:
      200:
        description: User details
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
      404:
        description: User not found
    """
    user = manager.get_user_by_id(user_id)
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'native_language': user.native_language,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<int:user_id>/languages/<string:language_code>', methods=['POST'])
def add_user_language(user_id, language_code):
    """
    Add a target language to a user
    ---
    tags:
      - Users
    summary: Add target language
    description: Adds a target language to a user's profile.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
      - name: language_code
        in: path
        type: string
        required: true
        description: Language code to add (e.g., 'fr', 'es')
    responses:
      201:
        description: Language added successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            user_id:
              type: integer
            language_code:
              type: string
            created_at:
              type: string
      400:
        description: Invalid input or language already added
      404:
        description: User not found
    """
    try:
        lang = manager.add_target_language(user_id, language_code)
        return jsonify({
            'id': lang.id,
            'user_id': lang.user_id,
            'language_code': lang.language_code,
            'created_at': lang.created_at.isoformat() if lang.created_at else None
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/users/<int:user_id>/languages', methods=['GET'])
def get_user_languages(user_id):
    """
    Get user's target languages
    ---
    tags:
      - Users
    summary: Get user languages
    description: Returns all target languages for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of user's target languages
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              language_code:
                type: string
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        user_languages = manager.get_user_languages(user_id)
        languages_list = []
        for lang in user_languages:
            languages_list.append({
                'id': lang.id,
                'user_id': lang.user_id,
                'language_code': lang.language_code,
                'created_at': lang.created_at.isoformat() if lang.created_at else None
            })
        return jsonify(languages_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SENTENCES MANAGEMENT ENDPOINTS ====================

@app.route('/api/sentences', methods=['POST'])
def add_sentence():
    """
    Create a new sentence
    ---
    tags:
      - Sentences
    summary: Create a sentence
    description: Creates a new sentence with category and generates translations for all target languages.
    parameters:
      - name: user_id
        in: formData
        type: integer
        required: true
        description: ID of the user
      - name: original_text
        in: formData
        type: string
        required: true
        description: The sentence text
      - name: category
        in: formData
        type: string
        required: true
        description: Category for the sentence
    responses:
      201:
        description: Sentence created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            user_id:
              type: integer
            original_text:
              type: string
            language_code:
              type: string
            category:
              type: string
            created_at:
              type: string
      400:
        description: Invalid input
      404:
        description: User not found
    """
    try:
        original_text = request.form.get('original_text')
        user_id = request.form.get('user_id')
        category = request.form.get('category')
        
        if not all([original_text, user_id, category]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Create sentence
        sentence = manager.create_sentence(user_id, original_text, category)
        
        # Create progress group for this sentence
        group = manager.create_progress_group(sentence.id, user_id)
        
        # Get user's target languages
        user_languages = manager.get_user_languages(user_id)
        
        # For each target language, create translation (AI would generate these)
        # This is a placeholder - you would call your AI service here
        for lang in user_languages:
            # In a real implementation, you would call an AI translation service
            translated_text = f"Translation of '{original_text}' to {lang.language_code}"
            manager.create_translation(
                sentence.id, 
                translated_text, 
                lang.language_code, 
                group.id
            )
        
        return jsonify({
            'id': sentence.id,
            'user_id': sentence.user_id,
            'original_text': sentence.original_text,
            'language_code': sentence.language_code,
            'category': sentence.category,
            'created_at': sentence.created_at.isoformat() if sentence.created_at else None
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Server error: ' + str(e)}), 500

@app.route('/api/sentences/<int:user_id>', methods=['GET'])
def get_sentences(user_id):
    """
    Get all sentences for a user
    ---
    tags:
      - Sentences
    summary: Get user sentences
    description: Returns all sentences for a specific user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of user's sentences
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              original_text:
                type: string
              language_code:
                type: string
              category:
                type: string
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        sentences = manager.get_sentences_for_user(user_id)
        sentences_list = []
        for sentence in sentences:
            sentences_list.append({
                'id': sentence.id,
                'user_id': sentence.user_id,
                'original_text': sentence.original_text,
                'language_code': sentence.language_code,
                'category': sentence.category,
                'created_at': sentence.created_at.isoformat() if sentence.created_at else None
            })
        return jsonify(sentences_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentences/<int:user_id>/category/<string:category>', methods=['GET'])
def get_sentences_by_category(user_id, category):
    """
    Get sentences by category for a user
    ---
    tags:
      - Sentences
    summary: Get sentences by category
    description: Returns all sentences for a user in a specific category.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
      - name: category
        in: path
        type: string
        required: true
        description: Category to filter by
    responses:
      200:
        description: List of sentences in the category
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              original_text:
                type: string
              language_code:
                type: string
              category:
                type: string
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        sentences = manager.get_sentences_by_category(user_id, category)
        sentences_list = []
        for sentence in sentences:
            sentences_list.append({
                'id': sentence.id,
                'user_id': sentence.user_id,
                'original_text': sentence.original_text,
                'language_code': sentence.language_code,
                'category': sentence.category,
                'created_at': sentence.created_at.isoformat() if sentence.created_at else None
            })
        return jsonify(sentences_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentences/<int:sentence_id>', methods=['DELETE'])
def delete_sentence(sentence_id):
    """
    Delete a sentence
    ---
    tags:
      - Sentences
    summary: Delete a sentence
    description: Deletes a sentence and all its associated translations.
    parameters:
      - name: sentence_id
        in: path
        type: integer
        required: true
        description: ID of the sentence to delete
    responses:
      200:
        description: Sentence deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      404:
        description: Sentence not found
    """
    success = manager.delete_sentence(sentence_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Sentence not found'}), 404



# ==================== LEARNING MANAGEMENT ENDPOINTS ====================

@app.route('/api/learn/user/<int:user_id>/due', methods=['GET'])
def get_due_reviews(user_id):
    """
    Get due progress groups for a user
    ---
    tags:
      - Learning
    summary: Get due reviews
    description: Returns all progress groups that are due for review for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: List of due progress groups
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              sentence_id:
                type: integer
              user_id:
                type: integer
              group_score:
                type: number
              next_review:
                type: string
              last_reviewed:
                type: string
              review_count:
                type: integer
              created_at:
                type: string
      404:
        description: User not found
    """
    try:
        due_groups = manager.get_due_progress_groups(user_id)
        groups_list = []
        for group in due_groups:
            groups_list.append({
                'id': group.id,
                'sentence_id': group.sentence_id,
                'user_id': group.user_id,
                'group_score': group.group_score,
                'next_review': group.next_review.isoformat() if group.next_review else None,
                'last_reviewed': group.last_reviewed.isoformat() if group.last_reviewed else None,
                'review_count': group.review_count,
                'created_at': group.created_at.isoformat() if group.created_at else None
            })
        return jsonify(groups_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/learn/stats/<int:user_id>', methods=['GET'])
def get_learning_stats(user_id):
    """
    Get learning statistics for a user
    ---
    tags:
      - Learning
    summary: Get learning stats
    description: Returns learning statistics for a user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: User learning statistics
        schema:
          type: object
          properties:
            total_reviews:
              type: integer
            avg_success_rate:
              type: number
      404:
        description: User not found
    """
    try:
        stats = manager.get_learning_stats(user_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)