# Łowca Maszyn — Polska i Litwa

Osobista aplikacja FastAPI + SQLite, z polskim interfejsem PWA. Instrukcja użytkownika: [INSTRUKCJA.md](INSTRUKCJA.md).

[![Uruchom w Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/emildawidejt-art/Private-prywatne-readme)

**Gotowy kod nie oznacza opublikowanej aplikacji.** Kliknij przycisk, zaloguj się do Render i potwierdź plan **Free**. Nie dodawaj karty ani płatnego dysku. Po uruchomieniu adres pojawi się w panelu Render. Nazwa repozytorium zawiera słowo „Private”, ale przy sprawdzaniu było ono publiczne; w repozytorium nie ma haseł ani danych użytkownika.


## Uruchomienie dla instalatora

Python 3.11+, zalecany 3.12. Jeden proces Uvicorn (zadania wyszukiwania są obsługiwane w tym procesie). Dla lokalnego użycia:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Windows: `Uruchom-Windows.cmd`. Skrypt `Uruchom.py` przygotowuje środowisko przy pierwszym uruchomieniu i otwiera przeglądarkę.

Docker lokalnie: `docker compose up --build -d`. Wolumen przechowuje SQLite; port jest związany wyłącznie z 127.0.0.1.

Serwer z własną domeną: skopiować `.env.example` do `.env`, ustawić DOMAIN i silne APP_PASSWORD, następnie `docker compose -f compose.server.yaml up --build -d`. Caddy zapewnia HTTPS, wymagane prawidłowe DNS i dostępne porty 80/443. To nie jest instrukcja zakupu serwera; żaden hosting nie jest opłacany automatycznie.

## Bezpłatny Render

`render.yaml` deklaruje jeden serwis **plan: free**, bez dysku, bazy zarządzanej ani usługi w tle. Używa dostarczonego przez Render portu i adresu. Nie podano klucza żadnego płatnego API. Wygenerowane APP_PASSWORD należy odczytać z ustawień środowiska Render i użyć z loginem `lowca`; nigdy nie commitować go do repozytorium. Interfejs i API są chronione tym samym hasłem.

Bezpłatny Render jest odpowiedni do próby osobistej, nie do gwarantowanej usługi produkcyjnej. Pliki SQLite są tam nietrwałe. `EPHEMERAL_STORAGE=true` włącza korzystanie z lokalnej biblioteki w IndexedDB jako kopii historii, ulubionych i ukrytych ofert. Nie jest to synchronizacja między urządzeniami. Brak metody płatności pozwala uniknąć dopłat opisanych w dokumentacji usługi; użytkownik nie powinien zatwierdzać jakichkolwiek płatnych opcji.

Publikacja nie została wykonana. Nie należy podawać przewidywanego adresu jako działającego. Po uzyskaniu repozytorium i uprawnień należy wgrać źródła, połączyć darmową usługę, poczekać na udane wdrożenie i sprawdzić adres, logowanie, PWA i wyszukiwanie z rzeczywistego serwera.

## Konfiguracja

| Zmienna | Znaczenie |
| --- | --- |
| DATA_DIR | Katalog SQLite, domyślnie `data`; powinien być trwały poza bezpłatnym wariantem. |
| APP_PASSWORD | Opcjonalne lokalnie, wymagane przy wystawieniu w internecie. Włącza jedną wspólną bibliotekę osobistej instalacji. Login `lowca`. |
| PUBLIC_ORIGIN | Publiczny adres HTTPS dla ochrony żądań; Render używa automatycznie RENDER_EXTERNAL_URL. |
| EPHEMERAL_STORAGE | `true` dla hostingu kasującego pliki; lokalna kopia biblioteki na urządzeniu. |
| BRAVE_SEARCH_API_KEY | Opcjonalny klucz oficjalnego Brave Search do odkrywania dodatkowych domen. Użytkownik musi wcześniej zatwierdzić ewentualny koszt. Bez klucza aplikacja nie wywołuje tego API. |

Nie wystawiać instalacji bez hasła w internecie. Bez APP_PASSWORD biblioteki są izolowane losowym identyfikatorem urządzenia w ciasteczku HttpOnly. CSRF kontroluje Origin i Sec-Fetch-Site, CSP blokuje skrypty inline i ramki. Podczas odczytu źródeł nie są używane ciasteczka użytkownika ani dane logowania do portali.

## Wyszukiwanie i granice pokrycia

Każdy portal ma osobny plik w `app/sources/`. Wspólny parser odczytuje Product/Vehicle JSON-LD z konkretnych stron ogłoszeń. Nie zakłada, że dowolna strona wyniku jest ogłoszeniem. Akceptuje wyłącznie bezpośrednie adresy spełniające wzorzec danego źródła i zgodne z odczytaną stroną. Nie używa zdjęć poglądowych. AggregateOffer.lowPrice nie jest ceną konkretnej maszyny i nie jest używane.

Robot przestrzega robots.txt (również po przekierowaniach), odstępów, limitów czasu i wielkości strony; brak potwierdzonych reguł jest traktowany zachowawczo. Nie rozwiązuje CAPTCHA, nie loguje się, nie omija blokad, nie podszywa się pod zwykłego użytkownika. Sprawdzanie robots.txt nie zastępuje kontroli warunków korzystania danego portalu. Przed rozszerzeniem adaptera instalator powinien sprawdzić bieżące warunki i dostępność oficjalnego API.

Każde źródło sprawdza maksymalnie 8 wariantów, pierwszą stronę wyników każdego wariantu i do 12 adresów ofert. 3 źródła są przetwarzane równolegle, limit źródła wynosi 180 sekund. Taki ograniczony odczyt jest oznaczony jako **Przeszukano częściowo**, nigdy jako pełne przeszukanie serwisu. Nie ma gwarancji znalezienia wszystkich ofert. Moduły nie realizują jeszcze dedykowanych, uwierzytelnionych integracji API poszczególnych portali.

Facebook ma wyłącznie jawnie oznaczony tryb ręczny. Dodatkowe domeny odkrywa wyłącznie opcjonalne oficjalne API Brave, nie ma skrobania wyników Google ani Bing. Odsyłacz Google służy do ręcznego otwarcia w przeglądarce.

Filtry stosują rozpoznane tytuły, kraj, jednoznaczne ceny/waluty i schemat availability. Stan techniczny nie jest zgadywany z wieku maszyny. Aktualność pozostaje „Do weryfikacji” również po udanym otwarciu strony. Filtr części jest heurystyką i wymaga dalszego rozwijania dla nowych języków i kategorii; nie zapewnia bezbłędnej klasyfikacji.

Duplikaty: kanoniczny adres lub identyczny obraz, tytuł, cena i waluta. Nie usuwa ofert wyłącznie z powodu podobnego tytułu. Oferty z nieznaną ceną, walutą lub krajem są odnotowane w powodach odrzucenia; nie zgaduje się tych danych. Dla międzynarodowych portali kraj musi wynikać z odczytanego adresu oferty. EUR przelicza publiczne API NBP bez awaryjnego, wymyślonego kursu.

Historia w SQLite ma trwałość wolumenu serwera. Zadania przerwane restartem są oznaczane jako przerwane. Dane wszystkich wyszukiwań są przechowywane w SQLite; interfejs pokazuje ostatnie 50, a kopia IndexedDB przechowuje maksymalnie 50 zakończonych zadań. Brak automatycznego harmonogramu.

## Testy

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
node --check app/static/app.js
node --check app/static/archive.js
node --check app/static/sw.js
```

Opcjonalny test przeglądarki wymaga Playwright i Chromium. Nie pobiera ani nie publikuje przykładowych ofert:

```sh
PYTHONPATH=. .venv/bin/python tests/browser_smoke.py
```

Testy nie są dowodem stałego dostępu do portali. Wyniki kontroli w `RAPORT-TESTOW.md`.
