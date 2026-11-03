# Site Shelf - website preview app

Sign up, log in, paste a website URL, see a visual preview of the page, and keep every
saved URL (with its preview) in your own library.

- **Frontend:** React 18 + Vite + React Router
- **Backend:** FastAPI + SQLAlchemy (SQLite by default) + JWT auth + Playwright (headless Chromium)

```
website-preview-app/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, CORS, static preview files
│   │   ├── config.py          Settings from environment / .env
│   │   ├── database.py        SQLAlchemy engine + session
│   │   ├── models.py          User, Site
│   │   ├── schemas.py         Request / response models
│   │   ├── security.py        bcrypt hashing, JWT, current-user dependency
│   │   ├── preview.py         URL safety checks + preview generation
│   │   └── routers/
│   │       ├── auth.py        POST /api/auth/signup, /login, GET /me
│   │       └── sites.py       POST/GET /api/sites, DELETE /api/sites/{id}
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/ (App, AuthContext, api client, Login, Signup, Dashboard, PreviewCard, styles)
    ├── package.json
    └── .env.example
```

## 1. Run the backend

Requires Python 3.10+.

```bash
cd backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium         # downloads the headless browser used for screenshots
cp .env.example .env                # Windows: copy .env.example .env  (then set SECRET_KEY)
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## 2. Run the frontend

Requires Node 18+.

```bash
cd frontend
npm install
cp .env.example .env                # Windows: copy .env.example .env
npm run dev
```

Open http://localhost:5173, create an account, and paste a URL. The dashboard has a
"Fill in the test URL" link that inserts the Justdial listing URL.

## How previews work

When you submit a URL the backend tries these in order and saves the first that works:

1. **Screenshot** with headless Chromium (Playwright).
2. **Screenshot via thum.io** if the browser was blocked (many sites, Justdial included,
   block headless browsers or cloud IPs). Disable with `USE_THUMIO_FALLBACK=false` in
   `backend/.env` - note this fallback sends the submitted URL to thum.io.
3. **The page's own Open Graph image** (`og:image`).
4. **A generated placeholder card**, so every saved URL always has a preview.

Each card shows which kind of preview it is. Images are stored in `backend/previews/`;
URLs and metadata are stored in the SQLite database `backend/app.db`.

## API summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/signup` | no | `{name, email, password}` → token + user |
| POST | `/api/auth/login` | no | `{email, password}` → token + user |
| GET | `/api/auth/me` | yes | current user |
| POST | `/api/sites` | yes | `{url}` → captures preview, saves, returns the record |
| GET | `/api/sites` | yes | the current user's saved URLs, newest first |
| DELETE | `/api/sites/{id}` | yes | remove a saved URL and its image |

Send the token as `Authorization: Bearer <token>`.

## Notes

- Passwords are hashed with bcrypt (8-72 characters). Tokens are JWTs valid for 24 hours
  by default (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Submitted URLs must be public http(s) addresses; private/loopback addresses are
  rejected to prevent server-side request forgery.
- Preview image files have random names and are served without auth; saved URL records
  are only visible to the user who saved them.
- Production: set a strong `SECRET_KEY`, set `CORS_ORIGINS` to your frontend origin, set
  `VITE_API_URL` before `npm run build`, and consider Postgres via `DATABASE_URL`.
