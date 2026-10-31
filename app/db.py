import json
import os
import sqlite3
from pathlib import Path

PATH = Path(os.environ.get('DATA_DIR', 'data')) / 'lowca.sqlite3'


def connect():
    PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(PATH, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c


def init():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS searches(id TEXT PRIMARY KEY, owner TEXT NOT NULL, created TEXT NOT NULL, query TEXT NOT NULL, fingerprint TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS searches_owner ON searches(owner,created);
        CREATE TABLE IF NOT EXISTS saved(owner TEXT NOT NULL, url TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(owner,url,kind));
        CREATE TABLE IF NOT EXISTS settings(owner TEXT PRIMARY KEY, payload TEXT NOT NULL);
        ''')
        for row in c.execute('SELECT id,payload FROM searches').fetchall():
            payload = json.loads(row['payload'])
            if payload['state'] == 'running':
                payload.update(state='interrupted', message='Serwer został ponownie uruchomiony. Uruchom wyszukiwanie jeszcze raz.')
                c.execute('UPDATE searches SET payload=? WHERE id=?', (json.dumps(payload, ensure_ascii=False), row['id']))


def save_job(job):
    with connect() as c:
        c.execute('INSERT OR REPLACE INTO searches VALUES(?,?,?,?,?,?)', (job['id'], job['owner'], job['created'], job['settings']['query'], job['fingerprint'], json.dumps(job, ensure_ascii=False)))


def get_job(owner, ident):
    with connect() as c:
        r = c.execute('SELECT payload FROM searches WHERE owner=? AND id=?', (owner, ident)).fetchone()
    return json.loads(r[0]) if r else None


def history(owner):
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT id,created,query FROM searches WHERE owner=? ORDER BY created DESC LIMIT 50', (owner,))]


def previous(owner, fingerprint):
    with connect() as c:
        rows = c.execute('SELECT payload FROM searches WHERE owner=? AND fingerprint=? ORDER BY created DESC LIMIT 100', (owner, fingerprint)).fetchall()
    for row in rows:
        job = json.loads(row[0])
        if job['state'] == 'done':
            return {x['url'] for x in job['offers']}
    return None


def saved(owner, kind):
    with connect() as c:
        return [json.loads(r[0]) for r in c.execute('SELECT payload FROM saved WHERE owner=? AND kind=?', (owner, kind))]


def mark(owner, offer, kind, enabled):
    with connect() as c:
        if enabled:
            c.execute('INSERT OR REPLACE INTO saved VALUES(?,?,?,?)', (owner, offer['url'], kind, json.dumps(offer, ensure_ascii=False)))
        else:
            c.execute('DELETE FROM saved WHERE owner=? AND url=? AND kind=?', (owner, offer['url'], kind))


def settings(owner, data=None):
    with connect() as c:
        if data is not None:
            c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (owner, json.dumps(data)))
        row = c.execute('SELECT payload FROM settings WHERE owner=?', (owner,)).fetchone()
    return json.loads(row[0]) if row else None
