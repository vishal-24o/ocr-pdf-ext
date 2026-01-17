from pathlib import Path
import os, json
from flask import Flask, request, jsonify, render_template_string

# ⚠️ Disable OCR on Vercel to avoid crashes
VERCEL = os.environ.get("VERCEL_ENV")

app = Flask(__name__)

INDEX_HTML = """ 
<!-- YOUR FULL HTML HERE (UNCHANGED UI) -->
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if VERCEL:
        return render_template_string(
            INDEX_HTML,
            extracted_data=None,
            json_data="",
            field_count=0,
            filled_count=0,
            completion_rate=0,
        )

    return jsonify({"message": "Run OCR locally, not on Vercel"})


@app.route("/extract", methods=["POST"])
def extract():
    return jsonify({
        "error": "OCR disabled on Vercel",
        "solution": "Run OCR locally or on VM backend"
    }), 501


# 👇 REQUIRED by Vercel
def handler(request, context):
    return app(request.environ, lambda status, headers: None)
