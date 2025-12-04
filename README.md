# DegreePath Tutor

An AI-powered academic advisor for Macquarie University students. Provides unit eligibility checking, prerequisite validation, personalized study reports, and interactive AI tutoring.

## Features

- **Unit Lookup**: Search for unit details with live web scraping from official Macquarie unit guides
- **Eligibility Checker**: Validate prerequisites before enrolling
- **AI Study Reports**: Generate personalized study plans, quizzes, and resources
- **Interactive Chat**: Conversational AI tutor with context memory
- **Student Management**: Track progress and completed units

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   Part 2 API    │────▶│   Part 1 API    │
│   (React/Vite)  │     │   (Port 8001)   │     │   (Port 8000)   │
│    Port 3000    │     │   AI + Chat     │     │   Database/RAG  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   LM Studio     │
                        │   (Optional)    │
                        │   Port 1234     │
                        └─────────────────┘
```

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend, optional)
- LM Studio (optional, for AI features)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Constantinos-uni/degreepath_tutor.git
cd degreepath_tutor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings (optional)
```

### 3. Start Services

#### Option A: Start Both APIs

```bash
# Terminal 1 - Part 1 API (Database, RAG, Web Search)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - Part 2 API (AI Tutor, Chat, Reports)
python -m uvicorn part2.main:app --host 127.0.0.1 --port 8001
```

#### Option B: Windows Quick Start (if using batch files)

```batch
START_DEMO.bat
```

### 4. Access the Application

- **Part 1 API Docs**: http://localhost:8000/docs
- **Part 2 API Docs**: http://localhost:8001/docs
- **Frontend** (if running): http://localhost:3000

## API Endpoints

### Part 1 API (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/unit/{code}` | Get unit details (live web + cache) |
| GET | `/unit/{code}/live` | Force live web fetch |
| POST | `/eligibility` | Check unit eligibility |
| POST | `/rag/query` | Query RAG knowledge base |
| POST | `/search/smart` | Smart search with prerequisite chains |
| GET | `/units/computing` | List all computing units |

### Part 2 API (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with AI status |
| GET | `/students` | List all students |
| GET | `/students/{id}` | Get student profile |
| POST | `/students` | Create student |
| POST | `/tutor-report` | Generate study report |
| GET | `/tutor-report/{code}` | Quick report for unit |
| POST | `/chat` | Chat with AI tutor |
| POST | `/chat/stream` | Streaming chat (SSE) |
| GET | `/chat/{id}/history` | Get conversation history |
| DELETE | `/chat/{id}` | Clear conversation |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PART1_HOST` | 127.0.0.1 | Part 1 API host |
| `PART1_PORT` | 8000 | Part 1 API port |
| `PART2_HOST` | 127.0.0.1 | Part 2 API host |
| `PART2_PORT` | 8001 | Part 2 API port |
| `USE_LM_STUDIO` | false | Enable AI features |
| `LM_STUDIO_URL` | http://localhost:1234/v1 | LM Studio endpoint |
| `LM_STUDIO_MODEL` | local-model | Model name |
| `CORS_ORIGINS` | * | Allowed CORS origins |

### LM Studio Setup (Optional)

For AI-powered content generation:

1. Download [LM Studio](https://lmstudio.ai/)
2. Load a compatible model (e.g., Gemma 2B, Llama 3)
3. Start the local server on port 1234
4. Update `.env`:
   ```
   USE_LM_STUDIO=true
   LM_STUDIO_URL=http://localhost:1234/v1
   LM_STUDIO_MODEL=your-model-name
   ```

Without LM Studio, the system uses rule-based generation (still functional).

## Project Structure

```
degreepath_tutor/
├── backend/              # Part 1: Database, RAG, Web Search
│   ├── main.py           # FastAPI application
│   ├── database.py       # SQLite operations
│   ├── logic.py          # Business logic
│   ├── models.py         # Pydantic models
│   ├── rag.py            # RAG system (ChromaDB)
│   ├── unit_search.py    # Web scraper for unit guides
│   └── data/             # Database and vector store
├── part2/                # Part 2: AI Tutor
│   ├── main.py           # FastAPI with AI integration
│   ├── conversation_manager.py  # Chat memory and context
│   └── data/             # Conversation persistence
├── frontend/             # React frontend (optional)
├── tests/                # Test suite
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### API Testing

Use the interactive Swagger docs at `/docs` or the included HTTP test file:
```
tests/api_tests.http
```

## Troubleshooting

### Services won't start

```bash
# Check if ports are in use
# Windows:
netstat -an | findstr "800"
# macOS/Linux:
lsof -i :8000

# Kill existing processes if needed
# Windows:
taskkill /F /IM python.exe
```

### AI not working

1. Verify LM Studio is running: `curl http://localhost:1234/v1/models`
2. Check `.env` has `USE_LM_STUDIO=true`
3. System falls back to rule-based generation automatically

### Unit not found

The system scrapes live data from Macquarie unit guides. If a unit isn't found:
- Verify the unit code is correct (e.g., COMP1010)
- Check if the unit is offered in the current year
- The system will use cached data if available

## Tech Stack

- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Pydantic
- **AI/RAG**: LangChain, ChromaDB, HuggingFace Embeddings
- **Web Scraping**: BeautifulSoup4, Requests
- **Frontend**: React, Vite, TypeScript, Tailwind CSS
- **Local LLM**: LM Studio (OpenAI-compatible API)

## License

This project is dual-licensed:

- **AGPL-3.0** - Free for open source, educational, and non-commercial use
- **Commercial License** - For commercial, proprietary, or SaaS use

See [LICENSE](LICENSE) for details. For commercial licensing inquiries, please open an issue or contact via GitHub.

## Author

Constantinos - Macquarie University

## Acknowledgments

- Macquarie University for unit guide data
- LM Studio for local LLM hosting
- The FastAPI and LangChain communities
