from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import sqlite3
import secrets
import string

app = FastAPI()

db = sqlite3.connect("shortener.db", check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("""
    CREATE TABLE IF NOT EXISTS links (
        code TEXT PRIMARY KEY,
        target_url TEXT NOT NULL,
        clicks INTEGER NOT NULL DEFAULT 0
    )
""")
db.commit()

ALPHABET = string.ascii_letters + string.digits

def make_code(n=7):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


class ShortenRequest(BaseModel):
    url: str


@app.get("/")
async def home():
    return {"hello": "world"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/count")
async def count():
    row = db.execute("SELECT COUNT(*) AS n FROM links").fetchone()
    return {"links": row["n"]}


@app.get("/links")
async def links():
    rows = db.execute("SELECT code, target_url, clicks FROM links").fetchall()
    return [dict(r) for r in rows]


@app.post("/shorten", status_code=201)
async def shorten(body: ShortenRequest):
    code = make_code()
    db.execute(
        "INSERT INTO links (code, target_url) VALUES (?, ?)",
        (code, body.url),
    )
    db.commit()
    return {"code": code, "short": f"/{code}"}


@app.get("/{code}")
async def redirect(code: str):
    row = db.execute(
        "SELECT target_url FROM links WHERE code = ?", (code,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="short link not found")
    db.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
    db.commit()
    return RedirectResponse(url=row["target_url"], status_code=302)