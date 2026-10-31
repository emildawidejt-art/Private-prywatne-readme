import asyncio
import hmac
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from app import db
from app.models import Search, variants
from app.sources import SOURCES
from app.engine import run, fingerprint, status

TASKS = {}
ROOT = Path(__file__).parent


@asynccontextmanager
async def lifespan(app):
    db.init()
    yield
    for task in list(TASKS.values()):
        task.cancel()
    if TASKS:
        await asyncio.gather(*list(TASKS.values()), return_exceptions=True)


app = FastAPI(title='Łowca Maszyn', lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware('http')
async def security(request: Request, call_next):
    # Optional single-user access token for a remotely hosted personal instance.
    password = os.environ.get('APP_PASSWORD')
    if password:
        import base64
        auth = request.headers.get('authorization', '')
        try:
            login = base64.b64decode(auth.removeprefix('Basic ')).decode()
        except Exception:
            login = ''
        if not hmac.compare_digest(login.encode(), f'lowca:{password}'.encode()):
            return JSONResponse({'detail': 'Zaloguj się użytkownikiem lowca.'}, 401, headers={'WWW-Authenticate': 'Basic realm="Lowca Maszyn", charset="UTF-8"'})
    if request.method in ('POST', 'PUT', 'DELETE'):
        origin = request.headers.get('origin')
        expected = os.environ.get('PUBLIC_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL') or str(request.base_url).rstrip('/')
        if origin and origin.rstrip('/') != expected:
            return JSONResponse({'detail': 'Nieprawidłowe źródło żądania.'}, 403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Żądanie z innej strony zostało odrzucone.'}, 403)
    owner = request.cookies.get('lowca_device', '')
    if len(owner) != 48 or any(c not in '0123456789abcdef' for c in owner):
        owner = secrets.token_hex(24)
    # A password-protected installation uses one personal library on all devices.
    request.state.owner = 'personal' if password else owner
    response = await call_next(request)
    secure = request.url.scheme == 'https' or (os.environ.get('PUBLIC_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL') or '').startswith('https://')
    response.set_cookie('lowca_device', owner, max_age=60*60*24*365, httponly=True, samesite='strict', secure=secure)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/')
async def index():
    return HTMLResponse((ROOT / 'static/index.html').read_text())


@app.get('/api/config')
async def config(request: Request):
    owner = request.state.owner
    return dict(portals=[s.info() for s in SOURCES.values()], settings=db.settings(owner),
        history=db.history(owner), favorites=db.saved(owner, 'favorite'), hidden=db.saved(owner, 'hidden'),
        discovery=bool(os.environ.get('BRAVE_SEARCH_API_KEY')), ephemeral=os.environ.get('EPHEMERAL_STORAGE') == 'true')


@app.post('/api/variants')
async def terms(search: Search):
    return variants(search.query, search.keywords)


@app.post('/api/search', status_code=202)
async def start(search: Search, request: Request):
    if set(search.portals) - SOURCES.keys():
        raise HTTPException(400, 'Wybrano nieznany portal.')
    owner = request.state.owner
    if owner in TASKS and not TASKS[owner].done():
        raise HTTPException(409, 'Wyszukiwanie już trwa. Poczekaj na jego zakończenie.')
    if sum(not t.done() for t in TASKS.values()) >= 3:
        raise HTTPException(429, 'Serwer wykonuje inne wyszukiwania. Spróbuj za kilka minut.')
    selected = [s for s in SOURCES.values() if s.id in search.portals and (s.country in search.countries or s.id == 'facebook')]
    if not selected:
        raise HTTPException(400, 'Wybierz przynajmniej jeden portal dla wybranego kraju.')
    reports = [status(s, search.query) for s in selected]
    if search.discovery:
        reports.append(dict(id='other', name='Inne publiczne strony', country='', state='waiting', pages=0, checked=0, found=0,
            variants=0, message='Oczekuje', url='https://www.google.com/search?q='+__import__('urllib.parse', fromlist=['quote']).quote(search.query+' (site:pl OR site:lt)')))
    job = dict(id=str(uuid4()), owner=owner, created=datetime.now(timezone.utc).isoformat(), fingerprint=fingerprint(search),
        settings=search.model_dump(), terms=variants(search.query, search.keywords), state='running', message='Pobieranie aktualnego kursu NBP…',
        completed=0, reports=reports, offers=[], rate=None, stats=dict(found=0, duplicates=0), rejected={})
    db.settings(owner, search.model_dump())
    db.save_job(job)
    task = asyncio.create_task(run(job, search))
    TASKS[owner] = task
    task.add_done_callback(lambda t: TASKS.pop(owner, None) if TASKS.get(owner) is t else None)
    return dict(id=job['id'])


@app.get('/api/search/{ident}')
async def poll(ident: str, request: Request):
    job = db.get_job(request.state.owner, ident)
    if not job:
        raise HTTPException(404, 'Nie odnaleziono wyszukiwania.')
    job.pop('owner', None)
    return job


class Mark(BaseModel):
    job_id: str | None = None
    url: str
    kind: str
    enabled: bool


@app.post('/api/mark')
async def mark(data: Mark, request: Request):
    if data.kind not in ('favorite', 'hidden'):
        raise HTTPException(400, 'Nieprawidłowa akcja.')
    owner = request.state.owner
    job = db.get_job(owner, data.job_id) if data.job_id else None
    candidates = (job or {}).get('offers', []) + db.saved(owner, 'favorite') + db.saved(owner, 'hidden')
    offer = next((x for x in candidates if x['url'] == data.url), None)
    if not offer:
        raise HTTPException(404, 'Nie odnaleziono oferty.')
    db.mark(owner, offer, data.kind, data.enabled)
    return dict(ok=True)


@app.get('/api/health')
async def health():
    return {'ok': True}


@app.get('/sw.js')
async def service_worker():
    return Response((ROOT / 'static/sw.js').read_bytes(), media_type='text/javascript',
                    headers={'Service-Worker-Allowed': '/', 'Cache-Control': 'no-cache'})


@app.get('/static/{name}')
async def static(name: str):
    media = {'style.css': 'text/css', 'app.js': 'text/javascript', 'archive.js': 'text/javascript', 'manifest.webmanifest': 'application/manifest+json',
             'icon-192.png': 'image/png', 'icon-512.png': 'image/png', 'icon.svg': 'image/svg+xml'}
    if name not in media or not (ROOT / 'static' / name).is_file():
        raise HTTPException(404)
    return Response((ROOT / 'static' / name).read_bytes(), media_type=media[name])
