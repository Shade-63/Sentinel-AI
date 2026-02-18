# SentinelAI — Digital Threat Risk Analyzer

> **AI-powered scam detection system** that analyzes suspicious messages and generates professional Structured Intelligence Brief (SIB) PDF reports.

---

## 🛡️ What It Does

SentinelAI uses a fine-tuned **DistilBERT transformer model** combined with rule-based heuristics to detect digital arrest scams, phishing attempts, and financial fraud patterns in text messages. Results are displayed in a dynamic threat-adaptive UI and can be exported as a formatted PDF security report.

---

## 🚀 Features

- **AI-Powered Detection** — Fine-tuned DistilBERT on a curated digital scam corpus
- **Hybrid Inference** — Rule-based pre-screening + transformer model for high accuracy
- **Threat-Adaptive UI** — Color theme shifts (cyan → red/green) based on risk level
- **PDF Report Generation** — Professional "Structured Intelligence Brief" with risk bands, signal tables, and recommended actions
- **Risk Scoring** — Probabilistic scam/safe score with HIGH / MEDIUM / LOW classification

---

## 📁 Project Structure

```
Sentinel/
├── app/
│   ├── app.py              # Flask application & API routes
│   ├── inference.py        # Hybrid prediction engine
│   ├── pdf_generator.py    # PDF report generator (ReportLab)
│   └── templates/
│       └── index.html      # Main UI (Tailwind CSS, dark theme)
├── models/
│   ├── sentinel_model/     # Fine-tuned DistilBERT (weights via Git LFS or HF Hub)
│   ├── train_model.py      # Training script v1
│   └── train_model_v2.py   # Training script v2
├── data/
│   └── sentinel_dataset_audited.csv   # Labeled training dataset
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Sentinel.git
cd Sentinel
```

### 2. Create and activate a virtual environment
```bash
python -m venv env

# Windows
env\Scripts\activate

# macOS / Linux
source env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download the model weights

> ⚠️ The model weights (`model.safetensors`, ~255 MB) are **not included** in this repository due to GitHub's file size limit.

**Option A — HuggingFace Hub** *(recommended)*
```bash
# Coming soon — model will be uploaded to HF Hub
```

**Option B — Manual download**  
Download `model.safetensors` from [Releases](../../releases) and place it at:
```
models/sentinel_model/model.safetensors
```

### 5. Run the application
```bash
cd app
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🧠 Model Details

| Property | Value |
|---|---|
| Base Model | `distilbert-base-uncased` |
| Task | Binary Sequence Classification (SCAM / SAFE) |
| Training Data | Custom curated digital arrest scam dataset |
| Inference | Hybrid: rule-based pre-filter + transformer |

---

## 📄 PDF Report

After running an analysis, click **Download PDF Report** to get a formatted **Structured Intelligence Brief** containing:
- Risk score & classification band (RED / AMBER / GREEN)
- Detected risk indicators table
- AI model interpretation
- Recommended immediate actions
- Report ID and timestamp

---

## ⚠️ Disclaimer

SentinelAI provides AI-based probabilistic risk estimation and does **not** constitute legal advice. Always verify through official law enforcement or financial authorities.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
