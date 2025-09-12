# 🚀 Healthy Meal Copilot API

The **Healthy Meal Copilot API** is a prototype backend designed to **generate AI-powered meal plans**.  
It balances **API-first development, type safety, AI integration, and testing best practices**.

This project serves as a **production-ready prototype** stack combining:

- **FastAPI** for high-performance APIs
- **Pydantic** for strict data modeling
- **Ruff** for lightning-fast linting
- **mypy** for static type checking
- **pytest** for robust testing
- **LLM integrations** with OpenAI, Gemini, and Claude
- **MongoDB** for structured data storage
- **Qdrant** for vector embeddings & retrieval

---

## ✨ Features

- 🍽️ **AI-driven meal plan generation**
- 🔑 **Authentication system** with multiple modes (`internal`, `partner`, `both`)
- ⚡ **RESTful API endpoints** with FastAPI
- 📊 **MongoDB persistence** for structured data
- 🔍 **Qdrant integration** for semantic retrieval
- 🤖 **Multiple LLMs supported**: OpenAI, Gemini, Claude
- 🧪 **Test-oriented stack** with `pytest`
- 🔒 Static analysis & formatting via `ruff` + `mypy`

---

## 🛠 Tech Stack

- **Language:** Python `3.12`
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM / Models:** [Pydantic](https://docs.pydantic.dev/)
- **Testing:** [pytest](https://docs.pytest.org/)
- **Static typing:** [mypy](http://mypy-lang.org/)
- **Linting & Formatting:** [Ruff](https://docs.astral.sh/ruff/)
- **Database:** [MongoDB](https://www.mongodb.com/)
- **Vector DB:** [Qdrant](https://qdrant.tech/)
- **LLM Providers:** OpenAI, Gemini, Claude

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/healthymeal-copilot-api.git
cd healthymeal-copilot-api
```

### 2. Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your keys, database URLs, and config.  
(See [example configuration above](#installation--setup)).

---

## ▶️ Running the Application

```bash
python -m app.main
```
or

```bash
uvicorn app.main:app --reload
```

By default, the app runs at:  
👉 [http://localhost:8000](http://localhost:8000)

---

## 📖 API Documentation

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Development Workflow

This project uses a **test-first, type-safe workflow**.

### Run Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

### Run Static Analysis (mypy)

```bash
mypy app test
```

### Run Linter/Formatter (ruff)

```bash
ruff check app test
ruff format app test
```

> ✅ Recommendation: Add `pre-commit` hooks to run `mypy` + `ruff` automatically.

---

## 📂 Project Structure

```
app/
 ├── api/            # API route handlers
 ├── core/           # Core settings & config
 ├── db/             # DB clients (Mongo, Qdrant)
 ├── models/         # Pydantic data models
 ├── prompts/        # LLM prompt templates
 ├── schemas/        # Request/response validation
 ├── services/       # Domain logic (meal planning, LLM, etc.)
 ├── utils/          # Helper functions
 └── main.py         # FastAPI entrypoint
docs/                # Additional documentation
tests/               # Pytest test suite
```

---

## 🔐 Authentication Overview

- Modes: `internal`, `partner`, `both`
- Authentication via **API Keys** + **JWT tokens**
- Super Admin API key for privileged routes

See [docs/authentication.md](docs/authentication.md) for full details.

---

## 🧑‍💻 Prototype Roadmap

1. ✅ Core FastAPI + MongoDB + Qdrant integration  
2. ✅ Multi-LLM integration (OpenAI, Gemini, Claude)  
3. ✅ Testing + linting + typing pipeline  
4. 🔄 CI/CD integration with GitHub Actions (test, lint, type-check)  
5. 🔜 Deployment to containerized environments  

---

## 🤝 Contributing

1. Fork repo & create feature branch  
2. Ensure `pytest`, `mypy`, and `ruff` pass cleanly  
3. Submit PR 🚀  

---

## 📜 License

MIT License – free to use, modify, and distribute.