from flask import Flask, render_template, request, jsonify, send_file
from inference import predict
from pdf_generator import generate_pdf
from ocr import extract_text_from_image, allowed_file
import os
import tempfile

app = Flask(__name__)

# Limit incoming request body to 15 MB (guards /ocr_analyze against huge uploads)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)

    if not data or not data.get("message"):
        return jsonify({"error": "No message provided."}), 400

    text = data["message"].strip()
    if not text:
        return jsonify({"error": "Message cannot be empty."}), 400

    result = predict(text)
    return jsonify(result)


@app.route("/ocr_analyze", methods=["POST"])
def ocr_analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PNG, JPG, JPEG, WEBP, or BMP."}), 400

    file_bytes = file.read()
    ocr_result = extract_text_from_image(file_bytes)

    if not ocr_result["success"]:
        return jsonify({"error": ocr_result["error"]}), 422

    extracted_text = ocr_result["text"]

    # Pipe directly into existing inference — zero changes to inference.py
    prediction = predict(extracted_text)
    prediction["extracted_text"] = extracted_text
    prediction["input_method"] = "ocr"

    return jsonify(prediction)


@app.route("/download_report", methods=["POST"])
def download_report():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided."}), 400

    # Use a temp file so concurrent requests don't overwrite each other
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        filepath = tmp.name

    try:
        generate_pdf(data, filepath)
        return send_file(
            filepath,
            as_attachment=True,
            mimetype="application/pdf",
            download_name="SentinelAI_Report.pdf",
        )
    finally:
        # Clean up the temp file after Flask sends it
        try:
            os.unlink(filepath)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)