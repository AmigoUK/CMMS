#!/usr/bin/env python3
"""Seed Polish translations for the new Help articles (transfers, reports)
plus refreshed Polish content for property + admin + faq + index articles
that gained v0.1.4 additions.

Idempotent — only updates content if it differs from current.

Run:  uv run python seed_help_v015.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models.help_content import HelpContent  # noqa: E402
from models.translation import Translation  # noqa: E402


# ── Polish help articles for new pages ──────────────────────────────────
NEW_HELP_PAGES = {
    "transfers": {
        "title": "Transfery części",
        "content": """\
<h4 class="mb-3"><i class="bi bi-arrow-left-right me-2"></i>Transfery części</h4>
<p class="text-muted mb-4">
    Każdy obiekt to osobne konto budżetowe z własnym magazynem części. Gdy
    jeden obiekt potrzebuje części, której inny ma w nadwyżce, nie trzeba
    zamawiać nowej — można zrobić transfer. Każdy transfer jest zapisany
    z dwiema stronami (źródło: -, cel: +) i pełnym śladem audytu.
</p>

<div class="alert alert-info">
    <i class="bi bi-info-circle me-2"></i>
    <strong>Kto co może?</strong>
    <strong>Supervisor obiektu źródłowego</strong> zgłasza transfer.
    <strong>Supervisor obiektu docelowego</strong> go zatwierdza.
    Administratorzy mogą obie czynności. Dwustronne uprawnienia
    zapobiegają cichemu „ściąganiu" stanu z innego obiektu.
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-arrow-repeat me-2"></i>Cykl życia transferu</h5>
        <div class="d-flex flex-wrap align-items-center gap-2 mb-3 justify-content-center">
            <span class="badge bg-warning text-dark fs-6">Oczekujący</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-success fs-6">Zakończony</span>
        </div>
        <div class="text-center mb-3">
            <span class="text-muted small">lub na etapie oczekiwania:</span>
            <span class="badge bg-secondary fs-6 ms-2">Anulowany</span>
        </div>
        <ul class="mb-0 small">
            <li><strong>Oczekujący</strong> — supervisor źródła zgłosił. Stan magazynowy jeszcze się nie zmienił. Każda ze stron może anulować.</li>
            <li><strong>Zakończony</strong> — supervisor celu zatwierdził. Stan zmniejszony w źródle, zwiększony (lub utworzony) w celu, atomowo. Powstają dwa powiązane wpisy <em>Stock Adjustment</em>.</li>
            <li><strong>Anulowany</strong> — bez ruchu magazynowego, tylko zapis zgłoszenia i powodu anulowania.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-plus-circle me-2"></i>Zgłaszanie transferu</h5>
        <ol>
            <li>Przełącz się na <strong>obiekt źródłowy</strong> przełącznikiem w pasku nawigacyjnym.</li>
            <li>Otwórz część w <em>Magazyn → Części</em>. Kliknij przycisk <span class="badge bg-warning text-dark"><i class="bi bi-arrow-left-right"></i> Zgłoś transfer</span> (widoczny tylko gdy część ma stan na magazynie).</li>
            <li>Wybierz obiekt docelowy (tylko obiekty, do których masz dostęp — administratorzy widzą wszystkie).</li>
            <li>Wprowadź ilość (nie większą niż stan źródła) i opcjonalną notatkę.</li>
            <li>Zatwierdź. Transfer staje się <span class="badge bg-warning text-dark">Oczekujący</span>.</li>
        </ol>
        <p class="small text-muted mb-0">
            Cena jednostkowa źródła jest zapisywana w momencie zgłoszenia, dzięki
            czemu wartość transferu pozostaje poprawna nawet jeśli ceny się zmienią.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-check-circle me-2"></i>Zatwierdzanie transferu</h5>
        <p class="small text-muted">
            Oczekujące transfery są widoczne w dwóch miejscach po zalogowaniu
            jako supervisor obiektu docelowego:
        </p>
        <ul>
            <li>Pozycja <strong>Magazyn</strong> w nawigacji pokazuje licznik (niski stan + oczekujące transfery).</li>
            <li><strong>Pulpit</strong> wyświetla kartę „Transfery oczekujące na Twoje zatwierdzenie".</li>
        </ul>
        <p class="small mb-0">
            Wejdź w szczegóły transferu. Sprawdź część, ilość i źródło. Kliknij
            <span class="badge bg-success">Zatwierdź i zakończ</span>. Stan
            zmienia się natychmiast. Jeśli obiekt docelowy nie ma jeszcze tej
            części (dopasowanie po numerze części), zostanie utworzona z tymi
            samymi danymi katalogowymi i przekazaną ilością.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-cart me-2"></i>Nadwyżka w innych lokalizacjach na raporcie zamówień</h5>
        <p class="small">
            Na <em>Magazyn → Raport zamówień</em>, gdy część ma stan poniżej
            minimum <strong>i</strong> inny obiekt trzyma więcej niż własne
            maksimum, pojawia się zielony baner „Nadwyżka w innych
            lokalizacjach" z linkami „Zgłoś transfer". Użyj ich <em>przed</em>
            złożeniem zamówienia u dostawcy — oszczędzasz pieniądze.
        </p>
        <p class="small mb-0">
            Baner uwzględnia także oczekujące transfery przychodzące, więc
            niedobór jest <em>netto</em> po uwzględnieniu spodziewanych dostaw.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-x-circle me-2"></i>Anulowanie oczekującego transferu</h5>
        <p class="small mb-0">
            Anulować może: zgłaszający, supervisor obiektu źródłowego lub
            docelowego, administrator. Podaj krótki powód — zostanie pokazany
            w szczegółach. <strong>Zakończonych transferów nie można
            anulować</strong> — by „cofnąć" wykonany transfer, zgłoś nowy
            transfer w przeciwnym kierunku.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-patch-question me-2"></i>Najczęstsze pytania</h5>
        <dl class="small mb-0">
            <dt>Co jeśli obiekt docelowy nie ma jeszcze tej części?</dt>
            <dd>Tworzona jest automatycznie przy zatwierdzeniu, kopiując dane
                katalogowe (nazwa, opis, dostawca, cena) ze źródła i startując
                z przekazanej ilości.</dd>

            <dt>Czy dwa transfery mogą „wyścignąć się" o ten sam stan?</dt>
            <dd>Nie — przy zatwierdzeniu zakładana jest blokada wiersza na
                części źródłowej, sprawdzany jest stan, a operacja jest
                wycofywana jeśli go nie wystarcza.</dd>

            <dt>Gdzie to widać w raportach?</dt>
            <dd>W <em>Raporty → Przegląd wydatków</em> obiekt źródłowy widzi
                wartość jako <strong>Transfery wychodzące</strong> (dodatni
                wydatek), obiekt docelowy widzi tę samą wartość jako
                <strong>Transfery przychodzące</strong> (ujemny wydatek /
                wpływ). Per-obiekt to ruch kosztu; organizacyjnie netto = 0.</dd>
        </dl>
    </div>
</div>
""",
    },
    "reports": {
        "title": "Raporty",
        "content": """\
<h4 class="mb-3"><i class="bi bi-graph-up me-2"></i>Raporty</h4>
<p class="text-muted mb-4">
    Moduł <em>Raporty</em> przekształca codzienne dane operacyjne (zlecenia,
    zużycie części, wpisy czasu, transfery) w analizę wydatków per obiekt
    z filtrami czasu i eksportem CSV.
</p>

<div class="alert alert-info">
    <i class="bi bi-info-circle me-2"></i>
    <strong>Kto widzi Raporty?</strong>
    Supervisorzy i administratorzy. Pozycja <em>Raporty</em> w nawigacji jest
    ukryta dla użytkowników, kontraktorów i techników.
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-card-list me-2"></i>Co jest dostępne</h5>
        <ul class="mb-0">
            <li><strong>Przegląd wydatków</strong> — zużyte części + koszt pracy + transfery przychodzące/wychodzące, per obiekt, dla dowolnego okresu. Eksport CSV.</li>
            <li><strong>Części do zamówienia</strong> (link z /parts/reorder) — niski stan per obiekt z sugestiami nadwyżki w innych lokalizacjach i kompensacją oczekujących transferów.</li>
            <li><strong>Rejestr transferów</strong> — wszystkie transfery z statusem (oczekujący/zakończony/anulowany) i wartością.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-calendar-range me-2"></i>Filtry czasu</h5>
        <p class="small text-muted">
            Każdy raport używa tego samego paska filtra na górze. Wybierz preset
            albo własny zakres, zaznacz „Porównaj" by zobaczyć poprzedni okres
            o tej samej długości obok.
        </p>
        <ul class="small mb-0">
            <li><strong>Dzisiaj</strong> / <strong>Ten tydzień</strong> (Pn–Nd) / <strong>Ten miesiąc</strong> / <strong>Ten kwartał</strong> / <strong>Od początku roku</strong></li>
            <li><strong>Poprzedni miesiąc</strong> / <strong>Poprzedni kwartał</strong></li>
            <li><strong>Własny</strong> — wybierz daty od / do ręcznie</li>
            <li><strong>Porównaj</strong> — dodaje kolumnę z tymi samymi metrykami dla poprzedniego okresu o tej samej długości</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-cash-stack me-2"></i>Jak liczone są wydatki</h5>
        <p class="small text-muted mb-3">
            Per obiekt, per okres, wzór wydatków:
        </p>
        <div class="bg-body-tertiary p-3 rounded mb-3">
            <code>net_spend = parts_consumed + labor + transfers_out − transfers_in</code>
        </div>
        <table class="table table-sm">
            <thead class="table-light">
                <tr><th>Składnik</th><th>Źródło</th></tr>
            </thead>
            <tbody>
                <tr><td>Zużyte części</td><td><code>PartUsage.quantity_used × unit_cost_at_use</code> dla zleceń obiektu, w okresie. Cofnięte zużycia są pomijane.</td></tr>
                <tr><td>Praca</td><td><code>(duration_minutes / 60) × rate_at_log</code> dla wpisów czasu obiektu, w okresie. Wpisy bez stawki = 0.</td></tr>
                <tr><td>Transfery wychodzące</td><td><code>quantity × unit_cost_at_transfer</code> dla zakończonych transferów <em>z</em> tego obiektu, w okresie.</td></tr>
                <tr><td>Transfery przychodzące</td><td>Ten sam wzór, transfery <em>do</em> tego obiektu — odejmowane (wpływ).</td></tr>
            </tbody>
        </table>
        <p class="small text-muted mb-0">
            Wszystkie wartości są <strong>zapisywane w momencie zdarzenia</strong>
            (zużycia, utworzenia wpisu, zgłoszenia transferu). Późniejsze zmiany
            stawek lub cen <em>nie</em> przepisują historii.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-clock-history me-2"></i>Konfiguracja kosztu pracy</h5>
        <p class="small">
            Koszt pracy pojawia się w raportach tylko dla wpisów czasu, które
            zapisały stawkę. Aby włączyć, administrator ustawia pole
            <strong>Stawka godzinowa</strong> w profilu użytkownika
            (<em>Admin → Użytkownicy → Edytuj</em>). Wszystkie <em>przyszłe</em>
            wpisy zapiszą stawkę w momencie utworzenia.
        </p>
        <p class="small mb-0">
            Historyczne wpisy (sprzed feature'u) pokazują „brak stawki" i liczą
            się jako 0. Brak backfillu — ustaw stawkę raz, a koszt pracy będzie
            poprawny od tego momentu.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-filetype-csv me-2"></i>Eksport CSV</h5>
        <p class="small mb-0">
            Kliknij <span class="badge bg-secondary">Eksport CSV</span> na dowolnym
            raporcie — ten sam filtr okresu zostanie zastosowany. CSV ma jeden
            wiersz per obiekt z kolumnami: <code>site_code, site_name, period,
            parts_consumed, labor, transfers_in, transfers_out, net_spend</code>.
            Otwórz w Excelu, Google Sheets lub dowolnym narzędziu księgowym.
        </p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-patch-question me-2"></i>Najczęstsze pytania</h5>
        <dl class="small mb-0">
            <dt>Dlaczego mój koszt pracy wydaje się niski?</dt>
            <dd>Najpewniej wpisy czasu powstały zanim użytkownik miał ustawioną
                stawkę. Nowe wpisy będą się liczyć, stare nie.</dd>

            <dt>Wartość „Transfery przychodzące" jest pokazana jako ujemna — dlaczego?</dt>
            <dd>Z perspektywy jednego obiektu otrzymanie transferu to wartość
                wpływająca — pomniejsza wydatek tego obiektu. Łączna suma
                organizacji się nie zmienia, bo obiekt źródłowy pokazuje tę
                samą kwotę jako Transfery wychodzące.</dd>

            <dt>Czy mogę zobaczyć wydatki dla wszystkich obiektów naraz?</dt>
            <dd>Administratorzy widzą wszystkie obiekty domyślnie. Supervisorzy
                widzą obiekty, do których mają dostęp. Suma w wierszu „Razem"
                u góry tabeli daje wartość zbiorczą.</dd>

            <dt>Jak porównać miesiące?</dt>
            <dd>Wybierz <em>Ten miesiąc</em> (lub <em>Poprzedni miesiąc</em>)
                i zaznacz <em>Porównaj</em>. Poprzedni okres o tej samej
                długości zostanie pokazany obok każdego składnika.</dd>
        </dl>
    </div>
</div>
""",
    },
}

# ── Translation keys for new help articles in sidebar ──────────────────
NEW_TRANSLATIONS = {
    ("ui.help.transfers", "ui"): {"en": "Transfers", "pl": "Transfery"},
    ("ui.help.reports", "ui"): {"en": "Reports", "pl": "Raporty"},
}


def main():
    app = create_app()
    with app.app_context():
        added_pages = 0
        updated_pages = 0
        for slug, payload in NEW_HELP_PAGES.items():
            existing = HelpContent.query.filter_by(
                page_slug=slug, language="pl",
            ).first()
            if existing is None:
                hc = HelpContent(
                    page_slug=slug, language="pl",
                    title=payload["title"], content=payload["content"],
                )
                db.session.add(hc)
                added_pages += 1
            elif (existing.title != payload["title"]
                  or existing.content != payload["content"]):
                existing.title = payload["title"]
                existing.content = payload["content"]
                updated_pages += 1

        added_t = 0
        updated_t = 0
        for (key, cat), langs in NEW_TRANSLATIONS.items():
            for lang, value in langs.items():
                existing = Translation.query.filter_by(
                    key=key, language=lang,
                ).first()
                if existing is None:
                    db.session.add(Translation(
                        key=key, category=cat, language=lang, value=value,
                    ))
                    added_t += 1
                elif existing.value != value:
                    existing.value = value
                    existing.category = cat
                    updated_t += 1

        db.session.commit()
        print(f"Help PL pages: {added_pages} added, {updated_pages} updated.")
        print(f"Sidebar i18n keys: {added_t} added, {updated_t} updated.")


if __name__ == "__main__":
    main()
