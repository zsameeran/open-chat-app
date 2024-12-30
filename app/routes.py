from flask import Blueprint, request, jsonify
#from .firebase_config import db
from google.cloud import firestore

main = Blueprint('main', __name__)

db = firestore.Client(project = "open-chat-app-446105" ,  database = "user-data")

################## USER REGISTRATION #########################################
@main.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    user_id = data.get('userId')
    nickname = data.get('nickname')
    gender = data.get('gender')

    if not user_id or not nickname or not gender:
        return jsonify({'message': 'Missing fields'}), 400

    try:
        # Firestore reference
        user_ref = db.collection('users-profiles').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            return jsonify({'message': 'User already registered'}), 400

        # Add user data to Firestore
        user_ref.set({
            'userId': user_id,
            'nickname': nickname,
            'gender': gender,
        })

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

################## CODE FOR FRIEND SEARCH #########################################


@main.route('/search_users', methods=['POST'])
def search_users():
    try:
        # Parse query from request JSON
        data = request.json
        query = data.get('query', '').lower()  # Search term
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        # Firestore Query
        users_ref = db.collection('users-profiles')  # Firestore collection name
        docs = users_ref.stream()

        # Search logic: Match query in nickname or gender
        results = []
        for doc in docs:
            user = doc.to_dict()
            if query in user.get('nickname', '').lower():
                results.append({
                    "userId": user.get('userId'),
                    "nickname": user.get('nickname'),
                    "gender": user.get('gender'),
                })

        # Return results
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/test-firestore', methods=['GET'])
def test_firestore():
    try:
        collections = [col.id for col in db.collections()]
        return jsonify({"message": "Connected to Firestore", "collections": collections}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @main.route('/user/<user_id>', methods=['GET'])
# def get_user_profile(user_id):
#     #user_ref = db.collection('users').document(user_id)
#     doc = user_ref.get()

#     if doc.exists:
#         return jsonify(doc.to_dict()), 200
#     return jsonify({'message': 'User not found'}), 404
