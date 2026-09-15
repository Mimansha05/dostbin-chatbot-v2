# DOSTBin Chatbot V2

Local RAG chatbot for DOSTBin FAQ data. WordPress hosts the widget; FastAPI keeps the Groq API key on the server.

The chatbot retrieves relevant FAQ entries first, then asks Groq to answer using only that context. If nothing relevant is found, it returns a safe fallback and does not call Groq.

## Requirements

- Python 3.10 or later
- A Groq API key from [console.groq.com](https://console.groq.com)
- For WordPress: WordPress 6.0+ and a publicly reachable chatbot API URL

## Installation

```powershell
cd "C:\Users\MIMANSHA MISHRA\Desktop\dostbin-chatbot-v2"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## Environment variables

Copy the example file and edit the values:

```powershell
Copy-Item .env.example .env
```

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | Yes | none | Server-side Groq API key. Never send this to the browser or WordPress. |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Groq chat model. `llama-3.3-70b-versatile` is no longer available on current Groq accounts. |
| `GROQ_BASE_URL` | No | `https://api.groq.com/openai/v1` | OpenAI-compatible Groq endpoint. |
| `GROQ_TIMEOUT_SECONDS` | No | `45` | Groq request timeout. |
| `ALLOWED_ORIGINS` | No | `http://localhost:8000,http://127.0.0.1:8000` | CORS allowlist for JavaScript embeds from other origins. |
| `RATE_LIMIT_REQUESTS` | No | `30` | Max chat requests per IP per window. |
| `RATE_LIMIT_WINDOW_SECONDS` | No | `60` | Rate-limit window. |
| `MAX_QUESTION_LENGTH` | No | `500` | Max question length. |

`.env` is gitignored. Do not commit API keys.

## Configure Groq

1. Create an API key in the [Groq console](https://console.groq.com/keys).
2. Set `GROQ_API_KEY` in `.env`.
3. Set `GROQ_MODEL=openai/gpt-oss-120b` (current Groq production text model). Alternatives on many accounts include `openai/gpt-oss-20b` or `qwen/qwen3.6-27b`.

The backend uses Groq's OpenAI-compatible Chat Completions API:

- Base URL: `https://api.groq.com/openai/v1`
- Python `openai` SDK with `chat.completions.create`

The key is read only in `backend/config.py` and `backend/llm.py`. Frontend and WordPress never receive it.

## Run locally

Build the FAQ index once (or again after editing `data/dostbin_faq.json`):

```powershell
python backend\build_index.py
```

Start the API and demo UI:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- Demo UI: http://127.0.0.1:8000/
- Embeddable widget: http://127.0.0.1:8000/embed
- Health: http://127.0.0.1:8000/health
- OpenAPI docs: http://127.0.0.1:8000/docs

There is no separate frontend build step. The UI is static files served by FastAPI.

## Production

```powershell
python -m compileall backend
pytest
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Put a reverse proxy (nginx, Caddy, or a cloud load balancer) in front of Uvicorn and serve HTTPS.

## API endpoints

### `GET /health`

```json
{"status":"ok","groq_configured":true,"frontend":true}
```

### `POST /api/chat`

WordPress-friendly chat endpoint.

Request:

```json
{"message":"Which model is automatic?"}
```

Success:

```json
{
  "success": true,
  "response": "The Premium model is fully motorized...",
  "sources": [{"id":"product_01","question":"...","score":0.81}]
}
```

Error:

```json
{"success": false, "error": "GROQ_API_KEY is not configured."}
```

### `POST /ask`

Original RAG endpoint, preserved for existing callers.

Request:

```json
{"question":"Which model is automatic?"}
```

Response:

```json
{
  "question": "Which model is automatic?",
  "answer": "The Premium model is fully motorized...",
  "sources": [{"id":"product_01","question":"...","score":0.81}]
}
```

PowerShell example:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -ContentType "application/json" -Body '{"message":"Which model is automatic?"}'
```

## WordPress integration

Recommended method: **iframe + shortcode plugin**. The iframe loads `/embed` from FastAPI, so the Groq key never leaves the Python server and WordPress does not need CORS for the chat POST.

1. Deploy this FastAPI app with HTTPS.
2. Copy `wordpress/dostbin-chatbot/` into `wp-content/plugins/dostbin-chatbot/`.
3. Activate **DOSTBin Chatbot**.
4. Go to **Settings → DOSTBin Chatbot** and set **Chatbot API URL** to the public FastAPI URL, for example `https://chat.example.com`.
5. Add `[dostbin_chat]` to any page or post.

Do not put `GROQ_API_KEY` in WordPress, wp-config, or the plugin settings.

Optional JavaScript embed (same-origin or CORS-enabled origin):

```html
<div id="dostbin-chat"></div>
<link rel="stylesheet" href="https://YOUR-API-HOST/static/widget.css" />
<script src="https://YOUR-API-HOST/static/widget.js"></script>
<script>
  DostbinChat.mount("#dostbin-chat", { apiBase: "https://YOUR-API-HOST" });
</script>
```

If you use the JS embed from another domain, add that WordPress origin to `ALLOWED_ORIGINS`.

## Security considerations

- `GROQ_API_KEY` stays server-side only.
- CORS is an allowlist, not `*`.
- Chat endpoints are rate-limited per IP.
- Questions are capped at 500 characters.
- Groq is instructed to answer only from retrieved FAQ context and to ignore prompt-injection attempts in the user question.
- Widget output is HTML-escaped to prevent XSS.
- The WordPress plugin only stores the FastAPI URL.
- Do not log API keys. Request bodies are not written to logs.

This API is a public FAQ assistant. If you need it private, put authentication on the reverse proxy.

## Deployment

1. Install Python dependencies on the server.
2. Create `.env` with `GROQ_API_KEY` and `GROQ_MODEL=openai/gpt-oss-120b`.
3. Run `python backend/build_index.py`.
4. Run Uvicorn behind HTTPS.
5. Set `ALLOWED_ORIGINS` if using a cross-origin JS embed.
6. Point the WordPress plugin at the public API URL.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `GROQ_API_KEY is not configured` | `.env` exists in the project root and the process was restarted. |
| `Groq API rejected the request` | Key validity at console.groq.com and that the key has access. |
| `GROQ_MODEL is not available` | Use a current Groq production model such as `openai/gpt-oss-120b`. Check `GET https://api.groq.com/openai/v1/models` with your key. |
| `FAISS index not found` | Run `python backend/build_index.py`. |
| Widget cannot reach API from WordPress | API must be HTTPS and publicly reachable; iframe `src` should be `https://YOUR-API-HOST/embed`. |
| CORS error with JS embed | Add the WordPress origin to `ALLOWED_ORIGINS`. The iframe method does not need CORS. |
| Empty or fallback answers | The question may not match FAQ content. Check `data/dostbin_faq.json` and rebuild the index. |
| Rate limit 429 | Wait and retry, or raise `RATE_LIMIT_REQUESTS`. |
