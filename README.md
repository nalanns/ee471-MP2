# EE471 Mini Project #2 – Voice-activated Library App

A Flask REST API for a small library of books and DVDs, controlled entirely by voice.
You speak a command, the app recognizes it with **Azure Speech-to-Text**, calls the matching
endpoint, and the librarian answers out loud with **Azure Text-to-Speech**.

```
🎤 You ──► Azure Speech-to-Text ──► voice_app.py ──► Flask API (app.py) ──► voice_app.py ──► Azure Text-to-Speech ──► 🔊 Librarian
```

## Features

- Voice control for all 8 Library API endpoints
- Spoken confirmation after every completed job
- Spoken error messages for `400`, `404` and `409` responses
- Every backend call is printed in the terminal (method, path, status code)
- API keys kept in a local `.env` file that is never pushed to GitHub

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Flask REST API (Week 4 Library App) |
| `custom_classes.py` | `MediaItem`, `Book`, `DVD`, `LibraryCollection` and error classes |
| `voice_app.py` | Voice client: listens, parses the command, calls the API, speaks the result |
| `templates/`, `static/` | Web UI from Week 4 |
| `main.py` | Week 4 demo script for the library classes |
| `.env.example` | Template for the Azure Speech credentials |
| `PROMPTS.md` | Vibe coding transcripts |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/nalanns/ee471-MP2.git
cd ee471-MP2
pip install -r requirements.txt
```

### 2. Add your Azure Speech credentials

Create a **Speech service** resource in the [Azure Portal](https://portal.azure.com), then copy the key and region from **Keys and Endpoint**.

```bash
cp .env.example .env
```

```env
SPEECH_KEY=<your-key>
SPEECH_REGION=westeurope
```

> `.env` is listed in `.gitignore`, so your key is never pushed to GitHub.

### 3. Run

Terminal 1, start the API:

```bash
python app.py
```

Terminal 2, start the voice client:

```bash
python voice_app.py
```

Allow microphone access when macOS asks. When you see `Listening...`, speak a command in English.

## Voice Commands

| Say | Endpoint |
|---|---|
| "Create item, type book, title The Catcher in the Rye, author J.D. Salinger, pages 220" | `POST /api/items` |
| "Create item, type DVD, title Inception, author Christopher Nolan, duration 148" | `POST /api/items` |
| "List items" | `GET /api/items` |
| "List available books" / "List checked out DVDs" | `GET /api/items?available=…&type=…` |
| "Get item 3" | `GET /api/items/3` |
| "Replace item 3, title Dune Messiah, author Frank Herbert, pages 256" | `PUT /api/items/3` |
| "Update item 3, pages 230" | `PATCH /api/items/3` |
| "Delete item 3" | `DELETE /api/items/3` |
| "Check out item 3" | `POST /api/items/3/checkout` |
| "Return item 3" | `POST /api/items/3/return` |
| "Exit" | Closes the voice client |

Field keywords: `type`, `title`, `author`, `pages`, `duration`.

## Example Session

```
You: Create item, type book, title The Catcher in the Rye, author J.D. Salinger, pages 220.
[backend] POST /api/items -> 201
Librarian: Successfully created book 'The Catcher in the Rye' with ID 5.

You: Check out item 5.
[backend] POST /api/items/5/checkout -> 200
Librarian: Item 5, 'The Catcher in the Rye', has been checked out.

You: Check out item 5.
[backend] POST /api/items/5/checkout -> 409
Librarian: Sorry, item 5 is already checked out.

You: Get item 99.
[backend] GET /api/items/99 -> 404
Librarian: Sorry, item 99 not found.
```

## API Reference

All responses are JSON. Errors are returned as `{"error": "<message>"}`.

| Endpoint | Purpose | Success | Errors |
|---|---|---|---|
| `POST /api/items` | Create a Book or DVD | 201 | 400 |
| `GET /api/items` | List items (`?available=true`, `?type=book`) | 200 | 400 |
| `GET /api/items/<id>` | Get one item | 200 | 404 |
| `PUT /api/items/<id>` | Replace all editable fields | 200 | 400, 404 |
| `PATCH /api/items/<id>` | Change some editable fields | 200 | 400, 404 |
| `DELETE /api/items/<id>` | Remove an item | 204 | 404, 409 |
| `POST /api/items/<id>/checkout` | Check an item out | 200 | 404, 409 |
| `POST /api/items/<id>/return` | Return an item | 200 | 404, 409 |

## Tech Stack

Python · Flask · Azure Speech SDK (`azure-cognitiveservices-speech`) · requests · python-dotenv
