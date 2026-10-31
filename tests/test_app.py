import asyncio
import copy
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
import httpx
from contextlib import asynccontextmanager
from app import db, engine
from app.main import app
from app.models import Search, variants, money, reject
from app.network import Web, AccessError, public_url
from app.sources import SOURCES
from app.sources.base import extract


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'PATH', tmp_path / 'test.sqlite3')
    monkeypatch.delenv('APP_PASSWORD', raising=False)
    monkeypatch.delenv('BRAVE_SEARCH_API_KEY', raising=False)
    db.init()


def search(**kw):
    return Search(query='JUMZ', portals=['olx'], **kw)


def offer(**kw):
    return dict(dict(title='JUMZ koparka', url='https://www.olx.pl/d/oferta/jumz-ID1.html',
        price=15000, currency='PLN', country='PL', image=None, sold=False), **kw)


@pytest.mark.parametrize('input,expected', [('20 000 zł',20000),('4 500,50',4500.5),('1.234,56',1234.56),('1,234.56',1234.56),('NaN',None),('-1',None),('0',None),('zapytaj',None)])
def test_money(input, expected):
    assert money(input) == expected


def test_aliases_preserve_model_and_prioritize_custom():
    terms = variants('JUMZ', 'moja nazwa')
    assert terms[1] == 'moja nazwa'
    assert 'ЮМЗ' in terms and 'EO-2621' in terms
    assert 'traktorius John Deere' in variants('Ciągnik rolniczy John Deere')
    assert 'traktor' not in variants('Ciągnik rolniczy John Deere')


@pytest.mark.parametrize('title,reason', [('Jumz starteris vietoj puskačiaus','parts'),('Traktory Białoruś - Katalog części zamiennych i zespołów JUMZ-6AM','parts'),('JUMZ na części','parts'),('Pompa hydrauliczna JUMZ','parts'),('JUMZ bez silnika','parts'),('JUMZ uszkodzony','damaged'),('JUMZ stary drobne naprawy',None),('JUMZ sprawny, części w komplecie',None),('JUMZ sprawny nie na części',None),('Kombajn Bizon','irrelevant')])
def test_filter_titles(title, reason):
    assert reject(offer(title=title), search(), None) == reason


def test_eur_budget_and_no_fabricated_rate():
    o=offer(price=5000,currency='EUR',country='LT')
    assert reject(o,search(),None)=='no_rate'
    assert reject(o,search(),{'value':4.5})=='budget'
    assert o['pln']==22500


@pytest.mark.parametrize('change,reason', [({'sold':True},'sold'),({'price':None},'unknown_price'),({'country':None},'country'),({'price':21000},'budget')])
def test_other_filters(change, reason):
    assert reject(offer(**change),search(),None)==reason


def test_photo_and_minimum():
    assert reject(offer(),search(photos=True),None)=='no_photo'
    assert reject(offer(),search(minimum=16000),None)=='budget'


def test_validation():
    with pytest.raises(ValueError): search(minimum=30000)
    with pytest.raises(ValueError): search(countries=['US'])


def product_html(availability='InStock', aggregate=False):
    product={'@type':'Product','name':'JUMZ EO-2621','url':'https://www.olx.pl/d/oferta/jumz-ID1.html','image':['https://images.example.org/machine.jpg'], 'offers':{'@type':'AggregateOffer' if aggregate else 'Offer', 'price':'15000','priceCurrency':'PLN','availability':'https://schema.org/'+availability}}
    return '<script type="application/ld+json">'+json.dumps(product)+'</script>'


def test_extract_actual_photos_and_uncertain_status():
    x=extract(product_html(),offer()['url'],SOURCES['olx'])[0]
    assert x['price']==15000 and x['image']=='https://images.example.org/machine.jpg'
    assert x['status']=='Do weryfikacji'
    assert extract(product_html('SoldOut'),offer()['url'],SOURCES['olx'])[0]['sold']
    assert not extract(product_html(aggregate=True),offer()['url'],SOURCES['olx'])


def test_bad_json_and_search_page_not_offer():
    assert not extract('<script type="application/ld+json">bad</script>', 'https://www.olx.pl/oferty/',SOURCES['olx'])
    assert not SOURCES['olx'].is_detail('https://evil.example/d/oferta/test')
    assert not SOURCES['olx'].is_detail('https://www.olx.pl/oferty/q-jumz/')


@pytest.mark.asyncio
async def test_private_network_blocked():
    for u in ['https://127.0.0.1/a','http://example.org','https://user:pass@example.org','https://[::1]/']:
        with pytest.raises(AccessError): await public_url(u)


@pytest.mark.asyncio
async def test_robots_denial_is_respected(monkeypatch):
    monkeypatch.setattr('app.network.public_url',AsyncMock(return_value=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit('https://example.org/a')))
    w=Web()
    w.raw=AsyncMock(return_value=('User-agent: *\nDisallow: /', 'https://example.org/robots.txt'))
    with pytest.raises(AccessError): await w.get('https://example.org/a')
    assert w.raw.await_count==1
    await w.close()


@pytest.mark.asyncio
async def test_engine_dedup_history_and_missing_rate(monkeypatch):
    monkeypatch.setattr(engine,'exchange_rate',AsyncMock(return_value={'value':4.3,'date':'2026-10-30','source':'test'}))
    mock=AsyncMock(return_value=[offer(),offer(),offer(price=25000,url='https://www.olx.pl/d/oferta/second.html')])
    monkeypatch.setattr(engine,'search_portal',mock)
    s=search()
    j=dict(id='test',owner='owner',fingerprint=engine.fingerprint(s),created=datetime.now(timezone.utc).isoformat(),settings=s.model_dump(),reports=[engine.status(SOURCES['olx'],s.query)],offers=[],stats={'found':0,'duplicates':0},rejected={},completed=0,state='running')
    await engine.run(j,s)
    assert j['state']=='done' and j['stats']['duplicates']==1 and j['rejected']['budget']==1
    assert len(j['offers'])==1 and not j['offers'][0]['new']
    assert db.previous('owner',j['fingerprint'])=={offer()['url']}


@pytest.mark.asyncio
async def test_api_isolation_history_and_marks():
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
        assert (await client.get('/')).status_code==200
        assert len((await client.get('/api/config')).json()['portals'])==14
        assert (await client.post('/api/search',json={'query':'JUMZ','portals':['unknown']})).status_code==400
        assert (await client.post('/api/search',json={'query':'JUMZ','portals':['olx'],'minimum':30000})).status_code==422
        assert (await client.post('/api/mark',json={'url':'https://bad.test','kind':'favorite','enabled':True})).status_code==404
        owner=client.cookies.get('lowca_device')
        j={'id':'mine','owner':owner,'created':'2026-10-31','fingerprint':'x','settings':{'query':'JUMZ'},'state':'done','offers':[offer()]}
        db.save_job(j)
        assert (await client.get('/api/search/mine')).status_code==200
        assert (await client.post('/api/mark',json={'url':offer()['url'],'kind':'favorite','enabled':True,'job_id':'mine'})).status_code==200
        assert len((await client.get('/api/config')).json()['favorites'])==1
        client.cookies.clear()
        assert (await client.get('/api/search/mine')).status_code==404


@pytest.mark.asyncio
async def test_csrf_and_password(monkeypatch):
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        assert (await c.post('/api/search',headers={'Origin':'https://evil.test'},json={})).status_code==403
    monkeypatch.setenv('APP_PASSWORD','test-secret')
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        assert (await c.get('/')).status_code==401
        assert (await c.get('/',auth=('lowca','test-secret'))).status_code==200


def test_recovery_after_restart():
    j={'id':'recover','owner':'owner','created':'2026-10-31','fingerprint':'x','settings':{'query':'JUMZ'},'state':'running'}
    db.save_job(j)
    db.init()
    assert db.get_job('owner','recover')['state']=='interrupted'


@pytest.mark.asyncio
async def test_pwa_assets_and_scope():
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as c:
        manifest = (await c.get('/static/manifest.webmanifest')).json()
        assert manifest['display'] == 'standalone' and manifest['scope'] == '/'
        for icon in manifest['icons']:
            r = await c.get(icon['src'])
            assert r.status_code == 200 and r.content.startswith(b'\x89PNG')
        worker = await c.get('/sw.js')
        assert worker.status_code == 200 and worker.headers['service-worker-allowed'] == '/'
        assert (await c.get('/static/archive.js')).status_code == 200
        assert (await c.get('/static/no-file')).status_code == 404


@pytest.mark.asyncio
async def test_real_job_lifecycle_with_unavailable_manual_source(monkeypatch):
    monkeypatch.setattr(engine, 'exchange_rate', AsyncMock(return_value=None))
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as c:
        r = await c.post('/api/search',json={'query':'JUMZ','portals':['facebook'],'discovery':False})
        assert r.status_code == 202
        await asyncio.sleep(.05)
        job = (await c.get('/api/search/'+r.json()['id'])).json()
        assert job['state'] == 'done' and job['reports'][0]['state'] == 'failed'
        assert not job['offers'] and job['stats']['found'] == 0
        assert (await c.get('/api/config')).json()['settings']['query'] == 'JUMZ'


@pytest.mark.asyncio
async def test_https_behind_render_proxy(monkeypatch):
    monkeypatch.setenv('RENDER_EXTERNAL_URL', 'https://my-app.onrender.com')
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://my-app.onrender.com') as c:
        r = await c.post('/api/variants',headers={'Origin':'https://my-app.onrender.com'},json={'query':'JUMZ','portals':['olx']})
        assert r.status_code == 200 and 'Secure' in r.headers['set-cookie']
