# BriefAI — Company Brochure Generator

Turn any company website into a polished, markdown brochure in seconds. BriefAI scrapes the homepage, discovers relevant pages (About, Careers, Products), and uses an LLM to write a structured brochure for prospective customers, investors, and recruits.

---

## Project Structure

```
brochure-app/
├── backend/
│   ├── main.py           # FastAPI backend
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variable template
└── frontend/
    └── index.html        # Single-file frontend (no build step)
```

---

## How It Works

1. **Scrape** — The backend fetches the homepage using `requests` + `BeautifulSoup` and extracts all links.
2. **Select** — An LLM call picks the most relevant links (About, Careers, Products) from the full list.
3. **Read** — The backend fetches and cleans the content of each relevant page.
4. **Write** — A second LLM call synthesises all the content into a structured markdown brochure.

---

## Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- A way to serve the frontend (e.g. VS Code Live Server)

---

## Setup

### 1. Clone / download the project

```bash
git clone https://github.com/your-username/brochure-app.git
cd brochure-app
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Copy the environment template and fill in your API key:

```bash
cp .env.example .env
```

Open `.env` and set your key:

```
API_KEY=your_gemini_api_key_here
MODEL=gemini-2.0-flash-lite
```

### 3. Start the backend

```bash
python main.py
```

The server starts at `http://127.0.0.1:8080`. Verify it's running:

```
http://127.0.0.1:8080/health
```

You should see:

```json
{ "status": "ok", "model": "gemini-2.0-flash-lite" }
```

### 4. Open the frontend

Open `frontend/index.html` with **VS Code Live Server** (right-click → _Open with Live Server_).

The frontend expects to be served from `http://127.0.0.1:5500`. If you use a different port, update the CORS origins in `backend/main.py`:

```python
allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"]
```

---

## Usage

1. Enter the company name (e.g. `Stripe`)
2. Enter the website URL (e.g. `https://stripe.com`)
3. Click **Generate brochure**
4. Copy the markdown output or print the page

---

## API Reference

### `GET /health`

Returns the server status and active model.

**Response**

```json
{ "status": "ok", "model": "gemini-2.0-flash-lite" }
```

---

### `POST /generate`

Scrapes the website and generates a brochure.

**Request body**

```json
{
  "company_name": "Stripe",
  "url": "https://stripe.com"
}
```

**Response**

```json
{
  "company_name": "Stripe",
  "brochure": "# Stripe\n\n## Overview\n..."
}
```

**Error responses**

| Status | Reason                                              |
| ------ | --------------------------------------------------- |
| `422`  | Missing `company_name` or `url`                     |
| `500`  | `API_KEY` not set, or model returned empty response |
| `502`  | Could not fetch the target website                  |

---

## Configuration

| Variable  | Default                 | Description                    |
| --------- | ----------------------- | ------------------------------ |
| `API_KEY` | —                       | Your Gemini API key (required) |
| `MODEL`   | `gemini-2.0-flash-lite` | Gemini model to use            |

To switch models, update `MODEL` in your `.env`:

```
MODEL=gemini-2.0-flash
```

---

## Troubleshooting

**"Failed to fetch" in the browser**
The frontend can't reach the backend. Check that `python main.py` is running and that the port in `index.html` matches (`8080`).

**CORS error in the browser console**
Your frontend is being served from a different origin than what's listed in `allow_origins` in `main.py`. Add your origin:

```python
allow_origins=["http://127.0.0.1:5500", "http://your-origin-here"]
```

**`API_KEY not set` error**
Make sure `.env` exists in the `backend/` folder and contains a valid `API_KEY`.

**Brochure content is thin or missing sections**
Some websites block scrapers. The backend will note failed fetches in the content with `[Could not fetch ...]` and the LLM will work with whatever it got.

---

## Deploying

For production, replace the CORS origin with your real frontend domain:

```python
allow_origins=["https://your-domain.com"]
```

Run the backend with a process manager:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2
```

The frontend is a plain HTML file — deploy it to any static host (Vercel, Netlify, GitHub Pages). Update `API_BASE` in `index.html` to point to your deployed backend URL:

```js
const API_BASE = "https://your-api.your-domain.com";
```

---
