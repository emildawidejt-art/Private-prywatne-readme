# Łowca Maszyn — instrukcja po polsku

## Aktualny stan

Aplikacja jest napisana i przygotowana do uruchomienia. **Nie została jeszcze opublikowana. Nie ma jeszcze potwierdzonego adresu internetowego do otwarcia na telefonie.**

Gotowe są: polski widok na telefon i komputer, wyszukiwanie uruchamiane przyciskiem, filtry, przeliczanie euro po kursie NBP, raporty dostępu do portali, ulubione, ukrywanie ofert, historia oraz pliki potrzebne do dodania ikony na ekranie Androida.

Nie potwierdzono niezawodnego przeszukiwania wszystkich portali. Serwisy mogą blokować dostęp, zmieniać strony albo nie udostępniać odczytywanych danych. Wtedy aplikacja pokazuje ograniczenie i link do ręcznego otwarcia wyników. Nie ma przykładowych ogłoszeń udających prawdziwe wyniki.

## Najprostsza bezpłatna droga na telefon

Proponowana usługa: **Render, plan Free**. Nie trzeba kupować domeny. Usługa przydzieli adres internetowy i zabezpieczone połączenie.

Najbliższy krok dla Ciebie:

1. Otwórz [Uruchom aplikację w Render](https://render.com/deploy?repo=https://github.com/emildawidejt-art/Private-prywatne-readme).
2. Zaloguj się lub załóż bezpłatne konto Render. Możesz użyć przycisku GitHub.
3. Jeśli pojawi się prośba o dostęp do GitHub, udostępnij wskazane repozytorium `Private-prywatne-readme`.
4. Na ekranie uruchomienia sprawdź, że usługa `lowca-maszyn` ma plan **Free**. Pozostaw nazwę bez zmian, chyba że usługa zgłosi konflikt nazwy. Wtedy dopisz na końcu swój dowolny identyfikator.
5. Kliknij **Deploy / Create resources / Apply** (nazwa zależy od widoku). Nie wybieraj płatnego planu, dysku ani bazy. Nie dodawaj karty. Jeśli usługa zażąda płatności lub karty, zatrzymaj się i napisz o tym w rozmowie.
6. Po ukończeniu uruchomienia w panelu usługi będzie adres kończący się `.onrender.com`. Prześlij go w rozmowie, aby można było zweryfikować działanie.

Nie musisz wpisywać komend ani ręcznie kopiować plików. Konto GitHub i repozytorium zostały już wskazane; pozostaje zalogowanie właściciela do Render i utworzenie bezpłatnej usługi. Repozytorium jest publiczne mimo nazwy „Private-prywatne-readme”. Zawiera wyłącznie kod i dokumentację, bez haseł i historii użytkownika.

Hasło logowania aplikacji zostanie automatycznie wygenerowane przez Render. Odczytaj pole **APP_PASSWORD** w zakładce **Environment** usługi. Nie wklejaj hasła do publicznego repozytorium ani do rozmowy. Login aplikacji to `lowca`. Jeśli nie możesz znaleźć hasła, opisz, jaki ekran widzisz — bez ujawniania hasła.

Nie została wykonana żadna operacja zakupu.

## Ważne ograniczenia bezpłatnego serwera

- Po około 15 minutach nieużywania serwer może zasnąć. Pierwsze otwarcie po przerwie może trwać około minuty.
- Bezpłatny serwer usuwa lokalne pliki po uśpieniu lub restarcie. Dlatego aplikacja dodatkowo zapisuje do 50 zakończonych wyszukiwań oraz ulubione i ukryte oferty **w przeglądarce Twojego telefonu**.
- Nie usuwaj danych tej witryny. Kopia z jednego telefonu nie synchronizuje się automatycznie z drugim telefonem ani komputerem. W trybie incognito lub po zapełnieniu pamięci zapis może nie być trwały.
- Oznaczenia „Nowa” porównują wyszukiwania dostępne w bazie serwera. Po wyczyszczeniu serwera pierwsze wyszukiwanie nie ma poprzedniego punktu porównania.
- Obowiązują limity bezpłatnej usługi. Nie ma gwarancji ciągłego działania ani gwarancji, że portale zaakceptują połączenia z serwera Render.

Warunki sprawdzono w oficjalnej dokumentacji: https://render.com/docs/free .

## Dodanie ikony na Androidzie — po publikacji

1. Otwórz otrzymany i potwierdzony adres aplikacji w **Chrome** na telefonie.
2. Przy pierwszym otwarciu zaloguj się danymi prywatnej instalacji. Nazwa użytkownika: `lowca`. Hasło zostanie ustalone przy uruchamianiu serwera.
3. Naciśnij menu **⋮**.
4. Wybierz **Dodaj do ekranu głównego** albo **Zainstaluj i utwórz skrót → Zainstaluj**. Nazwa zależy od wersji Chrome.
5. Potwierdź dodanie. Od tej chwili otwieraj aplikację przez ikonę **Łowca Maszyn**.

Nie instalujesz plików APK i nie kopiujesz plików na telefon. Wyszukiwanie wymaga internetu.

Oficjalna pomoc Chrome: https://support.google.com/chrome/answer/9658361?hl=pl&co=GENIE.Platform%3DAndroid .

## Korzystanie z wyszukiwarki

1. Wpisz nazwę maszyny, np. JUMZ, Ostrówek lub ładowarka teleskopowa.
2. Ustaw cenę maksymalną. Domyślnie wynosi 20 000 zł.
3. Wybierz Polskę, Litwę lub oba kraje.
4. W „Portale i dodatkowe filtry” wybierz serwisy, dodatkowe nazwy i filtry.
5. Naciśnij **Szukaj ofert**. Sprawdzanie może potrwać kilka minut.
6. Przeczytaj **Raport jakości wyszukiwania**. Przycisk „Otwórz wyniki” pozwala sprawdzić zablokowany portal samodzielnie.
7. Kliknięcie oferty otwiera oryginalne ogłoszenie. Gwiazdka zapisuje ofertę w ulubionych. „Ukryj” przenosi ją do zakładki Ukryte, skąd można ją przywrócić.

Wyniki są sortowane od najtańszych. Cena w euro jest przeliczana po najnowszym dostępnym średnim kursie NBP; przy wynikach widać datę kursu. To nie jest gwarantowany kurs zakupu euro. Przy braku kursu oferty w euro nie są porównywane ze złotowym budżetem.

„Do weryfikacji” oznacza, że nie potwierdzono dostępności lub stanu maszyny. Sam odczyt strony nie potwierdza, że sprzedawca nadal ją ma. Ceny mogą nie obejmować VAT, transportu i innych opłat — sprawdź to u sprzedawcy.

## Uruchomienie na komputerze — opcja dodatkowa

Telefon nie wymaga tej metody. Służy ona do lokalnego uruchomienia na komputerze z Pythonem 3.11 lub nowszym:

- Windows: otwórz `Uruchom-Windows.cmd`.
- Linux lub macOS: uruchom plik `Uruchom-Linux-Mac.sh`.

Przy pierwszym uruchomieniu program pobierze składniki, a następnie otworzy przeglądarkę. Pozostaw okno programu otwarte. Adres lokalny działa tylko na tym komputerze i nie zastępuje publikacji w internecie.
