from flask import jsonify, request

def register_routes(app):
    @app.route("/", methods=["GET"])
    def home():
        return jsonify({"message": "Flask is running!"})

    @app.route("/hello/<name>", methods=["GET"])
    def hello(name):
        return jsonify({"message": f"Hello, {name}!"})
