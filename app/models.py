import re
import unicodedata
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit
from pydantic import BaseModel, Field, model_validator


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s).lower().replace('ł', 'l')) if not unicodedata.combining(c))


GROUPS = [
    ('Białoruś', 'Ostrówek', 'JUMZ', 'ЮМЗ', 'EO-2621', 'ЭО-2621', 'Belarus', 'EO 2621'),
    ('koparko-ladowarka', 'koparko ładowarka', 'koparko ladowarka', 'ekskavatorius krautuvas', 'экскаватор погрузчик'),
    ('koparko-spycharka', 'koparko spycharka', 'ekskavatorius buldozeris'),
    ('ciagnik rolniczy', 'traktor', 'traktorius', 'трактор'),
    ('kombajn', 'kombainas', 'комбайн'),
    ('ladowarka teleskopowa', 'teleskopinis krautuvas', 'телескопический погрузчик'),
]


def variants(query, custom=''):
    out = [query.strip()]
    out.extend(x.strip() for x in custom.split(',') if x.strip())
    for group in GROUPS:
        matched = next((x for x in sorted(group, key=len, reverse=True) if re.search(r'(?<!\w)' + re.escape(norm(x)) + r'(?!\w)', norm(query))), None)
        if matched:
            # Keep make/model modifiers instead of broadening a specific request to all tractors.
            start = norm(query).index(norm(matched))
            out.extend(query[:start] + x + query[start + len(matched):] for x in group)
    return list(dict.fromkeys(out))[:20]


def money(value):
    try:
        s = re.sub(r'[^\d,.-]', '', str(value).replace('\u00a0', ''))
        if ',' in s and '.' in s:
            s = s.replace(',', '') if s.rfind('.') > s.rfind(',') else s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
        d = Decimal(s)
        return float(d) if d.is_finite() and d > 0 else None
    except (InvalidOperation, ValueError):
        return None


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), '', ''))


class Search(BaseModel):
    query: str = Field(min_length=2, max_length=160)
    keywords: str = Field(default='', max_length=500)
    minimum: float | None = Field(default=None, ge=0, le=1e9)
    maximum: float = Field(default=20000, gt=0, le=1e9)
    countries: list[str] = Field(default_factory=lambda: ['PL', 'LT'], min_length=1, max_length=2)
    portals: list[str] = Field(min_length=1, max_length=20)
    photos: bool = False
    hide_damaged: bool = True
    discovery: bool = True

    @model_validator(mode='after')
    def valid(self):
        self.query = self.query.strip()
        if len(self.query) < 2 or set(self.countries) - {'PL', 'LT'}:
            raise ValueError('Wpisz nazwę maszyny i wybierz poprawny kraj.')
        if self.minimum is not None and self.minimum > self.maximum:
            raise ValueError('Cena minimalna nie może przekraczać maksymalnej.')
        return self


PARTS = r'\b(na czesci|czesci do|sprzedam czesci|dalimis|dalys|запчасти|rozbiorka|niekompletn[ay]|bez silnika|sam silnik|katalog|instrukcja obslugi|starteris|puskaсius|atsargines dalys)\b|^(czesci|pompa hydrauliczna|skrzynia biegow|opony|uszczelki|filtr oleju|silnik|variklis|siurblys|padangos|стартер|двигатель)\b'
DAMAGED = r'\b(uszkodzon[ay]|niesprawn[ay]|nie odpala|sugedes|sugedęs|неисправный)\b'


def reject(offer, search, rate):
    title = norm(offer['title'])
    parts_title = re.sub(r'\b(nie na czesci|nie sprzedaje na czesci|nie jest niekompletn[ay])\b', '', title)
    if re.search(PARTS, parts_title, re.I):
        return 'parts'
    if offer.get('sold'):
        return 'sold'
    if not any(norm(v) in title for v in variants(search.query, search.keywords)):
        return 'irrelevant'
    if search.hide_damaged and re.search(DAMAGED, title, re.I):
        return 'damaged'
    if offer.get('country') not in search.countries:
        return 'country'
    price = offer.get('price')
    if price is None or offer.get('currency') not in ('PLN', 'EUR'):
        return 'unknown_price'
    if offer['currency'] == 'EUR' and not rate:
        return 'no_rate'
    pln = round(price * (rate['value'] if offer['currency'] == 'EUR' else 1), 2)
    offer['pln'] = pln
    if pln > search.maximum or (search.minimum is not None and pln < search.minimum):
        return 'budget'
    if search.photos and not offer.get('image'):
        return 'no_photo'
    return None
