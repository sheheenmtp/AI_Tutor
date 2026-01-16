#  Ai_Tutor Platform

An AI-driven interactive learning environment that transforms the coding practice experience. It combines a professional-grade editor with a pedagogical AI tutor that provides level-specific mentorship without giving away direct answers.

![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Ollama](https://img.shields.io/badge/AI-Ollama%20(Qwen2.5)-purple?style=flat-square)
![Judge0](https://img.shields.io/badge/Execution-Judge0-orange?style=flat-square)

## ✨ Key Features

* **🧠 Intelligent AI Tutor:** Powered by **Ollama (Qwen2.5-Coder)**. The tutor adjusts its feedback complexity based on your profile (Beginner, Intermediate, or Advanced) to provide conceptual hints rather than raw code.
* **💻 Professional Workspace:** Integrated **Monaco Editor** featuring Python 3 syntax highlighting, bracket pair colorization, and smooth caret animations.
* **⚙️ Sandboxed Execution:** Real-time code validation against sample and hidden test cases via a dedicated **Judge0** instance.
* **📈 Smart Progression:** Automatic level advancement logic—Beginner to Intermediate at 5 solved problems; Intermediate to Advanced at 10.
* **🌓 Adaptive Theming:** Seamless transition between high-contrast Dark and Light modes.

## 🏗️ Technical Architecture

The platform utilizes a modern, decoupled full-stack architecture:

-   **Frontend:** Vite-powered React application using `Lucide-React` for iconography and `Monaco` for editing.
-   **Backend:** FastAPI (Python) managing business logic, user state, and external service orchestration.
-   **Database:** PostgreSQL with SQLAlchemy ORM for persistence of users, problems, and submissions.
-   **Infrastructure:** Connects to local AI (Ollama) and sandboxed judges (Judge0) via REST APIs.

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have the following services active on your local network (as configured in `run.sh`):
* **Judge0:** `http://localhost:2358`
* **Ollama:** `http://localhost:11434` (Model: `qwen2.5-coder:14b`)
* **PostgreSQL:** A database named `codemastery`.

### 2. Backend Installation
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Installation
```bash

cd frontend
npm install
```

### 4. Running the Platform
The root directory includes a utility script to check service health and launch both servers:
```bash
chmod +x run.sh
./run.sh
```

## 🔌 API Summary

| Service | Endpoint | Protocol | Primary Role |
| :--- | :--- | :--- | :--- |
| **Backend API** | `http://localhost:8000` | REST | Business logic, Database ORM, and Service Orchestration |
| **Code Execution** | `http://localhost:2358` | REST | Sandboxed Python execution via **Judge0** |
| **AI Tutor** | `http://localhost:11434` | REST | LLM Feedback generation via **Ollama** (`qwen2.5-coder`) |
| **Database** | `localhost:5432` | TCP/IP | Persistent storage for users, problems, and submissions |

### Key Backend Endpoints
- `GET /problems` - Retrieves the list of coding challenges.
- `POST /run` - Performs a quick execution of code against sample input.
- `POST /validate` - Checks code against all hidden test cases.
- `POST /submit` - Finalizes a problem, calculates score, and updates user level.
- `POST /feedback` - Generates level-specific AI tutoring hints.


## 📁 Project Structure

The repository is organized into a decoupled full-stack architecture, separating the Python backend logic from the React frontend interface.

```text
.
├── backend/                # FastAPI Application
│   ├── app.py              # API routes & AI tutor logic
│   ├── models.py           # SQLAlchemy database schemas
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Python virtual environment (ignored by git)
│
├── frontend/               # React (Vite) Application
│   ├── src/
│   │   ├── components/     # UI Components (Editor, Sidebar, etc.)
│   │   ├── services/       # API integration (api.js)
│   │   ├── styles/         # Global & Component-specific CSS
│   │   ├── App.jsx         # Main application controller
│   │   └── main.jsx        # React entry point
│   ├── public/             # Static assets (logos, icons)
│   ├── index.html          # HTML template
│   └── package.json        # Node.js dependencies & scripts
│
├── run.sh                  # Root orchestration & startup script
└── .gitignore              # Files excluded from version control
```

