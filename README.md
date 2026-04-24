# VoxScribe

VoxScribe is a FastAPI + vanilla JS voice note app that records or uploads audio, transcribes it, structures it into notes, stores it in SQLite, and exports notes as Word documents.

## Stack

- Backend: FastAPI, uvicorn, SQLAlchemy
- Frontend: single `frontend/index.html`
- Transcription: `faster-whisper`
- AI structuring: OpenRouter
- Database: SQLite
- Export: `python-docx`

## Project structure

```text
voicenote-uk/
|-- backend/
|   |-- main.py
|   |-- models.py
|   |-- auth.py
|   |-- transcribe.py
|   |-- analyse.py
|   |-- templates.py
|   |-- requirements.txt
|   `-- .env
|-- frontend/
|   `-- index.html
|-- render.yaml
`-- README.md
```

## Local run

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:8000`.

## Environment variables

Create `backend/.env` with:

```bash
OPENROUTER_API_KEY=your_openrouter_key
SECRET_KEY=your_secret_key
```

`DATABASE_URL` is optional. If it is not set, the app uses local SQLite.

## Main routes

- `GET /` - frontend
- `POST /api/auth/login` - built-in local login
- `GET /api/auth/user` - current user
- `GET /api/notes` - list notes
- `POST /api/notes` - save note
- `GET /api/notes/{id}` - note detail
- `DELETE /api/notes/{id}` - delete note
- `GET /api/notes/{id}/export` - download `.docx`
- `POST /transcribe` - upload audio and get structured output

## Free deployment on Render

This project is set up for a simple single-service Render deploy.

### Option 1: use the included `render.yaml`

1. Push `voicenote-uk` to GitHub.
2. In Render, create a new **Blueprint** and select the repo.
3. Add these environment variables in Render:
   - `OPENROUTER_API_KEY`
   - `SECRET_KEY`
4. Deploy.

### Option 2: create the service manually

Use these settings:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Important note

Render free tier uses ephemeral disk storage. Since this app currently uses SQLite, saved notes should be treated as demo data unless you later move to a hosted database.
