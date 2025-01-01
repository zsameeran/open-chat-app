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
            if user.get('nickname', '').startswith(query).lower():
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


@main.route('/add_friend', methods=['POST'])
def add_friend():
    """
    Adds a friend relationship between two users.
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_id = data.get('friendId')

        if not user_id or not friend_id:
            return jsonify({"error": "userId and friendId are required"}), 400

        # Create a friendship document
        friendship_id = f"{user_id}_{friend_id}"  # Unique ID for the friendship
        reverse_friendship_id = f"{friend_id}_{user_id}"  # For bidirectional check

        # Check if friendship already exists (bidirectional)
        existing_friendship = db.collection('user_friends').document(friendship_id).get()
        reverse_friendship = db.collection('user_friends').document(reverse_friendship_id).get()

        if existing_friendship.exists or reverse_friendship.exists:
            return jsonify({"message": "Friendship already exists"}), 200

        # Add friendship document
        db.collection('user_friends').document(friendship_id).set({
            "userId1": user_id,
            "userId2": friend_id,
            "status": "pending",  # initial status
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Friend request sent"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/get_friends/<user_id>', methods=['GET'])
def get_friends(user_id):
    """
    Retrieves a list of friends for a specific user.
    """
    try:
        # Query the `user_friends` collection
        friends_ref = db.collection('user_friends').where("userId1", "==", user_id).where("status", "==", "accepted").stream()
        reverse_friends_ref = db.collection('user_friends').where("userId2", "==", user_id).where("status", "==", "accepted").stream()

        friends = []

        for friend_doc in friends_ref:
            friend_data = friend_doc.to_dict()
            friends.append(friend_data["userId2"])  # Add the other user ID

        for reverse_friend_doc in reverse_friends_ref:
            reverse_friend_data = reverse_friend_doc.to_dict()
            friends.append(reverse_friend_data["userId1"])  # Add the other user ID

        return jsonify({"friends": friends}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/respond_friend_request', methods=['POST'])
def respond_friend_request():
    """
    Responds to a friend request (accept or reject).
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_id = data.get('friendId')
        action = data.get('action')  # "accept" or "reject"

        if not user_id or not friend_id or action not in ["accept", "reject"]:
            return jsonify({"error": "Invalid input"}), 400

        # Find the friendship document
        friendship_id = f"{friend_id}_{user_id}"  # Reverse ID for checking friend requests
        friendship_doc = db.collection('user_friends').document(friendship_id).get()

        if not friendship_doc.exists:
            return jsonify({"error": "Friend request not found"}), 404

        if action == "accept":
            db.collection('user_friends').document(friendship_id).update({
                "status": "accepted"
            })
            return jsonify({"message": "Friend request accepted"}), 200

        elif action == "reject":
            db.collection('user_friends').document(friendship_id).delete()
            return jsonify({"message": "Friend request rejected"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @main.route('/user/<user_id>', methods=['GET'])
# def get_user_profile(user_id):
#     #user_ref = db.collection('users').document(user_id)
#     doc = user_ref.get()

#     if doc.exists:
#         return jsonify(doc.to_dict()), 200
#     return jsonify({'message': 'User not found'}), 404
