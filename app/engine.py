import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlsplit, quote
import httpx
from app import db
from app.models import variants, reject, canonical
from app.network import Web, AccessError
from app.sources import SOURCES
from app.sources.base import extract, Portal

MAX_SEARCH_PAGES = 8
MAX_DETAILS = 12


async def exchange_rate():
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get('https://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json')
            r.raise_for_status()
            rate = r.json()['rates'][0]
            return dict(value=rate['mid'], date=rate['effectiveDate'], source='NBP, tabela A')
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return None


def fingerprint(search):
    return hashlib.sha256(json.dumps([search.query.lower().strip(), search.keywords.lower().strip(), sorted(search.countries), sorted(search.portals), search.minimum, search.maximum, search.photos, search.hide_damaged], ensure_ascii=False).encode()).hexdigest()


def status(source, query):
    return dict(id=source.id, name=source.name, country=source.country, state='waiting', pages=0, checked=0,
                found=0, variants=0, message='Oczekuje na wyszukiwanie', url=source.search_url(query))


async def search_portal(web, source, search, report):
    if source.manual:
        report.update(state='failed', message='Brak skonfigurowanego, dozwolonego dostępu do publicznych ofert. Otwórz Marketplace ręcznie; serwis może wymagać logowania.')
        return []
    terms = variants(search.query, search.keywords)
    links, found, errors = [], [], []
    for term in terms[:MAX_SEARCH_PAGES]:
        try:
            html, actual = await web.get(source.search_url(term))
            report['pages'] += 1
            report['variants'] += 1
            links.extend(source.links(html, actual))
            # Only detail pages supply offer records; result snippets are never verified offers.
        except (AccessError, httpx.HTTPError) as e:
            errors.append(str(e))
            if report['pages'] == 0:
                break
    links = list(dict.fromkeys(links))
    for link in links[:MAX_DETAILS]:
        try:
            html, actual = await web.get(link)
            report['checked'] += 1
            extracted = extract(html, actual, source)
            # A product on a search page is not proof of current availability.
            for offer in extracted:
                if canonical(actual) != offer['url']:
                    continue
                offer['checked_at'] = datetime.now(timezone.utc).isoformat()
                offer['evidence'] = 'Otworzono stronę oferty. Samo istnienie strony nie potwierdza dostępności maszyny.'
                found.append(offer)
        except (AccessError, httpx.HTTPError) as e:
            errors.append(str(e))
    report['found'] = len(found)
    if report['pages'] == 0:
        report.update(state='failed', message=errors[0] if errors else 'Brak dostępu do wyników.')
    else:
        message = f"Odczytano {report['pages']} stron wyników i {report['checked']} stron ofert. Warianty: {report['variants']}/{len(terms)}. Limit {MAX_DETAILS} ofert na portal; bez dalszych stron wyników."
        if not found:
            message += ' Nie uzyskano danych konkretnych ofert w obsługiwanym formacie.'
        if errors:
            message += ' ' + errors[0]
        report.update(state='partial', message=message)
    return found


async def discover(web, search, report):
    key = os.environ.get('BRAVE_SEARCH_API_KEY')
    if not key:
        report.update(state='failed', message='Wyszukiwanie dodatkowych stron wymaga klucza oficjalnego API Brave Search. Portale z listy są sprawdzane niezależnie. Dostępne jest wyszukiwanie ręczne.')
        return []
    found, urls = [], []
    async with httpx.AsyncClient(timeout=15) as client:
        for country in search.countries:
            response = await client.get('https://api.search.brave.com/res/v1/web/search',
                headers={'X-Subscription-Token': key}, params={'q': f'{search.query} {search.keywords} używane naudota site:{"pl" if country == "PL" else "lt"}', 'count': 10})
            response.raise_for_status()
            urls.extend(x['url'] for x in response.json().get('web', {}).get('results', []))
    known = {s.domain.removeprefix('www.') for s in SOURCES.values()}
    for url in list(dict.fromkeys(urls))[:12]:
        p = urlsplit(url)
        if not p.hostname or p.hostname.removeprefix('www.') in known or not p.hostname.endswith(('.pl', '.lt')):
            continue
        source = Portal('other', p.hostname, 'LT' if p.hostname.endswith('.lt') else 'PL', p.hostname, '', r'/[^/]+')
        try:
            html, actual = await web.get(url)
            report['pages'] += 1
            extracted = [o for o in extract(html, actual, source) if o['url'] == canonical(actual)]
            found.extend(extracted)
        except (AccessError, httpx.HTTPError):
            continue
    report.update(state='partial', found=len(found), message=f"Sprawdzono {report['pages']} dodatkowych stron. Wyniki indeksu i ograniczony zakres; aktualność do weryfikacji.")
    return found


async def run(job, search):
    web = Web()
    try:
        old = db.previous(job['owner'], job['fingerprint'])
        job['rate'] = await exchange_rate()
        job['message'] = 'Sprawdzanie portali i stron konkretnych ogłoszeń…'
        db.save_job(job)
        gate = asyncio.Semaphore(3)
        seen, images = set(), set()

        async def one(report):
            async with gate:
                report.update(state='running', message='Sprawdzanie publicznych stron…')
                db.save_job(job)
                try:
                    async with asyncio.timeout(180):
                        if report['id'] == 'other':
                            offers = await discover(web, search, report)
                        else:
                            offers = await search_portal(web, SOURCES[report['id']], search, report)
                except TimeoutError:
                    offers = []
                    report.update(state='partial' if report['pages'] else 'failed', message='Osiągnięto limit 3 minut dla portalu. Nie potwierdzono pełnych wyników; sprawdź ręcznie.')
                except Exception:
                    offers = []
                    report.update(state='partial' if report['pages'] else 'failed', message='Nie udało się odczytać odpowiedzi portalu. Spróbuj ponownie lub otwórz wyniki ręcznie.')
                for offer in offers:
                    job['stats']['found'] += 1
                    key = canonical(offer['url'])
                    # Only identical image + title + price is treated as a cross-site duplicate.
                    image_key = (offer.get('image'), offer['title'].casefold(), offer['price'], offer['currency']) if offer.get('image') else None
                    if key in seen or (image_key and image_key in images):
                        job['stats']['duplicates'] += 1
                        continue
                    seen.add(key)
                    if image_key:
                        images.add(image_key)
                    reason = reject(offer, search, job['rate'])
                    if reason:
                        job['rejected'][reason] = job['rejected'].get(reason, 0) + 1
                        continue
                    offer['new'] = old is not None and key not in old
                    job['offers'].append(offer)
                job['offers'].sort(key=lambda x: x['pln'])
                job['completed'] += 1
                db.save_job(job)

        await asyncio.gather(*(one(r) for r in job['reports']))
        job.update(state='done', message='Wyszukiwanie zakończone. Sprawdź zakres i ograniczenia w raporcie portali.')
    except Exception:
        job.update(state='error', message='Wyszukiwanie przerwano przez błąd serwera. Możesz spróbować ponownie.')
    finally:
        await web.close()
        db.save_job(job)
