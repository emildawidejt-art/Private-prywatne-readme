from .base import Portal

SOURCE = Portal('machineryline_lt', 'Machineryline LT', 'LT', 'machineryline.lt', 'https://machineryline.lt/search_text.php?query={q}', '/-/(?:prekyba|pardavimas)/.+--\\d+', local=False, manual=False)
