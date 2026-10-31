# Raport weryfikacji

## Potwierdzone

- 37 testów automatycznych Python: poprawne zakończenie. Obejmują ceny, kurs EUR, budżet, polskie i litewskie przykłady części, uszkodzenia, zachowanie starych maszyn, warianty nazw z zachowaniem marki/modelu, deduplikację, parser konkretnych ofert, dostęp do prywatnych adresów, odmowę robots.txt, zapis historii i ulubionych, izolację urządzeń, ochronę Origin, logowanie, odtwarzanie po restarcie, pliki PWA, cykl zadania i HTTPS za proxy Render.
- Kontrola składni JavaScript: `app.js`, `archive.js`, `sw.js`.
- Test prawdziwej przeglądarki Chromium w rozmiarze telefonu 390 × 844 oraz komputera 1280 × 900: poprawne zakończenie. Sprawdzono brak przewijania poziomego, zmianę nazwy przez podpowiedź, wybór źródła, wykonanie wyszukiwania, brak wymyślonych wyników przy niedostępnym źródle, raport, historię, pomoc, dodawanie do ulubionych, ukrywanie i przywracanie, bezpieczne wyświetlanie tytułu z fragmentem HTML oraz zachowanie historii i ulubionych w IndexedDB po symulowanej utracie całej bazy SQLite. Bez błędów JavaScript. Syntetyczna oferta do testu interakcji istnieje wyłącznie w tymczasowej bazie testowej; nie znajduje się w danych aplikacji ani na udostępnionym podglądzie.
- Rzeczywisty odczyt publicznych wyników Skelbiu i Sprzedajemy w środowisku testowym: znaleziono odpowiednio 24 i 30 adresów potencjalnych ofert dla JUMZ. Odczytano po jednej stronie konkretnego ogłoszenia; oba zawierały obsługiwany Product JSON-LD, cenę, walutę i zdjęcie. Były to części (starter i katalog), nie maszyny — dodano testy ich odrzucania. Nie są to dane demonstracyjne w aplikacji.
- Skontrolowano formularze wyszukiwania Machineryline PL/LT; na tej podstawie poprawiono adres modułu z niedziałającego endpointu na `search_text.php?query=...`. Nie jest to dowód pełnego działania przeszukiwania tych portali.
- Sprawdzono oficjalne warunki Render Free i instrukcję instalacji aplikacji internetowych w Chrome na Androidzie.

## Wymaga sprawdzenia po publikacji

- Dostęp do każdego portalu z docelowego serwera i uzyskiwanie rzeczywistych ofert maszyn, nie tylko adresów lub ofert części.
- Skuteczność filtrów w szerszej próbce ogłoszeń wszystkich serwisów i języków.
- Odczyt regionów, dat i cen z serwisów, których dane nie mieszczą się w obsługiwanym JSON-LD. Wtedy aplikacja jawnie oznacza brak obsługiwanych danych.
- Instalacja ikony na fizycznym telefonie z Androidem i test pod rzeczywistym adresem HTTPS. Przygotowanie manifestu i ikon nie stanowi dowodu instalacji na telefonie użytkownika.
- Działanie nowego wyszukiwania po uśpieniu bezpłatnego serwera i ponownym zalogowaniu.

## Publikacja

**Aplikacja nie została opublikowana.** Nie uzyskano produkcyjnego adresu ani potwierdzenia udanego wdrożenia. Narzędzie Sites nie ma w tym środowisku lokalnych plików wspierających publikację, a hosting Sites nie uruchamia bezpośrednio tej aplikacji FastAPI/Python. Przygotowano alternatywny `render.yaml` dla darmowego serwera Python.

Nie zakupiono hostingu, domeny, bazy ani dostępu do API. Repozytorium GitHub wskazano i potwierdzono prawo zapisu. Pozostaje konfiguracja bezpłatnego konta hostingowego, wykonanie wdrożenia i weryfikacja uzyskanego adresu.
