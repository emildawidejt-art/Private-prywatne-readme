import json
import re
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlsplit
from bs4 import BeautifulSoup
from app.models import money, canonical


def nodes(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from nodes(v)
    elif isinstance(value, list):
        for v in value:
            yield from nodes(v)


def jsonld(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data.extend(nodes(json.loads(script.get_text())))
        except (json.JSONDecodeError, TypeError, RecursionError):
            continue
    return soup, data


def safe_link(url, base):
    if not isinstance(url, str):
        return None
    result = urljoin(base, url)
    return result if urlsplit(result).scheme == 'https' else None


def extract(html, url, source):
    soup, data = jsonld(html)
    offers = []
    for node in data:
        types = node.get('@type', [])
        types = types if isinstance(types, list) else [types]
        if not set(types) & {'Product', 'Vehicle', 'Car', 'IndividualProduct'}:
            continue
        title = node.get('name')
        if not isinstance(title, str) or len(title) < 3:
            continue
        raw = node.get('offers', {})
        raw = raw[0] if isinstance(raw, list) and raw else raw
        raw = raw if isinstance(raw, dict) else {}
        # AggregateOffer.lowPrice is not the price of a concrete machine.
        price = money(raw.get('price'))
        if raw.get('@type') == 'AggregateOffer':
            continue
        link = safe_link(raw.get('url') or node.get('url') or url, url)
        if not link or not source.is_detail(link):
            continue
        image = node.get('image')
        image = image[0] if isinstance(image, list) and image else image
        image = image.get('url') or image.get('contentUrl') if isinstance(image, dict) else image
        image = safe_link(image, url) if image else None
        address = node.get('availableAtOrFrom') or raw.get('availableAtOrFrom') or node.get('location') or {}
        if not isinstance(address, dict):
            address = {}
        address = address.get('address', address)
        if not isinstance(address, dict):
            address = {}
        country = address.get('addressCountry')
        if isinstance(country, dict):
            country = country.get('name')
        countries = {'PL':'PL', 'Polska':'PL', 'Poland':'PL', 'LT':'LT', 'Lithuania':'LT', 'Lietuva':'LT'}
        country = countries.get(country, source.country if source.local else None)
        availability = str(raw.get('availability', ''))
        sold = any(s in availability for s in ('SoldOut', 'OutOfStock', 'Discontinued'))
        condition = str(node.get('itemCondition') or raw.get('itemCondition') or '')
        offers.append(dict(title=title[:250], url=canonical(link), image=image, price=price,
            currency=str(raw.get('priceCurrency', '')).upper(), country=country,
            location=address.get('addressLocality') or 'Miejscowość niepodana', portal=source.name,
            published=node.get('datePosted') or node.get('datePublished'),
            condition='Używana — według ogłoszenia' if 'UsedCondition' in condition else 'Stan techniczny do weryfikacji',
            status='Do weryfikacji', sold=sold, tax='Nie potwierdzono, czy cena zawiera VAT'))
    return offers


@dataclass
class Portal:
    id: str
    name: str
    country: str
    domain: str
    template: str
    pattern: str
    local: bool = True
    manual: bool = False

    def search_url(self, query):
        return self.template.format(q=quote(query, safe=''), slug=quote(query.lower().replace(' ', '-'), safe=''))

    def is_detail(self, url):
        p = urlsplit(url)
        return p.scheme == 'https' and p.hostname == self.domain and bool(re.search(self.pattern, p.path))

    def links(self, html, base):
        soup, data = jsonld(html)
        links = [safe_link(a.get('href'), base) for a in soup.select('a[href]')]
        links.extend(safe_link(n.get('url'), base) for n in data if n.get('url'))
        return list(dict.fromkeys(canonical(x) for x in links if x and self.is_detail(x)))

    def info(self):
        return dict(id=self.id, name=self.name, country=self.country, domain=self.domain, manual=self.manual)
