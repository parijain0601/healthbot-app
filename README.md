# 🏥 HealthBot - AI Medical Report Analyzer

An intelligent health report analysis platform that helps users understand their medical test results safely and clearly.

## ✨ Features

- **📤 Report Upload** — Upload PDF, images, or text files
- **📊 Data Extraction** — Automatic extraction of medical test values using OCR
- **🔍 Abnormality Detection** — Identify high, low, and normal values
- **💯 Health Score** — Get an overall health assessment (0-100)
- **⚠️ Risk Assessment** — Low, Moderate, or High risk levels
- **💡 Health Insights** — Personalized lifestyle recommendations
- **🏥 Hospital Recommendations** — AI-powered specialist and hospital matching
- **📱 Responsive Design** — Works on desktop, tablet, and mobile

## 🛠️ Tech Stack

- **Backend:** Python, Flask, PostgreSQL
- **Frontend:** React, CSS3
- **Processing:** PyPDF2, Pillow, pytesseract
- **Deployment:** Docker, Docker Compose

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15 (if running locally without Docker)

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
git clone https://github.com/parijain0601/healthbot-app.git
cd healthbot-app

cp .env.example .env

docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000/api
```

### Manual Setup

**Backend:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:password@localhost/healthbot
python app_advanced.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 📚 API Endpoints

- `POST /api/users` — Create new user
- `POST /api/reports` — Upload health report
- `POST /api/reports/<id>/analyze` — Analyze report
- `GET /api/reports/<id>` — Get report details
- `GET /api/users/<id>/reports` — Get user's reports

## ⚠️ Disclaimer

**This is not medical advice.** Always consult a qualified healthcare professional.

## 📝 License

MIT License - see LICENSE file for details