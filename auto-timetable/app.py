from flask import Flask
from flask_cors import CORS
from routes import register_routes

app = Flask(__name__)
CORS(app)  # อนุญาตให้ Frontend เรียก API
register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)  # http://127.0.0.1:5000
