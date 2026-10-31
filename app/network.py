import asyncio
import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import httpx

AGENT = 'LowcaMaszyn/1.0'


class AccessError(Exception):
    pass


async def public_url(url):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise AccessError('Niedozwolony adres strony.')
    try:
        literal = ipaddress.ip_address(p.hostname)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise AccessError('Adres nie jest publiczną stroną internetową.')
        return p
    try:
        addresses = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM), timeout=5)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise AccessError('Adres nie jest publiczną stroną internetową.')
    except (socket.gaierror, TimeoutError) as e:
        raise AccessError('Nie odnaleziono serwera portalu.') from e
    return p


class Web:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(14), headers={'User-Agent': AGENT, 'Accept-Language': 'pl,lt;q=0.8'}, follow_redirects=False)
        self.robots = {}
        self.locks = {}
        self.last = {}

    async def close(self):
        await self.client.aclose()

    async def raw(self, url, host):
        for _ in range(4):
            p = await public_url(url)
            if p.hostname != host:
                raise AccessError('Przekierowanie do innej domeny — sprawdź ręcznie.')
            if host in self.robots and not self.robots[host].can_fetch(AGENT, url):
                raise AccessError('Reguły robots.txt zabraniają pobrania strony docelowej przekierowania.')
            async with self.client.stream('GET', url) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = urljoin(url, response.headers.get('location', ''))
                    continue
                if response.status_code == 404:
                    raise AccessError('Strona nie istnieje (404).')
                if response.status_code in (401, 403, 429):
                    raise AccessError(f'Portal ogranicza automatyczny dostęp (HTTP {response.status_code}).')
                if response.status_code != 200:
                    raise AccessError(f'Błąd portalu (HTTP {response.status_code}).')
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > 6_000_000:
                        raise AccessError('Strona przekracza limit rozmiaru pobierania.')
                    chunks.append(chunk)
                text = b''.join(chunks).decode('utf-8', errors='replace')
                if any(x in text.lower() for x in ['cf-chl-', 'g-recaptcha', '<title>just a moment', 'verify you are human']):
                    raise AccessError('Portal wymaga potwierdzenia w przeglądarce. Nie obchodzimy zabezpieczeń.')
                return text, url
        raise AccessError('Zbyt wiele przekierowań.')

    async def get(self, url):
        p = await public_url(url)
        host = p.hostname
        async with self.locks.setdefault(host, asyncio.Lock()):
            if host not in self.robots:
                try:
                    text, _ = await self.raw(f'https://{host}/robots.txt', host)
                    parser = RobotFileParser()
                    parser.parse(text.splitlines())
                    # HTML instead of robots cannot establish crawl permission.
                    if '<html' in text.lower():
                        raise AccessError('Nie można potwierdzić reguł dostępu portalu.')
                    self.robots[host] = parser
                except (AccessError, httpx.HTTPError):
                    raise AccessError('Nie można potwierdzić reguł robots.txt. Otwórz wyniki ręcznie.')
            rules = self.robots[host]
            if not rules.can_fetch(AGENT, url):
                raise AccessError('Reguły robots.txt zabraniają pobrania tej strony.')
            delay = max(1.0, rules.crawl_delay(AGENT) or rules.crawl_delay('*') or 0)
            if delay > 15:
                raise AccessError('Portal wymaga zbyt długich odstępów. Otwórz wyniki ręcznie.')
            await asyncio.sleep(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
            self.last[host] = time.monotonic()
            try:
                return await self.raw(url, host)
            except httpx.HTTPError as e:
                raise AccessError('Portal nie odpowiedział w limicie czasu lub wystąpił błąd połączenia.') from e
