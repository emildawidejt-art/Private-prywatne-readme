from .base import Portal

SOURCE = Portal('facebook', 'Facebook Marketplace', 'PL', 'www.facebook.com', 'https://www.facebook.com/marketplace/search/?query={q}', '/marketplace/item/\\d+', local=True, manual=True)
