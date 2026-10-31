from .base import Portal

SOURCE = Portal('autogidas', 'Autogidas', 'LT', 'autogidas.lt', 'https://autogidas.lt/paieska/?q={q}', '/skelbimas/.+-\\d+\\.html', local=True, manual=False)
