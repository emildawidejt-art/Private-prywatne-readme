from .base import Portal

SOURCE = Portal('machineryline_pl', 'Machineryline PL', 'PL', 'machineryline.pl', 'https://machineryline.pl/search_text.php?query={q}', '/-/sprzedaz/.+--\\d+', local=False, manual=False)
