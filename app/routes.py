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
            if user.get('nickname', '').lower().startswith(query):
                results.append({
                    "userId": user.get('userId'),
                    "nickname": user.get('nickname'),
                    "gender": user.get('gender'),
                })

        # Return results
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/health-check', methods=['GET'])
def test_firestore():
    try:
        collections = [col.id for col in db.collections()]
        return jsonify({"message": "Connected to Firestore", "collections": collections}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/add_friend', methods=['POST'])
def add_friend():
    """
    Adds a friend relationship by updating subcollections under each user's profile document.
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_id = data.get('friendId')

        if not user_id or not friend_id:
            return jsonify({"error": "userId and friendId are required"}), 400

        # Firestore references for the users
        user_ref = db.collection('users-profiles').document(user_id).collection('my-friends').document(friend_id)
        friend_ref = db.collection('users-profiles').document(friend_id).collection('my-friends').document(user_id)

        # Check if friendship already exists (bidirectional)
        user_friendship = user_ref.get()
        friend_friendship = friend_ref.get()

        if user_friendship.exists or friend_friendship.exists:
            return jsonify({"message": "Friendship already exists or request already sent"}), 200

        # Add friendship documents in both users' subcollections
        user_ref.set({
            "friendId": friend_id,
            "status": "Request Sent",  # Initial status
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        friend_ref.set({
            "friendId": user_id,
            "status": "requested",  # Shows this user received the request
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Friend request sent"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

        
@main.route('/get_friends/<user_id>', methods=['GET'])
def get_friends(user_id):
    """
    Retrieves a list of friends for a specific user by querying `myfriends` subcollection
    and supplementing the data from `user_profiles`.
    """
    try:
        # Access the `myfriends` subcollection
        friends_ref = db.collection('users-profiles').document(user_id).collection('my-friends').stream()

        friends = []

        for friend_doc in friends_ref:
            friend_data = friend_doc.to_dict()
            friend_id = friend_data.get("friendId")  # ID of the friend

            # Fetch additional details about the friend from `user_profiles`
            friend_profile_ref = db.collection('users-profiles').document(friend_id).get()
            if friend_profile_ref.exists:
                friend_profile_data = friend_profile_ref.to_dict()
                friends.append({
                    "userId": friend_id,
                    "nickname": friend_profile_data.get("nickname", "Unknown"),
                    "avatarUrl": friend_profile_data.get("avatarUrl", ""),
                    "gender":friend_profile_data.get("gender", ""),
                    "status": friend_data.get("status", "Unknown"),
                    "timestamp": friend_data.get("createdAt", ""),
                })
            else:
                # Friend profile does not exist, handle gracefully
                friends.append({
                    "id": friend_id,
                    "name": "Unknown",
                    "avatarUrl": "",
                    "status": friend_data.get("status", "Unknown"),
                    "timestamp": friend_data.get("timestamp", ""),
                })

        return jsonify({"friends": friends}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/respond_friend_request', methods=['POST'])
def respond_friend_request():
    """
    Responds to a friend request by updating or deleting the friendship in both users' subcollections.
    Accepts or rejects a friend request.
    """
    try:
        data = request.json
        user_id = data.get('userId')  # The user responding to the request
        friend_id = data.get('friendId')  # The user who sent the request
        response = data.get('response')  # Either 'Accepted' or 'Rejected'

        if not user_id or not friend_id or not response:
            return jsonify({"error": "userId, friendId, and response are required"}), 400

        if response not in ["Accepted", "Rejected"]:
            return jsonify({"error": "Invalid response value. Use 'Accepted' or 'Rejected'"}), 400

        # Firestore references for both users' friendship documents
        user_ref = db.collection('users-profiles').document(user_id).collection('my-friends').document(friend_id)
        friend_ref = db.collection('users-profiles').document(friend_id).collection('my-friends').document(user_id)

        # Fetch the existing friendship documents
        user_friendship = user_ref.get()
        friend_friendship = friend_ref.get()

        if not user_friendship.exists or not friend_friendship.exists:
            return jsonify({"error": "Friendship request does not exist"}), 404

        # Handle response
        if response == "Accepted":
            user_ref.update({
                "status": "Accepted",
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            friend_ref.update({
                "status": "Accepted",
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            message = "Friend request accepted"
        elif response == "Rejected":
            # Delete friendship documents
            user_ref.delete()
            friend_ref.delete()
            message = "Friend request rejected and removed"

        return jsonify({"message": message}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@main.route('/delete_friends', methods=['POST'])
def delete_friends():
    """
    Deletes multiple friends by removing their relationships from the `my-friends` subcollection
    for both the user and the specified friends.
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_ids = data.get('friendIds')  # List of friend IDs to delete

        if not user_id or not friend_ids or not isinstance(friend_ids, list):
            return jsonify({"error": "userId and a non-empty list of friendIds are required"}), 400

        batch = db.batch()  # Batch write for Firestore operations

        for friend_id in friend_ids:
            # Firestore references for both users' friendship documents
            user_ref = db.collection('users-profiles').document(user_id).collection('my-friends').document(friend_id)
            friend_ref = db.collection('users-profiles').document(friend_id).collection('my-friends').document(user_id)

            # Delete the documents in a batch
            batch.delete(user_ref)
            batch.delete(friend_ref)

        # Commit the batch operation
        batch.commit()

        return jsonify({"message": "Friends deleted successfully", "deletedFriendIds": friend_ids}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



############################################### FAVOuRITES ###################################



@main.route('/add_favourites', methods=['POST'])
def add_favourites():
    """
    Adds a friend relationship by updating subcollections under each user's profile document.
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_id = data.get('friendId')

        if not user_id or not friend_id:
            return jsonify({"error": "userId and friendId are required"}), 400

        # Firestore references for the users
        user_ref = db.collection('users-profiles').document(user_id).collection('my-favourites').document(friend_id)
        friend_ref = db.collection('users-profiles').document(friend_id).collection('my-favourites').document(user_id)

        # Check if friendship already exists (bidirectional)
        user_friendship = user_ref.get()
        friend_friendship = friend_ref.get()

        if user_friendship.exists or friend_friendship.exists:
            return jsonify({"message": "Friendship already exists or request already sent"}), 200

        # Add friendship documents in both users' subcollections
        user_ref.set({
            "friendId": friend_id,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        friend_ref.set({
            "friendId": user_id,
             # Shows this user received the request
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Favourite added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@main.route('/get_favourites/<user_id>', methods=['GET'])
def get_favourites(user_id):
    """
    Retrieves a list of friends for a specific user by querying `myfriends` subcollection
    and supplementing the data from `user_profiles`.
    """
    try:
        # Access the `myfriends` subcollection
        friends_ref = db.collection('users-profiles').document(user_id).collection('my-favourites').stream()

        fav = []

        for friend_doc in friends_ref:
            friend_data = friend_doc.to_dict()
            friend_id = friend_data.get("friendId")  # ID of the friend

            # Fetch additional details about the friend from `user_profiles`
            friend_profile_ref = db.collection('users-profiles').document(friend_id).get()
            if friend_profile_ref.exists:
                friend_profile_data = friend_profile_ref.to_dict()
                fav.append({
                    "userId": friend_id,
                    "nickname": friend_profile_data.get("nickname", "Unknown"),
                    "avatarUrl": friend_profile_data.get("avatarUrl", ""),
                    "gender":friend_profile_data.get("gender", ""),
                    "status": friend_data.get("status", "Unknown"),
                    "timestamp": friend_data.get("createdAt", ""),
                })
            else:
                # Friend profile does not exist, handle gracefully
                fav.append({
                    "id": friend_id,
                    "name": "Unknown",
                    "avatarUrl": "",
                    "status": friend_data.get("status", "Unknown"),
                    "timestamp": friend_data.get("timestamp", ""),
                })

        return jsonify({"favorites": fav}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@main.route('/delete_favourite', methods=['POST'])
def delete_favourite():
    """
    Deletes multiple friends by removing their relationships from the `my-friends` subcollection
    for both the user and the specified friends.
    """
    try:
        data = request.json
        user_id = data.get('userId')
        friend_ids = data.get('friendIds')  # List of friend IDs to delete

        if not user_id or not friend_ids or not isinstance(friend_ids, list):
            return jsonify({"error": "userId and a non-empty list of friendIds are required"}), 400

        batch = db.batch()  # Batch write for Firestore operations

        for friend_id in friend_ids:
            # Firestore references for both users' friendship documents
            user_ref = db.collection('users-profiles').document(user_id).collection('my-favourites').document(friend_id)
            friend_ref = db.collection('users-profiles').document(friend_id).collection('my-favourites').document(user_id)

            # Delete the documents in a batch
            batch.delete(user_ref)
            batch.delete(friend_ref)

        # Commit the batch operation
        batch.commit()

        return jsonify({"message": "Friends deleted successfully", "deletedFriendIds": friend_ids}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



