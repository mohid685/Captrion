# Captrion

Captrion is a financial advisory platform designed to provide users with data-driven insights for understanding markets, evaluating investments, and managing their portfolios.

## Technical Implementation

* **RAG** — Retrieval-Augmented Generation
* **MCP** — Model Context Protocol
* **FinBERT** — Financial sentiment analysis
* **Machine Learning** — Market signals and risk assessment
* **LLM-based reasoning** — Financial analysis and advisory responses

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Docker

**Frontend:** React, TypeScript, Vite, Tailwind CSS, Zustand

## Setup

### Prerequisites

* Python 3.9+
* Node.js 18+
* Docker Desktop
* Git

### Backend

Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd financial-advisor
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start Docker Desktop, then start the PostgreSQL container:

```bash
docker compose up -d
docker ps
```

Make sure `financial-advisor-db` is running and shows a **healthy** status before continuing.

Start the API server:

```bash
uvicorn app.main:app --reload
```

Wait for:

```text
Application startup complete.
```

Keep the API server running and use a separate terminal for the remaining commands.

### Frontend

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```


## API Documentation

Once the backend is running:

**Swagger UI:** `http://127.0.0.1:8000/docs`

**ReDoc:** `http://127.0.0.1:8000/redoc`
