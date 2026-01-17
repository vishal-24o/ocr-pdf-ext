from pathlib import Path
import os
import json
from flask import Flask, render_template_string, request, jsonify
from ocr_pdf_extract import ocr_pdf
from field_extractor import extract_insurance_fields

app = Flask(__name__)

# ================= HTML TEMPLATE =================
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OCR PDF Extractor</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  background: linear-gradient(135deg, #0f172a, #1e293b, #312e81);
  min-height: 100vh;
  padding: 40px 20px;
  color: #e5e7eb;
}

/* ---------- HEADER ---------- */

.header {
  text-align: center;
  margin-bottom: 45px;
}

.title {
  font-size: 2.7rem;
  font-weight: 700;
  opacity: 0;
  transform: translateY(20px);
  animation: fadeUp 0.9s ease forwards;
}

.subtitle {
  margin-top: 10px;
  opacity: 0;
  transform: translateY(10px);
  animation: fadeUp 0.9s ease forwards;
  animation-delay: 0.3s;
  color: #c7d2fe;
}

.header-line {
  width: 0;
  height: 3px;
  margin: 18px auto 0;
  border-radius: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  animation: expand 0.8s ease forwards;
  animation-delay: 0.6s;
}

/* ---------- CONTAINER ---------- */

.container {
  max-width: 1100px;
  margin: auto;
}

/* ---------- CARD / GRID ---------- */

.card {
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(14px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 25px 60px rgba(0,0,0,0.35);
  margin-bottom: 35px;
}

/* ---------- UPLOAD ---------- */

.upload-section {
  text-align: center;
}

h2 {
  color: #a5b4fc;
  margin-bottom: 25px;
}

.btn {
  display: inline-block;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  padding: 14px 36px;
  border-radius: 999px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 12px 30px rgba(99,102,241,0.45);
}

.btn:hover {
  transform: translateY(-3px) scale(1.04);
  box-shadow: 0 20px 45px rgba(139,92,246,0.55);
}

.file-wrapper {
  margin: 25px 0;
}

input[type=file] { display: none; }

.file-name {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #c7d2fe;
}

/* ---------- LOADING ---------- */

.loading {
  display: none;
  margin-top: 25px;
}

.loading.active { display: block; }

.spinner {
  width: 42px;
  height: 42px;
  border: 4px solid rgba(255,255,255,0.25);
  border-top: 4px solid #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: auto;
}

/* ---------- STATS ---------- */

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 25px;
}

.stat {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  padding: 18px;
  border-radius: 14px;
  font-weight: 600;
}

/* ---------- FIELDS ---------- */

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 15px;
}

.field {
  background: rgba(255,255,255,0.12);
  border-radius: 12px;
  padding: 14px;
}

.field span {
  font-size: 0.8rem;
  color: #c7d2fe;
  text-transform: uppercase;
}

.field p {
  margin-top: 6px;
}

/* ---------- JSON ---------- */

.json-view {
  display: none;
  background: #020617;
  color: #e5e7eb;
  padding: 20px;
  border-radius: 12px;
  margin-top: 25px;
  max-height: 450px;
  overflow: auto;
  font-family: monospace;
}

.json-view.active { display: block; }

/* ---------- ANIMATIONS ---------- */

@keyframes fadeUp {
  to { opacity: 1; transform: translateY(0); }
}

@keyframes expand {
  to { width: 120px; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
</head>

<body>
<div class="container">

<div class="header">
  <h1 class="title">📄 OCR PDF Extractor</h1>
  <p class="subtitle">Upload an insurance PDF and extract structured data</p>
  <div class="header-line"></div>
</div>

<div class="card upload-section">
<form method="post" enctype="multipart/form-data" id="form">
  <h2>Upload Policy PDF</h2>

  <div class="file-wrapper">
    <label class="btn">
      Choose PDF
      <input type="file" name="file" id="file" accept="application/pdf" required>
    </label>
    <div class="file-name" id="fileName"></div>
  </div>

  <button class="btn">Extract Data</button>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p>Processing PDF…</p>
  </div>
</form>
</div>

{% if extracted_data %}
<div class="card">

  <div class="stats">
    <div class="stat">Fields: {{ field_count }}</div>
    <div class="stat">Filled: {{ filled_count }}</div>
    <div class="stat">Completion: {{ completion_rate }}%</div>
  </div>

  <button class="btn" onclick="toggleJson()">Toggle JSON</button>

  <div class="grid">
    {% for k,v in extracted_data.items() %}
    <div class="field">
      <span>{{ k }}</span>
      <p>{{ v if v else "Not found" }}</p>
    </div>
    {% endfor %}
  </div>

  <div class="json-view" id="jsonView">
    <pre>{{ json_data }}</pre>
  </div>

</div>
{% endif %}

</div>

<script>
document.getElementById("file").onchange = e =>
  document.getElementById("fileName").textContent =
  e.target.files[0]?.name || "";

document.getElementById("form").onsubmit = () =>
  document.getElementById("loading").classList.add("active");

function toggleJson() {
  const json = document.getElementById("jsonView");
  json.classList.toggle("active");
  if (json.classList.contains("active")) {
    json.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}
</script>

</body>
</html>
"""

# ================= ROUTES =================

@app.route("/", methods=["GET", "POST"])
@app.route("/api", methods=["GET", "POST"])
def index():
    extracted_data = None
    json_data = ""
    field_count = filled_count = completion_rate = 0

    if request.method == "POST":
        file = request.files.get("file")
        if file:
            uploads = Path("/tmp/uploads") if os.environ.get("VERCEL_ENV") else Path("uploads")
            uploads.mkdir(parents=True, exist_ok=True)

            path = uploads / file.filename
            file.save(path)

            text = ocr_pdf(path)
            extracted_data = extract_insurance_fields(text)

            field_count = len(extracted_data)
            filled_count = sum(1 for v in extracted_data.values() if v)
            completion_rate = round((filled_count / field_count) * 100, 1) if field_count else 0

            json_data = json.dumps(extracted_data, indent=2, ensure_ascii=False)
            path.unlink(missing_ok=True)

    return render_template_string(
        INDEX_HTML,
        extracted_data=extracted_data,
        json_data=json_data,
        field_count=field_count,
        filled_count=filled_count,
        completion_rate=completion_rate,
    )

@app.route("/api/extract", methods=["POST"])
def api_extract():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    uploads = Path("/tmp/uploads")
    uploads.mkdir(parents=True, exist_ok=True)
    path = uploads / file.filename
    file.save(path)

    text = ocr_pdf(path)
    data = extract_insurance_fields(text)
    path.unlink(missing_ok=True)

    return jsonify(data)

# ================= LOCAL RUN =================
if __name__ == "__main__":
    app.run(debug=True)
