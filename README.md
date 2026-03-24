# CaseDesk AI

Self-hosted, privacy-focused document and case management with AI assistance.

## Features

- Document Management with OCR and intelligent renaming
- Case Management with AI-powered analysis
- Email Processing via IMAP with automatic AI analysis
- AI Assistant with full document knowledge (local Ollama or OpenAI)
- Response Generation in PDF/DOCX format
- Multi-User Support with invitation system
- Calendar and Task Management
- Data Export with all documents
- Dark/Light Theme
- Multilingual (DE, EN, FR, ES)

## Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose
- (Optional) NVIDIA GPU for faster local AI

### Installation

```bash
# Clone the repository
git clone <your-repo-url> casedesk-ai
cd casedesk-ai

# Copy environment config
cp .env.example .env

# Edit .env - IMPORTANT: Change SECRET_KEY!
nano .env

# Start all services
docker-compose up -d
```

The application will be available at **http://localhost** (Port 80).

### First Setup

1. Open http://localhost in your browser
2. The Setup Wizard guides you through:
   - Admin account creation
   - AI provider selection (Ollama local or OpenAI)
   - Language preference
3. Done! Start uploading documents.

### GPU Support (Ollama)

The default `docker-compose.yml` includes GPU support for Ollama.
If you don't have an NVIDIA GPU, comment out the `deploy` section in the Ollama service
and uncomment the CPU-only alternative.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_USER` | MongoDB username | `casedesk` |
| `MONGO_PASSWORD` | MongoDB password | `casedesk_secret` |
| `DB_NAME` | Database name | `casedesk` |
| `SECRET_KEY` | JWT signing key | **CHANGE THIS!** |
| `OPENAI_API_KEY` | OpenAI API key (optional) | empty |

### Services

| Service | Internal Port | Description |
|---------|--------------|-------------|
| Frontend (Nginx) | 80 | Web UI + API proxy |
| Backend (FastAPI) | 8001 | REST API |
| MongoDB | 27017 | Document database |
| OCR | 8002 | Tesseract OCR service |
| Ollama | 11434 | Local LLM server |

### Data Persistence

All data is stored in Docker volumes:
- `mongodb_data` - Database
- `uploads_data` - Uploaded documents
- `ollama_data` - Downloaded AI models

### Backup

```bash
# Backup MongoDB
docker exec casedesk-mongodb mongodump --out /dump \
  -u casedesk -p casedesk_secret --authenticationDatabase admin

# Copy backup
docker cp casedesk-mongodb:/dump ./backup

# Backup uploads
docker cp casedesk-backend:/app/uploads ./backup/uploads
```

### Update

```bash
git pull
docker-compose build
docker-compose up -d
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
yarn install
yarn start
```

## License

Private use. All rights reserved.
