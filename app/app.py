from flask import Flask, render_template, request, jsonify
from inference import predict
from pdf_generator import generate_pdf
from flask import send_file
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

    # return jsonify({
    #     "label": result["label"],
    #     "scam_probability": result["scam_probability"],
    #     "safe_probability": result["safe_probability"]
    # })

@app.route("/download_report", methods=["POST"])
def download_report():

    data = request.get_json()

    filepath = os.path.abspath("SentinelAI_Report.pdf")

    generate_pdf(data, filepath)

    return send_file(filepath, as_attachment=True, mimetype="application/pdf", download_name="SentinelAI_Report.pdf")

if __name__ == "__main__":
    app.run(debug=True)