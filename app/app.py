from flask import Flask, render_template, request, jsonify
from inference import predict
from pdf_generator import generate_pdf
from flask import send_file
from ocr import extract_text_from_image, allowed_file
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("message")

    result = predict(text)

    return jsonify(result)


@app.route('/ocr_analyze', methods=['POST'])
def ocr_analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded.'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Use PNG, JPG, JPEG, WEBP, or BMP.'}), 400

    file_bytes = file.read()
    ocr_result = extract_text_from_image(file_bytes)

    if not ocr_result['success']:
        return jsonify({'error': ocr_result['error']}), 422

    extracted_text = ocr_result['text']

    # Pipe directly into existing inference — zero changes to inference.py
    prediction = predict(extracted_text)
    prediction['extracted_text'] = extracted_text
    prediction['input_method'] = 'ocr'

    return jsonify(prediction)

@app.route("/download_report", methods=["POST"])
def download_report():

    data = request.get_json()

    filepath = os.path.abspath("SentinelAI_Report.pdf")

    generate_pdf(data, filepath)

    return send_file(filepath, as_attachment=True, mimetype="application/pdf", download_name="SentinelAI_Report.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)