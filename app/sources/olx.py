from .base import Portal

SOURCE = Portal('olx', 'OLX', 'PL', 'www.olx.pl', 'https://www.olx.pl/oferty/q-{slug}/', '/d/oferta/.+', local=True, manual=False)
