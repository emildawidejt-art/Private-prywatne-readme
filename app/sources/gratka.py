from .base import Portal

SOURCE = Portal('gratka', 'Gratka', 'PL', 'gratka.pl', 'https://gratka.pl/rolnictwo?tekst={q}', '/[^/]+/[^/]+/ob/\\d+', local=True, manual=False)
