from .base import Portal

SOURCE = Portal('sprzedajemy', 'Sprzedajemy', 'PL', 'sprzedajemy.pl', 'https://sprzedajemy.pl/szukaj?inp_text={q}', '/[^/]+-nr\\d+', local=True, manual=False)
