from flask import Flask
from flask_socketio import SocketIO

# Create a SocketIO instance
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # Register Blueprints for routes
    from .routes import main
    app.register_blueprint(main)

    # Initialize SocketIO with the app
    socketio.init_app(app)

    return app

