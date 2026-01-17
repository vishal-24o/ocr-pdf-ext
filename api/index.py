from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "UI is running. OCR is disabled on Vercel."
    })

@app.route("/api/extract", methods=["POST"])
def extract():
    return jsonify({
        "error": "OCR not supported on Vercel serverless",
        "solution": "Run OCR locally or on VM backend"
    }), 501

def handler(request, context):
    return app(request.environ, lambda status, headers: None)
