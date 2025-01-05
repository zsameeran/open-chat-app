from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Store user-room mapping in memory (for simplicity)
user_rooms = {}

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit("connection_ack", {"message": "Connected to WebSocket server"})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")
    # Optionally handle cleanup of user_rooms here

@socketio.on('join_room')
def handle_join_room(data):
    user_id = data.get('user_id')
    room = data.get('room')

    if user_id and room:
        user_rooms[user_id] = room
        join_room(room)
        emit("join_ack", {"message": f"Joined room {room}"}, room=room)
        print(f"User {user_id} joined room {room}")
    else:
        emit("error", {"message": "Invalid data"})

@socketio.on('leave_room')
def handle_leave_room(data):
    user_id = data.get('user_id')
    room = user_rooms.pop(user_id, None)

    if room:
        leave_room(room)
        emit("leave_ack", {"message": f"Left room {room}"}, room=room)
        print(f"User {user_id} left room {room}")
    else:
        emit("error", {"message": "User is not in any room"})

@socketio.on('send_message')
def handle_send_message(data):
    user_id = data.get('user_id')
    message = data.get('message')
    room = user_rooms.get(user_id)

    if room and message:
        emit("receive_message", {"user_id": user_id, "message": message}, room=room)
        print(f"User {user_id} sent message to room {room}: {message}")
    else:
        emit("error", {"message": "Invalid data or user not in any room"})

if __name__ == "__main__":
    # For testing, use a local host and port
    socketio.run(app, host="0.0.0.0", port=5000)
