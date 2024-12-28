from flask import Blueprint, request, jsonify
#from .firebase_config import db

main = Blueprint('main', __name__)

@main.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    user_id = data.get('userId')
    nickname = data.get('nickname')
    gender = data.get('gender')

    if not user_id or not nickname or not gender:
        return jsonify({'message': 'Missing fields'}), 400

    # user_ref = db.collection('users').document(user_id)
    # doc = user_ref.get()
    return jsonify({'message':user_id + nickname + gender})

    if doc.exists:
        return jsonify({'message': 'User already registered'}), 400

    user_ref.set({
        'userId': user_id,
        'nickname': nickname,
        'gender': gender,
    })

    return jsonify({'message': 'User registered successfully'}), 201

# @main.route('/user/<user_id>', methods=['GET'])
# def get_user_profile(user_id):
#     #user_ref = db.collection('users').document(user_id)
#     doc = user_ref.get()

#     if doc.exists:
#         return jsonify(doc.to_dict()), 200
#     return jsonify({'message': 'User not found'}), 404
