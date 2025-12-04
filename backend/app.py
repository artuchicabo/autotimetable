from flask import Flask
from flask_cors import CORS
from routes import api_blueprint
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Configure CORS for production - allow all origins in development, specific in production
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # Allow all origins - change this in production to specific domains
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.register_blueprint(api_blueprint, url_prefix="/api")

@app.route("/")
def home():
    return {"message": "AI Timetable API Running 🚀", "status": "OK"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False") == "True"
    # Bind to 0.0.0.0 to allow external access
    app.run(host="0.0.0.0", debug=debug, port=port)
