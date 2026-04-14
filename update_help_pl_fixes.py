#!/usr/bin/env python3
"""Apply targeted Polish help content fixes matching EN template fixes.

Fixes applied:
1. reporting   — asset/property is REQUIRED, mention searchable selector
2. property    — remove Tags mention, add Certifications section
3. getting-started — contractor "parts" in description, add Contractor accordion
4. faq         — email report: address book; report problem: Dashboard button;
                 Reporter→User
5. work-orders — add Cancelled status, stock validation note
6. admin       — Reporter→User+Contractor in roles table, add Email Templates,
                 Certifications, Contacts sections, fix Permissions path

Run:  python update_help_pl_fixes.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.help_content import HelpContent

app = create_app()


def patch_content(slug, old, new):
    """Replace old substring with new in the Polish help page content."""
    with app.app_context():
        page = HelpContent.query.filter_by(page_slug=slug, language="pl").first()
        if not page:
            print(f"  NOT FOUND  {slug} (pl) — skipping")
            return False
        if old not in page.content:
            print(f"  NOT FOUND  substring in {slug} (pl) — skipping")
            print(f"    Looking for: {old[:80]}...")
            return False
        page.content = page.content.replace(old, new, 1)
        db.session.commit()
        print(f"  PATCHED  {slug} (pl)")
        return True


def run():
    patched = 0

    with app.app_context():

        # ── 1. REPORTING — asset is required, searchable selector ──────────
        page = HelpContent.query.filter_by(page_slug="reporting", language="pl").first()
        if page:
            old = (
                '<li>Wypełnij tytuł (co się dzieje), opis (szczegóły) i priorytet</li>\n'
                '            <li>Opcjonalnie wybierz lokalizację i element majątku</li>'
            )
            new = (
                '<li>Wypełnij tytuł (co się dzieje), opis (szczegóły) i priorytet</li>\n'
                '            <li>Wybierz zasób/element majątku (wymagane) &mdash; zacznij pisać 3 lub więcej znaków, aby przeszukać listę, a następnie wybierz pasujący element</li>\n'
                '            <li>Opcjonalnie wybierz lokalizację</li>'
            )
            if old in page.content:
                page.content = page.content.replace(old, new, 1)
                db.session.commit()
                print("  PATCHED  reporting (pl) — asset required + searchable selector")
                patched += 1
            else:
                print("  SKIP     reporting (pl) — substring not found")
        else:
            print("  NOT FOUND  reporting (pl)")

        # ── 2. PROPERTY — remove Tags, add Certifications ─────────────────
        page = HelpContent.query.filter_by(page_slug="property", language="pl").first()
        if page:
            # Remove Tags line
            old_tags = '            <li><strong>Tagi</strong> &mdash; Stosuj dowolne tagi do elementów w celu elastycznego grupowania między kategoriami.</li>\n'
            if old_tags in page.content:
                page.content = page.content.replace(old_tags, '', 1)
                print("  PATCHED  property (pl) — removed Tags")
                patched += 1
            else:
                print("  SKIP     property (pl) Tags — substring not found")

            # Add Certifications section before Reorder Report
            cert_section = """\
<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-award me-2"></i>Certyfikaty</h5>
        <p class="text-muted small mb-3">Śledź certyfikaty, gwarancje i dokumenty zgodności powiązane z poszczególnymi zasobami.</p>

        <ul class="mb-0">
            <li><strong>Powiązane z zasobami</strong> &mdash; Każdy certyfikat jest przypisany do konkretnego elementu majątku. Wszystkie certyfikaty można przeglądać na stronie szczegółów zasobu.</li>
            <li><strong>Śledzenie dat ważności</strong> &mdash; Certyfikaty mają daty ważności. Wygasłe lub zbliżające się do wygaśnięcia certyfikaty są oznaczane w Raporcie wygasania.</li>
            <li><strong>Przesyłanie dokumentów</strong> &mdash; Dołączaj zeskanowane certyfikaty lub dokumenty potwierdzające bezpośrednio do rekordu certyfikatu.</li>
            <li><strong>Rodzaje</strong> &mdash; Typowe przykłady to świadectwa bezpieczeństwa elektrycznego, certyfikaty gazowe, protokoły PAT, dokumenty ubezpieczeniowe i karty gwarancyjne.</li>
        </ul>
    </div>
</div>

"""
            old_reorder = '<div class="card shadow-sm mb-4">\n    <div class="card-body">\n        <h5 class="card-title"><i class="bi bi-cart-check me-2"></i>Raport zamówień</h5>'
            if old_reorder in page.content:
                page.content = page.content.replace(old_reorder, cert_section + old_reorder, 1)
                print("  PATCHED  property (pl) — added Certifications section")
                patched += 1
            else:
                print("  SKIP     property (pl) Certifications — anchor not found")

            db.session.commit()

        # ── 3. GETTING-STARTED — contractor desc + accordion ──────────────
        page = HelpContent.query.filter_by(page_slug="getting-started", language="pl").first()
        if page:
            # Fix contractor description
            old_contr = 'Rejestruj czas i notatki.'
            new_contr = 'Rejestruj czas, notatki i części.'
            if old_contr in page.content:
                page.content = page.content.replace(old_contr, new_contr, 1)
                print("  PATCHED  getting-started (pl) — contractor description")
                patched += 1
            else:
                print("  SKIP     getting-started (pl) contractor desc — not found")

            # Add Contractor accordion between User and Technician
            contractor_accordion = """\
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button"
                            data-bs-toggle="collapse" data-bs-target="#stepsContractor">
                        <span class="badge bg-warning text-dark me-2">Wykonawca</span> Jestem Wykonawcą
                    </button>
                </h2>
                <div id="stepsContractor" class="accordion-collapse collapse" data-bs-parent="#firstSteps">
                    <div class="accordion-body">
                        <ol class="mb-0">
                            <li>Sprawdź <strong>Pulpit</strong>, aby zobaczyć przydzielone zlecenia pracy.</li>
                            <li>Otwórz zlecenie, aby sprawdzić, co trzeba zrobić.</li>
                            <li>Kliknij <strong>Rozpocznij pracę</strong>, gdy zaczynasz.</li>
                            <li>Rejestruj czas, notatki i zużyte części.</li>
                            <li>Kliknij <strong>Oznacz jako ukończone</strong>, gdy skończysz.</li>
                        </ol>
                    </div>
                </div>
            </div>

"""
            old_tech_start = '            <div class="accordion-item">\n                <h2 class="accordion-header">\n                    <button class="accordion-button collapsed" type="button"\n                            data-bs-toggle="collapse" data-bs-target="#stepsTech">'
            if old_tech_start in page.content and '#stepsContractor' not in page.content:
                page.content = page.content.replace(old_tech_start, contractor_accordion + old_tech_start, 1)
                print("  PATCHED  getting-started (pl) — added Contractor accordion")
                patched += 1
            else:
                if '#stepsContractor' in page.content:
                    print("  SKIP     getting-started (pl) Contractor accordion — already exists")
                else:
                    print("  SKIP     getting-started (pl) Contractor accordion — anchor not found")

            db.session.commit()

        # ── 4. FAQ — email report, report problem, Reporter→User ──────────
        page = HelpContent.query.filter_by(page_slug="faq", language="pl").first()
        if page:
            # Email report: address book
            old_email = 'Podaj adres e-mail odbiorcy i kliknij Wyślij.'
            new_email = 'Wybierz jednego lub więcej odbiorców z książki adresowej i kliknij Wyślij.'
            if old_email in page.content:
                page.content = page.content.replace(old_email, new_email, 1)
                print("  PATCHED  faq (pl) — email report: address book")
                patched += 1
            else:
                print("  SKIP     faq (pl) email report — not found")

            # Report problem: Dashboard button
            old_report = 'wysłać zgłoszenie przez stronę Zgłoszenia'
            new_report = 'użyć przycisku <strong>Zgłoś problem</strong> na Pulpicie'
            if old_report in page.content:
                page.content = page.content.replace(old_report, new_report, 1)
                print("  PATCHED  faq (pl) — report problem: Dashboard button")
                patched += 1
            else:
                print("  SKIP     faq (pl) report problem — not found")

            # Reporter→User in add user FAQ
            old_role = 'Technik lub Zgłaszający'
            new_role = 'Technik lub Użytkownik'
            if old_role in page.content:
                page.content = page.content.replace(old_role, new_role, 1)
                print("  PATCHED  faq (pl) — Reporter→User")
                patched += 1
            else:
                print("  SKIP     faq (pl) Reporter→User — not found")

            db.session.commit()

        # ── 5. WORK-ORDERS — Cancelled status + stock validation ──────────
        page = HelpContent.query.filter_by(page_slug="work-orders", language="pl").first()
        if page:
            # Add Cancelled to lifecycle diagram
            old_hold = ('            <span class="text-muted small">Odgałęzienie od W realizacji:</span>\n'
                        '            <span class="badge bg-warning text-dark fs-6 ms-2">Wstrzymane</span>')
            new_hold = ('            <span class="text-muted small">Odgałęzienie od W realizacji:</span>\n'
                        '            <span class="badge bg-warning text-dark fs-6 ms-2">Wstrzymane</span>\n'
                        '            <span class="text-muted small ms-3">Można anulować na każdym etapie:</span>\n'
                        '            <span class="badge bg-danger fs-6 ms-2">Anulowane</span>')
            if old_hold in page.content:
                page.content = page.content.replace(old_hold, new_hold, 1)
                print("  PATCHED  work-orders (pl) — Cancelled in lifecycle diagram")
                patched += 1
            else:
                print("  SKIP     work-orders (pl) lifecycle — not found")

            # Add Cancelled to status table
            old_closed_row = ('                    <tr>\n'
                              '                        <td><span class="badge bg-dark">Zamknięte</span></td>\n'
                              '                        <td>Kierownik sprawdził i zamknął zlecenie pracy. Brak dalszych zmian.</td>\n'
                              '                    </tr>\n'
                              '                </tbody>')
            new_closed_row = ('                    <tr>\n'
                              '                        <td><span class="badge bg-dark">Zamknięte</span></td>\n'
                              '                        <td>Kierownik sprawdził i zamknął zlecenie pracy. Brak dalszych zmian.</td>\n'
                              '                    </tr>\n'
                              '                    <tr>\n'
                              '                        <td><span class="badge bg-danger">Anulowane</span></td>\n'
                              '                        <td>Zlecenie pracy zostało anulowane i nie będzie realizowane. Można zastosować na każdym etapie.</td>\n'
                              '                    </tr>\n'
                              '                </tbody>')
            if old_closed_row in page.content:
                page.content = page.content.replace(old_closed_row, new_closed_row, 1)
                print("  PATCHED  work-orders (pl) — Cancelled in status table")
                patched += 1
            else:
                print("  SKIP     work-orders (pl) status table — not found")

            # Add stock validation note before Part Usage Reversal
            old_reversal = '        <h6>Wycofanie zużycia części</h6>'
            new_reversal = ('        <div class="alert alert-info mb-3">\n'
                            '            <i class="bi bi-info-circle me-1"></i>\n'
                            '            <strong>Walidacja stanów magazynowych:</strong> System uniemożliwia dodanie części, gdy stan magazynowy jest niewystarczający. Jeśli spróbujesz użyć więcej niż dostępna ilość, wpis zostanie odrzucony. Sprawdź stany magazynowe lub poproś kierownika o uzupełnienie zapasów.\n'
                            '        </div>\n\n'
                            '        <h6>Wycofanie zużycia części</h6>')
            if old_reversal in page.content:
                page.content = page.content.replace(old_reversal, new_reversal, 1)
                print("  PATCHED  work-orders (pl) — stock validation note")
                patched += 1
            else:
                print("  SKIP     work-orders (pl) stock validation — not found")

            db.session.commit()

        # ── 6. ADMIN — Reporter→User+Contractor, new sections, permissions fix ─
        page = HelpContent.query.filter_by(page_slug="admin", language="pl").first()
        if page:
            # Change Zgłaszający to Użytkownik and add Wykonawca row
            old_reporter = ('                    <tr>\n'
                            '                        <td><strong>Zgłaszający</strong></td>\n'
                            '                        <td>Może wysyłać zgłoszenia konserwacyjne i śledzić ich postęp.</td>\n'
                            '                    </tr>')
            new_reporter = ('                    <tr>\n'
                            '                        <td><strong>Wykonawca</strong></td>\n'
                            '                        <td>Może przeglądać i realizować przydzielone zlecenia pracy, rejestrować czas, notatki i części.</td>\n'
                            '                    </tr>\n'
                            '                    <tr>\n'
                            '                        <td><strong>Użytkownik</strong></td>\n'
                            '                        <td>Może wysyłać zgłoszenia konserwacyjne i śledzić ich postęp.</td>\n'
                            '                    </tr>')
            if old_reporter in page.content:
                page.content = page.content.replace(old_reporter, new_reporter, 1)
                print("  PATCHED  admin (pl) — Reporter→User+Contractor in roles table")
                patched += 1
            else:
                print("  SKIP     admin (pl) roles table — not found")

            # Add Email Templates, Certifications, Contacts before Permissions Matrix
            new_sections = """\
<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-envelope-paper me-2"></i>Szablony e-mail</h5>
        <p class="text-muted small mb-3">Dostosuj powiadomienia e-mail wysyłane przez system dla różnych zdarzeń.</p>

        <ul class="mb-0">
            <li><strong>Typy szablonów</strong> &mdash; Szablony istnieją dla kluczowych zdarzeń, takich jak powiadomienia o nowych zgłoszeniach, przydzielenie zleceń pracy, powiadomienia o ukończeniu i wysyłanie raportów.</li>
            <li><strong>Dostosowanie treści</strong> &mdash; Przejdź do <strong>Admin &rarr; Szablony e-mail</strong>, aby edytować temat i treść każdego szablonu.</li>
            <li><strong>Zmienne</strong> &mdash; Używaj zmiennych (np. <code>{{work_order_number}}</code>, <code>{{asset_name}}</code>, <code>{{assigned_to}}</code>) do wstawiania dynamicznych danych do treści wiadomości.</li>
            <li><strong>Per obiekt</strong> &mdash; Szablony mogą być konfigurowane per obiekt, dzięki czemu różne lokalizacje mogą mieć dostosowane wiadomości.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-award me-2"></i>Certyfikaty</h5>
        <p class="text-muted small mb-3">Zarządzaj certyfikatami zgodności i dokumentami gwarancyjnymi powiązanymi z elementami majątku.</p>

        <ul class="mb-0">
            <li><strong>Tworzenie certyfikatów</strong> &mdash; Na stronie szczegółów elementu majątku dodaj certyfikaty z typem, datą wystawienia, datą ważności i opcjonalnym załącznikiem dokumentu.</li>
            <li><strong>Monitorowanie ważności</strong> &mdash; Certyfikaty zbliżające się do lub po dacie ważności są wyświetlane w <strong>Raporcie wygasania</strong> w sekcji <strong>Raporty</strong>.</li>
            <li><strong>Przechowywanie dokumentów</strong> &mdash; Przesyłaj zeskanowane certyfikaty (PDF, obrazy) bezpośrednio do każdego rekordu certyfikatu w celu łatwego dostępu.</li>
            <li><strong>Ścieżka audytu</strong> &mdash; System rejestruje, kiedy certyfikaty zostały utworzone, zaktualizowane lub odnowione, utrzymując pełną historię zgodności per zasób.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-person-rolodex me-2"></i>Kontakty / Książka adresowa</h5>
        <p class="text-muted small mb-3">Prowadź centralną książkę adresową kontaktów używanych do wysyłania raportów i powiadomień e-mailem.</p>

        <ul class="mb-0">
            <li><strong>Dodawanie kontaktów</strong> &mdash; Przejdź do <strong>Admin &rarr; Książka adresowa</strong>, aby dodać nazwy kontaktów i adresy e-mail.</li>
            <li><strong>Używane do wysyłania raportów</strong> &mdash; Przy wysyłaniu raportu e-mailem odbiorcy są wybierani z książki adresowej zamiast ręcznego wpisywania.</li>
            <li><strong>Kategoryzacja kontaktów</strong> &mdash; Organizuj kontakty według typu (np. personel wewnętrzny, dostawcy, wykonawcy, organy kontrolne) dla łatwiejszego wyboru.</li>
            <li><strong>Kontakty per obiekt</strong> &mdash; Kontakty mogą być przypisane do konkretnych obiektów, dzięki czemu przy wysyłaniu raportów dla danego obiektu wyświetlani są tylko odpowiedni odbiorcy.</li>
        </ul>
    </div>
</div>

"""
            old_permissions = '<div class="card shadow-sm mb-4">\n    <div class="card-body">\n        <h5 class="card-title"><i class="bi bi-shield-check me-2"></i>Matryca uprawnień</h5>'
            if old_permissions in page.content:
                page.content = page.content.replace(old_permissions, new_sections + old_permissions, 1)
                print("  PATCHED  admin (pl) — added Email Templates, Certifications, Contacts sections")
                patched += 1
            else:
                print("  SKIP     admin (pl) new sections — anchor not found")

            # Fix permissions path
            old_perm = 'Przejdź do <strong>Admin &rarr; Uprawnienia</strong> do zarządzania nadpisaniami.'
            new_perm = 'Zarządzaj nadpisaniami ze strony edycji użytkownika: <strong>Admin &rarr; Użytkownicy &rarr; (wybierz użytkownika) &rarr; Uprawnienia</strong>.'
            if old_perm in page.content:
                page.content = page.content.replace(old_perm, new_perm, 1)
                print("  PATCHED  admin (pl) — permissions path fix")
                patched += 1
            else:
                print("  SKIP     admin (pl) permissions path — not found")

            db.session.commit()

    print(f"\nDone. Total patches applied: {patched}")


if __name__ == "__main__":
    run()
