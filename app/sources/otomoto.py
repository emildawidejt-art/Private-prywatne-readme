from .base import Portal

SOURCE = Portal('otomoto', 'Otomoto', 'PL', 'www.otomoto.pl', 'https://www.otomoto.pl/maszyny-rolnicze?search%5Bfilter_enum_make%5D=&search%5Bfilter_float_price%3Ato%5D=&search%5Badvanced_search_expanded%5D=true&q={q}', '/(?:maszyny-rolnicze|maszyny-budowlane)/oferta/.+', local=True, manual=False)
