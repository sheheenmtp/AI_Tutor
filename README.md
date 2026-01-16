🚀 Code Mastery Platform
An AI-driven interactive learning environment designed to help developers master Python through real-time execution and pedagogical mentorship. Unlike traditional judges, this platform uses Local LLMs to provide conceptual guidance tailored to a student's current skill level.

✨ Features
🧠 Adaptive AI Tutor: Integrated with Ollama (Qwen2.5-Coder) to provide hints and feedback. The AI identifies conceptual gaps without revealing direct solutions, adjusting its tone for Beginner, Intermediate, and Advanced users.

💻 Professional Editor: A fully-featured coding workspace powered by the Monaco Editor (the engine behind VS Code), featuring Python syntax highlighting and bracket matching.

⚙️ Sandboxed Execution: Secure, real-time code execution via the Judge0 API.

📈 Progression System: Automated level tracking that promotes users as they solve increasingly complex problems.

🌓 Modern UI/UX: Responsive design with a seamless Dark/Light mode toggle and real-time health monitoring of backend services.

🏗️ Technical Architecture
The platform is built as a decoupled full-stack application:

Frontend: React (Vite) + Lucide Icons + Monaco Editor.

Backend: FastAPI (Python) + SQLAlchemy ORM.

Database: PostgreSQL for user progress, problem sets, and submission history.

Execution Engine: Judge0 (Self-hosted/Docker).

AI Engine: Ollama running qwen2.5-coder:14b.

🛠️ Installation & Setup
Prerequisites
Python 3.10+

Node.js & npm

PostgreSQL

Docker (for Judge0)

Ollama

1. Clone the Repository
Bash

git clone https://github.com/YOUR_USERNAME/code-mastery.git
cd code-mastery
2. Backend Setup
Bash

cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# Update DATABASE_URL in models.py if necessary
3. Frontend Setup
Bash

cd ../frontend
npm install
4. Running the Platform
You can use the provided orchestration script to launch all services:

Bash

chmod +x run.sh
./run.sh
🔌 API Configuration
Ensure your service endpoints are correctly configured in api.js (Frontend) and app.py (Backend):

FastAPI: localhost:8000

Judge0: 192.168.x.x:2358

Ollama: 192.168.x.x:11434
