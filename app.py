from app import create_app, socketio

app = create_app()

# Import WebSocket handlers
import app.websockets

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)