#!/usr/bin/env python3
"""Seed Polish help content for CMMS.

Inserts HelpContent records for all help pages in Polish (pl).
Idempotent — skips pages that already exist.

Run:  python seed_help_pl.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.help_content import HelpContent

app = create_app()

# ═══════════════════════════════════════════════════════════════════════════
#  Polish help pages — {slug: (title, html_content)}
# ═══════════════════════════════════════════════════════════════════════════

HELP_PAGES_PL = {

    # ──────────────────────────────────────────────────────────────────────
    #  INDEX — Help Centre landing page
    # ──────────────────────────────────────────────────────────────────────
    "index": (
        "Centrum Pomocy",
        """\
<p class="text-muted mb-4">Witamy w Centrum Pomocy CMMS. Znajdziesz tu przewodniki, instrukcje i odpowiedzi, które pomogą Ci w pełni korzystać z systemu zarządzania utrzymaniem ruchu.</p>

<h5 class="mb-3">Czego potrzebujesz?</h5>
<div class="row g-3 mb-4">
    <div class="col-md-6 col-lg-3">
        <a href="/help/reporting" class="card h-100 text-decoration-none shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-person fs-2 text-primary d-block mb-2"></i>
                <h6 class="card-title mb-1">Chcę zgłosić problem</h6>
            </div>
        </a>
    </div>
    <div class="col-md-6 col-lg-3">
        <a href="/help/work-orders" class="card h-100 text-decoration-none shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-clipboard fs-2 text-success d-block mb-2"></i>
                <h6 class="card-title mb-1">Mam przydzieloną pracę</h6>
                <small class="text-muted">Wymagane logowanie</small>
            </div>
        </a>
    </div>
    <div class="col-md-6 col-lg-3">
        <a href="/help/work-orders" class="card h-100 text-decoration-none shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-funnel fs-2 text-warning d-block mb-2"></i>
                <h6 class="card-title mb-1">Zarządzam kolejką</h6>
                <small class="text-muted">Wymagane logowanie</small>
            </div>
        </a>
    </div>
    <div class="col-md-6 col-lg-3">
        <a href="/help/admin" class="card h-100 text-decoration-none shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-shield fs-2 text-danger d-block mb-2"></i>
                <h6 class="card-title mb-1">Zarządzam systemem</h6>
                <small class="text-muted">Tylko administrator</small>
            </div>
        </a>
    </div>
</div>

<h5 class="mb-3">Przeglądaj tematy</h5>
<div class="row g-3 mb-4">
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-rocket-takeoff me-2"></i>Rozpoczęcie pracy</h6>
                <p class="text-muted small mb-2">Nowy w CMMS? Zacznij tutaj.</p>
                <a href="/help/getting-started" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-exclamation-triangle me-2"></i>Zgłaszanie problemu</h6>
                <p class="text-muted small mb-2">Jak zgłosić usterkę za pomocą kodu QR lub formularza.</p>
                <a href="/help/reporting" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-list-check me-2"></i>Zgłoszenia</h6>
                <p class="text-muted small mb-2">Śledź swoje zgłoszenia i poznaj statusy.</p>
                <a href="/help/requests" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-clipboard-check me-2"></i>Zlecenia pracy</h6>
                <p class="text-muted small mb-2">Realizuj, śledź i zamykaj prace konserwacyjne.</p>
                <a href="/help/work-orders" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-buildings me-2"></i>Majątek i części</h6>
                <p class="text-muted small mb-2">Zarządzaj urządzeniami, magazynem części i kompatybilnością.</p>
                <a href="/help/property" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card shadow-sm h-100">
            <div class="card-body">
                <h6><i class="bi bi-patch-question me-2"></i>FAQ</h6>
                <p class="text-muted small mb-2">Najczęściej zadawane pytania.</p>
                <a href="/help/faq" class="stretched-link small">Czytaj więcej <i class="bi bi-arrow-right"></i></a>
            </div>
        </div>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  GETTING STARTED
    # ──────────────────────────────────────────────────────────────────────
    "getting-started": (
        "Rozpoczęcie pracy",
        """\
<p class="text-muted mb-4">Ten przewodnik przeprowadzi Cię przez podstawy korzystania z CMMS &mdash; niezależnie od tego, czy zgłaszasz problem, wykonujesz prace konserwacyjne, czy zarządzasz systemem.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-diagram-3 me-2"></i>Czym jest CMMS?</h5>
        <p>CMMS (ang. Computerised Maintenance Management System) to system do śledzenia napraw, przeglądów i konserwacji zapobiegawczej w jednym lub wielu obiektach. Każde zadanie przebiega według jasnego cyklu:</p>
        <div class="d-flex flex-wrap align-items-center gap-2 my-3 justify-content-center">
            <span class="badge bg-primary fs-6 py-2 px-3">Zgłoś problem</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-info text-dark fs-6 py-2 px-3">Weryfikacja</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-warning text-dark fs-6 py-2 px-3">Zlecenie pracy</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-success fs-6 py-2 px-3">Ukończone</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-secondary fs-6 py-2 px-3">Historia zasobu</span>
        </div>
        <p class="mb-0">Wszystko, co wprowadzisz, jest zachowywane &mdash; zdjęcia, notatki, zużyte części, czas pracy &mdash; tworząc kompletną historię konserwacji każdego zasobu.</p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-people me-2"></i>Twoja rola</h5>
        <p>To, co możesz zobaczyć i zrobić, zależy od Twojej roli:</p>
        <div class="table-responsive">
            <table class="table table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th style="width: 140px;">Rola</th>
                        <th>Co możesz robić</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge bg-secondary">Użytkownik</span></td>
                        <td>Zgłaszaj problemy, dodawaj zdjęcia, śledź własne zgłoszenia.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-warning text-dark">Wykonawca</span></td>
                        <td>Przeglądaj i realizuj przydzielone zlecenia pracy. Rejestruj czas i notatki.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">Technik</span></td>
                        <td>Wszystko, co Wykonawca, a także: przeglądanie wszystkich zleceń pracy w obiekcie, informacje o zasobach i ich historia, rejestrowanie zużytych części.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">Kierownik</span></td>
                        <td>Wszystko, co Technik, a także: weryfikacja zgłoszeń, tworzenie zleceń pracy, przydzielanie pracy, zarządzanie zasobami, lokalizacjami i magazynem części, zamykanie zleceń.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-danger">Administrator</span></td>
                        <td>Pełny dostęp. Wszystko, co Kierownik, a także zarządzanie użytkownikami, zespołami i obiektami.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-signpost-split me-2"></i>Pierwsze kroki wg roli</h5>
        <p>Znajdź swoją rolę poniżej, aby zobaczyć, od czego zacząć.</p>

        <div class="accordion" id="firstSteps">
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button" type="button"
                            data-bs-toggle="collapse" data-bs-target="#stepsUser">
                        <span class="badge bg-secondary me-2">Użytkownik</span> Jestem Użytkownikiem / Pracownikiem
                    </button>
                </h2>
                <div id="stepsUser" class="accordion-collapse collapse show" data-bs-parent="#firstSteps">
                    <div class="accordion-body">
                        <ol class="mb-0">
                            <li>Przejdź do <strong>Pulpitu</strong>.</li>
                            <li>Kliknij <strong>&bdquo;Zgłoś problem&rdquo;</strong>.</li>
                            <li>Opisz, co się dzieje &mdash; opisz usterkę, wybierz lokalizację i dołącz zdjęcie, jeśli możesz.</li>
                            <li>Śledź postępy w sekcji <strong>&bdquo;Moje zgłoszenia&rdquo;</strong>.</li>
                        </ol>
                    </div>
                </div>
            </div>

            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button"
                            data-bs-toggle="collapse" data-bs-target="#stepsTech">
                        <span class="badge bg-success me-2">Technik</span> Jestem Technikiem
                    </button>
                </h2>
                <div id="stepsTech" class="accordion-collapse collapse" data-bs-parent="#firstSteps">
                    <div class="accordion-body">
                        <ol class="mb-0">
                            <li>Sprawdź <strong>Pulpit</strong>, aby zobaczyć przydzielone zlecenia pracy.</li>
                            <li>Otwórz zlecenie, aby sprawdzić, co trzeba zrobić.</li>
                            <li>Kliknij <strong>Rozpocznij pracę</strong>, gdy zaczynasz.</li>
                            <li>Wykonaj listę kontrolną, zarejestruj czas i zużyte części.</li>
                            <li>Kliknij <strong>Oznacz jako ukończone</strong>, gdy skończysz.</li>
                        </ol>
                    </div>
                </div>
            </div>

            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button"
                            data-bs-toggle="collapse" data-bs-target="#stepsSupervisor">
                        <span class="badge bg-primary me-2">Kierownik</span> Jestem Kierownikiem
                    </button>
                </h2>
                <div id="stepsSupervisor" class="accordion-collapse collapse" data-bs-parent="#firstSteps">
                    <div class="accordion-body">
                        <ol class="mb-0">
                            <li>Sprawdź <strong>Kolejkę weryfikacji</strong> pod kątem nowych zgłoszeń.</li>
                            <li><strong>Potwierdź</strong> zasadne zgłoszenia.</li>
                            <li><strong>Przekształć w zlecenia pracy</strong> i dodaj listy kontrolne, priorytet oraz terminy.</li>
                            <li><strong>Przydziel</strong> zlecenia technikom lub wykonawcom.</li>
                            <li><strong>Sprawdź i zamknij</strong> ukończone zlecenia pracy.</li>
                        </ol>
                    </div>
                </div>
            </div>

            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button"
                            data-bs-toggle="collapse" data-bs-target="#stepsAdmin">
                        <span class="badge bg-danger me-2">Admin</span> Jestem Administratorem
                    </button>
                </h2>
                <div id="stepsAdmin" class="accordion-collapse collapse" data-bs-parent="#firstSteps">
                    <div class="accordion-body">
                        <ol class="mb-0">
                            <li>Skonfiguruj <strong>Obiekty</strong> &mdash; dodaj lokalizacje, którymi zarządza Twoja organizacja.</li>
                            <li>Utwórz <strong>Zespoły</strong> &mdash; wewnętrzne zespoły konserwacyjne i zewnętrznych wykonawców.</li>
                            <li>Dodaj <strong>Użytkowników</strong> i przypisz role oraz obiekty do każdej osoby.</li>
                            <li>Skonfiguruj <strong>Ustawienia</strong> &mdash; lokalizacje, majątek, magazyn części i kategorie.</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-life-preserver me-2"></i>Potrzebujesz więcej pomocy?</h5>
        <p class="mb-0">Sprawdź <a href="/help/faq">Najczęściej zadawane pytania</a>, aby znaleźć odpowiedzi na popularne pytania, lub przeglądaj inne tematy w pasku bocznym.</p>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  REPORTING A PROBLEM
    # ──────────────────────────────────────────────────────────────────────
    "reporting": (
        "Zgłaszanie problemu",
        """\
<p class="text-muted mb-4">Każdy może zgłosić problem konserwacyjny. Są na to dwa sposoby: zeskanuj kod QR na urządzeniu lub zaloguj się i wypełnij formularz ręcznie.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-qr-code me-2"></i>Skanowanie kodu QR</h5>
        <ol class="mb-3">
            <li>Znajdź naklejkę z kodem QR na urządzeniu (zwykle mała etykieta)</li>
            <li>Otwórz aparat w telefonie i skieruj go na kod QR</li>
            <li>Kliknij link, który się pojawi &mdash; otworzy formularz zgłoszenia</li>
            <li>Urządzenie zostanie automatycznie zidentyfikowane &mdash; nie musisz go szukać</li>
            <li>Opisz problem i wyślij zgłoszenie</li>
        </ol>
        <div class="text-muted small">
            <i class="bi bi-info-circle me-1"></i>
            Jeśli zgłoszenia anonimowe są włączone, możesz je wysłać bez logowania. W przeciwnym razie system poprosi o zalogowanie.
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-pencil-square me-2"></i>Ręczne zgłaszanie</h5>
        <ol class="mb-0">
            <li>Zaloguj się do CMMS</li>
            <li>Kliknij <strong>&bdquo;Zgłoś problem&rdquo;</strong> na pulpicie</li>
            <li>Wypełnij tytuł (co się dzieje), opis (szczegóły) i priorytet</li>
            <li>Opcjonalnie wybierz lokalizację i element majątku</li>
            <li>Dołącz zdjęcie, jeśli to możliwe</li>
            <li>Kliknij <strong>&bdquo;Wyślij zgłoszenie&rdquo;</strong></li>
        </ol>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-flag me-2"></i>Poziomy priorytetu</h5>
        <div class="table-responsive">
            <table class="table table-bordered mb-3">
                <thead class="table-light">
                    <tr>
                        <th style="width: 140px;">Priorytet</th>
                        <th>Kiedy stosować</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge bg-success">Niepilne</span></td>
                        <td>Problemy kosmetyczne, drobne niedogodności. Brak wpływu na działalność.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">Normalne</span></td>
                        <td>Powinno zostać rozwiązane w ciągu kilku dni. Działalność może być kontynuowana.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-warning text-dark">Pilne</span></td>
                        <td>Znaczący wpływ na pracę. Może istnieć obejście, ale wymaga szybkiej reakcji.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-danger">Awaria</span></td>
                        <td>Praca wstrzymana lub zagrożenie bezpieczeństwa. Wymaga natychmiastowego działania.</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="text-muted small">
            <i class="bi bi-lightbulb me-1"></i>
            <strong>Wskazówka:</strong> W razie wątpliwości wybierz &bdquo;Normalne&rdquo;. Kierownik dostosuje priorytet w razie potrzeby.
        </div>
    </div>
</div>

<div class="card border-info mb-4">
    <div class="card-body">
        <h5 class="card-title text-info"><i class="bi bi-lightbulb me-2"></i>Wskazówki dotyczące dobrego zgłoszenia</h5>
        <ul class="mb-0">
            <li>Opisz konkretnie, co widzisz, słyszysz lub czujesz</li>
            <li>Podaj, kiedy problem się zaczął i czy się pogarsza</li>
            <li>Podaj lokalizację, jeśli ją znasz</li>
            <li>Dołącz zdjęcie &mdash; jeden obraz jest wart tysiąca słów</li>
            <li>Nie martw się terminologią techniczną &mdash; opisz problem własnymi słowami</li>
        </ul>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  REQUESTS
    # ──────────────────────────────────────────────────────────────────────
    "requests": (
        "Zgłoszenia",
        """\
<p class="text-muted mb-4">Zgłoszenie to raport o problemie. Po wysłaniu przechodzi przez cykl życia, w miarę jak zespół konserwacyjny je analizuje i rozwiązuje.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-arrow-repeat me-2"></i>Cykl życia zgłoszenia</h5>

        <div class="d-flex flex-wrap align-items-center gap-2 mb-4">
            <span class="badge bg-primary">Nowe</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge" style="background-color: #6f42c1;">Potwierdzone</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-warning text-dark">W realizacji</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-success">Rozwiązane</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-secondary">Zamknięte</span>
        </div>

        <div class="table-responsive">
            <table class="table table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th style="width: 160px;">Status</th>
                        <th>Znaczenie</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge bg-primary">Nowe</span></td>
                        <td>Właśnie wysłane, oczekuje na weryfikację</td>
                    </tr>
                    <tr>
                        <td><span class="badge" style="background-color: #6f42c1;">Potwierdzone</span></td>
                        <td>Kierownik potwierdził, że zgłoszenie jest zasadne</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-warning text-dark">W realizacji</span></td>
                        <td>Utworzono zlecenie pracy</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">Rozwiązane</span></td>
                        <td>Prace zakończone, problem naprawiony</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-secondary">Zamknięte</span></td>
                        <td>Całkowicie zamknięte, brak dalszych działań</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-danger">Anulowane</span></td>
                        <td>Zgłoszenie zostało anulowane</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-search me-2"></i>Śledzenie zgłoszeń</h5>
        <p class="mb-2">Po wysłaniu możesz śledzić swoje zgłoszenie z Pulpitu lub strony Zgłoszenia.</p>
        <p class="mb-0">Kliknij dowolne zgłoszenie, aby zobaczyć pełne szczegóły, oś czasu aktywności i powiązane zlecenie pracy.</p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-clock-history me-2"></i>Oś czasu aktywności</h5>
        <p>Każde zgłoszenie ma oś czasu aktywności pokazującą, co się wydarzyło i kiedy:</p>
        <ul class="list-group list-group-flush mb-0">
            <li class="list-group-item ps-0">
                <i class="bi bi-circle-fill text-primary me-2" style="font-size: 0.5rem; vertical-align: middle;"></i>
                <strong>Kasia</strong> wysłała to zgłoszenie &mdash; <span class="text-muted">3 kwi 10:15</span>
            </li>
            <li class="list-group-item ps-0">
                <i class="bi bi-circle-fill text-primary me-2" style="font-size: 0.5rem; vertical-align: middle;"></i>
                <strong>Jan</strong> potwierdził zgłoszenie &mdash; <span class="text-muted">3 kwi 14:30</span>
            </li>
            <li class="list-group-item ps-0">
                <i class="bi bi-circle-fill text-primary me-2" style="font-size: 0.5rem; vertical-align: middle;"></i>
                <strong>Jan</strong> przekształcił w zlecenie pracy <code>WO-20260403-001</code> &mdash; <span class="text-muted">4 kwi 09:00</span>
            </li>
            <li class="list-group-item ps-0">
                <i class="bi bi-circle-fill text-info me-2" style="font-size: 0.5rem; vertical-align: middle;"></i>
                <strong>Kasia:</strong> &bdquo;Pogarsza się, teraz przecieka&rdquo; &mdash; <span class="text-muted">4 kwi 11:20</span>
            </li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-chat-dots me-2"></i>Dodawanie komentarzy</h5>
        <p class="mb-2">Możesz dodawać komentarze do swojego zgłoszenia w dowolnym momencie (chyba że jest zamknięte lub anulowane).</p>
        <p class="mb-2">Komentarze służą do przekazywania aktualizacji, wyjaśniania szczegółów lub zadawania pytań.</p>
        <p class="mb-0">Kierownicy również mogą komentować &mdash; sprawdzaj, czy pojawiły się odpowiedzi.</p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-paperclip me-2"></i>Przesyłanie plików</h5>
        <p class="mb-2">Do zgłoszenia możesz przesyłać zdjęcia i dokumenty.</p>
        <p class="mb-2">Obsługiwane formaty: JPEG, PNG, WebP, GIF, PDF, Word, Excel.</p>
        <p class="mb-0">Zdjęcia pomagają technikom zrozumieć problem przed przybyciem na miejsce.</p>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  WORK ORDERS
    # ──────────────────────────────────────────────────────────────────────
    "work-orders": (
        "Zlecenia pracy",
        """\
<p class="text-muted mb-4">Zlecenie pracy to kontrolowane zadanie konserwacyjne. Śledzi, co trzeba zrobić, kto to robi, jakie części i czas zostały zużyte oraz co zostało stwierdzone.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-arrow-repeat me-2"></i>Cykl życia zlecenia pracy</h5>
        <p class="text-muted small mb-3">Każde zlecenie pracy przechodzi przez szereg statusów od utworzenia do zamknięcia.</p>

        <div class="d-flex flex-wrap align-items-center gap-2 mb-4 justify-content-center">
            <span class="badge bg-secondary fs-6">Otwarte</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-info fs-6">Przydzielone</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-primary fs-6">W realizacji</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-success fs-6">Ukończone</span>
            <i class="bi bi-arrow-right text-muted"></i>
            <span class="badge bg-dark fs-6">Zamknięte</span>
        </div>
        <div class="text-center mb-4">
            <span class="text-muted small">Odgałęzienie od W realizacji:</span>
            <span class="badge bg-warning text-dark fs-6 ms-2">Wstrzymane</span>
        </div>

        <div class="table-responsive">
            <table class="table table-sm table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Status</th>
                        <th>Opis</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge bg-secondary">Otwarte</span></td>
                        <td>Zlecenie pracy zostało utworzone, ale jeszcze nie przydzielone technikowi.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-info">Przydzielone</span></td>
                        <td>Technik został przydzielony, praca oczekuje na rozpoczęcie.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">W realizacji</span></td>
                        <td>Technik rozpoczął pracę nad zadaniem.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-warning text-dark">Wstrzymane</span></td>
                        <td>Praca jest wstrzymana &mdash; zazwyczaj w oczekiwaniu na części, informacje lub dostęp.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">Ukończone</span></td>
                        <td>Technik zakończył pracę i zarejestrował swoje ustalenia.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-dark">Zamknięte</span></td>
                        <td>Kierownik sprawdził i zamknął zlecenie pracy. Brak dalszych zmian.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-tools me-2"></i>Realizacja zlecenia pracy</h5>
        <p class="text-muted small mb-3">Instrukcja krok po kroku dla techników wykonujących prace konserwacyjne.</p>

        <ol class="list-group list-group-numbered list-group-flush">
            <li class="list-group-item">
                <strong>Sprawdź przydzielone zadania</strong> &mdash; Przejdź do Pulpitu i zobacz sekcję &bdquo;Moje przydzielone zlecenia&rdquo;.
            </li>
            <li class="list-group-item">
                <strong>Otwórz zlecenie pracy</strong> &mdash; Kliknij zlecenie, aby zobaczyć szczegóły, instrukcje i załączone pliki.
            </li>
            <li class="list-group-item">
                <strong>Rozpocznij pracę</strong> &mdash; Kliknij przycisk <span class="badge bg-primary">Rozpocznij pracę</span>, aby zmienić status na W realizacji.
            </li>
            <li class="list-group-item">
                <strong>Realizuj listę kontrolną</strong> &mdash; Wykonaj każde zadanie z listy i odhaczaj kolejne pozycje.
            </li>
            <li class="list-group-item">
                <strong>Zarejestruj zużyte części</strong> &mdash; Wybierz każdą część z listy rozwijanej i podaj zużytą ilość. Stan magazynowy jest automatycznie aktualizowany.
            </li>
            <li class="list-group-item">
                <strong>Zarejestruj czas pracy</strong> &mdash; Podaj liczbę przepracowanych minut i dodaj notatki o wykonanych czynnościach.
            </li>
            <li class="list-group-item">
                <strong>Prześlij zdjęcia</strong> &mdash; Zrób zdjęcia wykonanej pracy i prześlij je jako dowód.
            </li>
            <li class="list-group-item">
                <strong>Ukończ zlecenie pracy</strong> &mdash; Kliknij <span class="badge bg-success">Ukończ</span> i opisz, co stwierdzono i co zostało zrobione.
            </li>
        </ol>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-tags me-2"></i>Typy zleceń pracy</h5>
        <p class="text-muted small mb-3">Zlecenia pracy są kategoryzowane według rodzaju wykonywanej konserwacji.</p>

        <div class="table-responsive">
            <table class="table table-sm table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Typ</th>
                        <th>Opis</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Korekcyjna</strong></td>
                        <td>Konserwacja reaktywna mająca na celu naprawę czegoś, co się zepsuło lub działa nieprawidłowo.</td>
                    </tr>
                    <tr>
                        <td><strong>Zapobiegawcza</strong></td>
                        <td>Planowa konserwacja zapobiegająca awariom, np. serwisowanie, smarowanie, wymiana filtrów.</td>
                    </tr>
                    <tr>
                        <td><strong>Inspekcja</strong></td>
                        <td>Rutynowe kontrole i oceny mające na celu wykrycie zużycia, uszkodzeń lub potencjalnych problemów przed awarią.</td>
                    </tr>
                    <tr>
                        <td><strong>Awaryjna</strong></td>
                        <td>Pilne, nieplanowane prace wymagane natychmiast z powodu zagrożenia bezpieczeństwa lub krytycznej awarii sprzętu.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-check2-square me-2"></i>Listy kontrolne</h5>
        <p class="text-muted small mb-3">Listy kontrolne to zestawy zadań dołączone do zlecenia pracy, które prowadzą techników przez poszczególne etapy pracy.</p>
        <ul class="mb-0">
            <li>Każde zlecenie pracy może mieć listę kontrolną z poszczególnymi zadaniami do wykonania.</li>
            <li>Odhaczaj pozycje w miarę ich realizacji &mdash; postęp jest zapisywany automatycznie.</li>
            <li>Kierownicy mogą dodawać pozycje do listy kontrolnej podczas tworzenia lub edycji zlecenia.</li>
            <li>Listy kontrolne zapewniają spójność i minimalizują ryzyko przeoczenia czegoś podczas konserwacji.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-box-seam me-2"></i>Części i czas</h5>
        <p class="text-muted small mb-3">Rejestrowanie części i czasu w zleceniu pracy zapewnia dokładne zapisy konserwacyjne i zarządzanie magazynem.</p>

        <h6>Zużycie części</h6>
        <ul>
            <li>Wybierz część z listy rozwijanej na stronie szczegółów zlecenia.</li>
            <li>Podaj zużytą ilość.</li>
            <li>Stan magazynowy jest automatycznie pomniejszany po zarejestrowaniu zużycia części.</li>
            <li>Gdy stan spadnie do lub poniżej poziomu minimalnego, wyzwalany jest alert o konieczności zamówienia.</li>
        </ul>

        <h6>Rejestrowanie czasu</h6>
        <ul class="mb-0">
            <li>Podaj liczbę minut poświęconych na zadanie.</li>
            <li>Dodaj krótką notatkę opisującą wykonane czynności.</li>
            <li>W jednym zleceniu pracy można zarejestrować wiele wpisów czasowych.</li>
            <li>Rejestry czasu pomagają śledzić koszty pracy i identyfikować zadania trwające dłużej niż oczekiwano.</li>
        </ul>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  PROPERTY & PARTS
    # ──────────────────────────────────────────────────────────────────────
    "property": (
        "Majątek i części",
        """\
<p class="text-muted mb-4">Majątek obejmuje wszystkie elementy wymagające konserwacji &mdash; maszyny, narzędzia, pojazdy i budynki. Części to części zamienne i materiały eksploatacyjne wykorzystywane podczas konserwacji.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-building-gear me-2"></i>Rejestr majątku</h5>
        <p class="text-muted small mb-3">Rejestr majątku to centralna ewidencja wszystkich elementów wymagających konserwacji w Twojej organizacji.</p>

        <ul>
            <li><strong>Czym jest element majątku?</strong> Każdy zasób wymagający konserwacji &mdash; sprzęt, maszyny, pojazdy, narzędzia lub elementy budynku (drzwi, klimatyzacja, windy itp.).</li>
            <li><strong>Kategorie</strong> &mdash; Grupuj elementy według typu (np. Elektryczne, Mechaniczne, Hydraulika) dla łatwiejszego filtrowania i raportowania.</li>
            <li><strong>Tagi</strong> &mdash; Dodawaj dowolne tagi do elementów, umożliwiające elastyczne grupowanie między kategoriami.</li>
            <li><strong>Zdjęcia</strong> &mdash; Przesyłaj zdjęcia, aby technicy mogli szybko zidentyfikować sprzęt w terenie.</li>
        </ul>

        <h6>Statusy majątku</h6>
        <div class="table-responsive">
            <table class="table table-sm table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Status</th>
                        <th>Znaczenie</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge bg-success">Sprawny</span></td>
                        <td>Element działa prawidłowo i jest dostępny do użytku.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-warning text-dark">Wymaga naprawy</span></td>
                        <td>Element ma znany problem i wymaga konserwacji.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-danger">Wyłączony z eksploatacji</span></td>
                        <td>Element nie działa i nie wolno go używać do czasu naprawy.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-secondary">Wycofany</span></td>
                        <td>Element został trwale wycofany i nie jest już konserwowany.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-qr-code me-2"></i>Etykiety z kodem QR</h5>
        <p class="text-muted small mb-3">Etykiety QR umożliwiają każdemu zeskanowanie urządzenia w celu natychmiastowego zgłoszenia problemu lub wyświetlenia historii konserwacji.</p>

        <h6>Drukowanie etykiet QR</h6>
        <ol>
            <li>Przejdź do strony z listą <strong>Majątku</strong>.</li>
            <li>Kliknij <strong>Drukuj wszystkie etykiety QR</strong>.</li>
            <li>Wybierz elementy, dla których chcesz wydrukować etykiety.</li>
            <li>Kliknij <strong>Drukuj</strong> &mdash; etykiety są sformatowane do standardowych arkuszy etykiet.</li>
        </ol>

        <h6>Pojedyncze etykiety</h6>
        <p class="mb-0">Możesz również wydrukować pojedynczą etykietę QR ze strony szczegółów dowolnego elementu majątku, klikając przycisk <strong>Drukuj etykietę QR</strong>.</p>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-box-seam me-2"></i>Magazyn części</h5>
        <p class="text-muted small mb-3">Śledź części zamienne i materiały eksploatacyjne, aby zawsze wiedzieć, co jest na stanie i kiedy zamawiać.</p>

        <ul class="mb-0">
            <li><strong>Stany magazynowe</strong> &mdash; Każda część ma bieżącą ilość na stanie oraz konfigurowalne poziomy minimalny i maksymalny.</li>
            <li><strong>Poziom minimalny</strong> &mdash; Gdy stan spadnie do lub poniżej tego progu, wyzwalany jest alert o konieczności zamówienia.</li>
            <li><strong>Poziom maksymalny</strong> &mdash; Zalecany górny limit, aby uniknąć nadmiernego zapasu.</li>
            <li><strong>Alerty zamówień</strong> &mdash; Części na poziomie minimalnym lub poniżej pojawiają się w Raporcie zamówień i są oznaczone na pulpicie.</li>
            <li><strong>Dane dostawcy</strong> &mdash; Zapisz nazwę dostawcy, dane kontaktowe i numer części w celu łatwego zamawiania.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-link-45deg me-2"></i>Kompatybilność części</h5>
        <p class="text-muted small mb-3">Powiąż części z elementami majątku, z którymi są kompatybilne, aby technicy zawsze wiedzieli, które części pasują do danego urządzenia.</p>

        <ul class="mb-0">
            <li>Na <strong>stronie szczegółów części</strong> możesz powiązać ją z jednym lub wieloma elementami majątku &mdash; strona części wyświetli wtedy cały kompatybilny sprzęt.</li>
            <li>Na <strong>stronie szczegółów majątku</strong> możesz zobaczyć wszystkie kompatybilne części &mdash; co ułatwia znalezienie właściwego zamiennika podczas naprawy.</li>
            <li>Powiązania kompatybilności działają w obu kierunkach: powiązanie części z elementem majątku powoduje również wyświetlenie tej części na stronie danego elementu.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-cart-check me-2"></i>Raport zamówień</h5>
        <p class="text-muted small mb-3">Raport zamówień pomaga nadążyć z uzupełnianiem zapasów, zanim zabraknie kluczowych części.</p>

        <ul>
            <li><strong>Co go wyzwala?</strong> Każda część, której bieżący stan jest na poziomie skonfigurowanego minimum lub poniżej.</li>
            <li><strong>Gdzie go znaleźć:</strong> Przejdź do <strong>Części</strong> &rarr; <strong>Raport zamówień</strong>.</li>
            <li><strong>Grupowanie wg dostawcy</strong> &mdash; Elementy są pogrupowane według przypisanego dostawcy, co ułatwia składanie zbiorczych zamówień.</li>
            <li><strong>Do druku</strong> &mdash; Raport jest przygotowany do druku, więc możesz przekazać go działowi zakupów lub zabrać ze sobą.</li>
        </ul>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  ADMIN GUIDE
    # ──────────────────────────────────────────────────────────────────────
    "admin": (
        "Przewodnik administratora",
        """\
<p class="text-muted mb-4">Ten przewodnik obejmuje administrację systemem &mdash; zarządzanie użytkownikami, zespołami, obiektami i ustawieniami.</p>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-people me-2"></i>Zarządzanie użytkownikami</h5>
        <p class="text-muted small mb-3">Konta użytkowników kontrolują, kto ma dostęp do systemu i co może robić.</p>

        <ul>
            <li><strong>Tworzenie użytkownika:</strong> Przejdź do <strong>Admin &rarr; Użytkownicy &rarr; Nowy użytkownik</strong>. Podaj imię i nazwisko, e-mail oraz przypisz rolę i obiekt(y).</li>
            <li><strong>Edycja użytkownika:</strong> Kliknij dowolnego użytkownika na liście, aby zaktualizować dane, rolę lub przypisania do obiektów.</li>
            <li><strong>Aktywacja/dezaktywacja:</strong> Dezaktywuj użytkownika, aby cofnąć dostęp bez usuwania konta. Możesz go aktywować ponownie w dowolnym momencie.</li>
            <li><strong>Resetowanie hasła:</strong> Administratorzy mogą zresetować hasło użytkownika ze strony edycji użytkownika.</li>
        </ul>

        <h6>Role</h6>
        <div class="table-responsive">
            <table class="table table-sm table-bordered mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Rola</th>
                        <th>Opis</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Administrator</strong></td>
                        <td>Pełny dostęp do systemu, w tym zarządzanie użytkownikami, ustawienia i wszystkie obiekty.</td>
                    </tr>
                    <tr>
                        <td><strong>Kierownik</strong></td>
                        <td>Może weryfikować zgłoszenia, tworzyć i przydzielać zlecenia pracy oraz zarządzać majątkiem i częściami.</td>
                    </tr>
                    <tr>
                        <td><strong>Technik</strong></td>
                        <td>Może przeglądać i realizować przydzielone zlecenia pracy, rejestrować części i czas.</td>
                    </tr>
                    <tr>
                        <td><strong>Zgłaszający</strong></td>
                        <td>Może wysyłać zgłoszenia konserwacyjne i śledzić ich postęp.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-person-badge me-2"></i>Zarządzanie zespołami</h5>
        <p class="text-muted small mb-3">Zespoły grupują techników w celu przydzielania pracy i planowania.</p>

        <ul>
            <li><strong>Zespoły wewnętrzne</strong> &mdash; Własny personel konserwacyjny, zorganizowany według specjalizacji lub obszaru (np. Elektryczny, Mechaniczny, Obiekty).</li>
            <li><strong>Zespoły wykonawców</strong> &mdash; Zewnętrzni usługodawcy obsługujący prace specjalistyczne lub dodatkowe.</li>
            <li><strong>Tworzenie zespołu:</strong> Przejdź do <strong>Admin &rarr; Zespoły &rarr; Nowy zespół</strong>. Podaj nazwę, wybierz typ (wewnętrzny/wykonawca) i dodaj członków.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-geo-alt me-2"></i>Zarządzanie obiektami</h5>
        <p class="text-muted small mb-3">Obiekty to fizyczne lokalizacje, które konserwuje Twoja organizacja.</p>

        <ul class="mb-0">
            <li><strong>Dodawanie obiektu:</strong> Przejdź do <strong>Admin &rarr; Obiekty &rarr; Nowy obiekt</strong>. Podaj nazwę obiektu, adres i krótki kod obiektu.</li>
            <li><strong>Kody obiektów</strong> &mdash; Krótkie identyfikatory (np. HQ, DEPOT-01) używane w raportach i etykietach do szybkiej identyfikacji.</li>
            <li>Użytkownicy i elementy majątku są przypisani do konkretnych obiektów, dzięki czemu dane są uporządkowane według lokalizacji.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-gear me-2"></i>Ustawienia</h5>
        <p class="text-muted small mb-3">Opcje konfiguracji systemu dostępne dla administratorów.</p>

        <ul class="mb-0">
            <li><strong>Zgłoszenia anonimowe</strong> &mdash; Przełącz, czy odwiedzający mogą wysyłać zgłoszenia konserwacyjne bez logowania. Po włączeniu każdy, kto zeskanuje kod QR, może zgłosić problem.</li>
            <li><strong>Wymagania dotyczące danych</strong> &mdash; Konfiguruj, czy anonimowi zgłaszający muszą podać imię i/lub adres e-mail przy wysyłaniu zgłoszenia.</li>
        </ul>
    </div>
</div>

<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h5 class="card-title"><i class="bi bi-list-check me-2"></i>Lista kontrolna wstępnej konfiguracji</h5>
        <p class="text-muted small mb-3">Wykonaj te kroki podczas pierwszej konfiguracji CMMS.</p>

        <div class="list-group list-group-flush">
            <div class="list-group-item px-0">
                <i class="bi bi-1-circle-fill text-primary me-2"></i>
                <strong>Zmień domyślne hasło administratora</strong>
                <p class="text-muted small mb-0 ms-4">Zabezpiecz konto administratora natychmiast po pierwszym logowaniu.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-2-circle-fill text-primary me-2"></i>
                <strong>Utwórz obiekty</strong>
                <p class="text-muted small mb-0 ms-4">Dodaj każdą fizyczną lokalizację, którą konserwuje Twoja organizacja.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-3-circle-fill text-primary me-2"></i>
                <strong>Utwórz zespoły (wewnętrzne + wykonawcy)</strong>
                <p class="text-muted small mb-0 ms-4">Skonfiguruj wewnętrzne zespoły konserwacyjne i ewentualne zespoły zewnętrznych wykonawców.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-4-circle-fill text-primary me-2"></i>
                <strong>Dodaj użytkowników, przypisz role i obiekty</strong>
                <p class="text-muted small mb-0 ms-4">Utwórz konta dla wszystkich osób korzystających z systemu i przypisz odpowiednie role.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-5-circle-fill text-primary me-2"></i>
                <strong>Dodaj lokalizacje dla każdego obiektu</strong>
                <p class="text-muted small mb-0 ms-4">Zdefiniuj konkretne obszary w każdym obiekcie (pomieszczenia, piętra, strefy) dla precyzyjnego zgłaszania usterek.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-6-circle-fill text-primary me-2"></i>
                <strong>Zarejestruj elementy majątku</strong>
                <p class="text-muted small mb-0 ms-4">Dodaj cały sprzęt, maszyny i elementy budynku wymagające konserwacji do rejestru majątku.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-7-circle-fill text-primary me-2"></i>
                <strong>Wydrukuj i przyklej etykiety QR</strong>
                <p class="text-muted small mb-0 ms-4">Wygeneruj kody QR i przyklej je do każdego elementu majątku w celu szybkiego skanowania.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-8-circle-fill text-primary me-2"></i>
                <strong>Dodaj części do magazynu</strong>
                <p class="text-muted small mb-0 ms-4">Wprowadź części zamienne i materiały eksploatacyjne ze stanami magazynowymi i danymi dostawców.</p>
            </div>
            <div class="list-group-item px-0">
                <i class="bi bi-9-circle-fill text-primary me-2"></i>
                <strong>Włącz zgłoszenia anonimowe, jeśli potrzebne</strong>
                <p class="text-muted small mb-0 ms-4">Włącz zgłoszenia anonimowe w Ustawieniach, jeśli chcesz, aby każdy mógł wysyłać zgłoszenia za pomocą kodów QR.</p>
            </div>
        </div>
    </div>
</div>"""
    ),

    # ──────────────────────────────────────────────────────────────────────
    #  FAQ
    # ──────────────────────────────────────────────────────────────────────
    "faq": (
        "Najczęściej zadawane pytania",
        """\
<h6 class="text-muted text-uppercase small mt-4 mb-3">Ogólne</h6>
<div class="accordion mb-4" id="faqGeneral">
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqGeneralH1">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqGeneralC1" aria-expanded="false" aria-controls="faqGeneralC1">
                Czym jest CMMS?
            </button>
        </h2>
        <div id="faqGeneralC1" class="accordion-collapse collapse" aria-labelledby="faqGeneralH1" data-bs-parent="#faqGeneral">
            <div class="accordion-body">
                CMMS to skrót od Computerised Maintenance Management System (Skomputeryzowany System Zarządzania Utrzymaniem Ruchu). Pomaga organizacjom śledzić zgłoszenia konserwacyjne, zarządzać zleceniami pracy, monitorować urządzenia i kontrolować magazyn części zamiennych &mdash; wszystko w jednym miejscu.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqGeneralH2">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqGeneralC2" aria-expanded="false" aria-controls="faqGeneralC2">
                Jak zgłosić problem?
            </button>
        </h2>
        <div id="faqGeneralC2" class="accordion-collapse collapse" aria-labelledby="faqGeneralH2" data-bs-parent="#faqGeneral">
            <div class="accordion-body">
                Najszybszym sposobem jest zeskanowanie etykiety z kodem QR na urządzeniu. Możesz również zalogować się i wysłać zgłoszenie przez stronę Zgłoszenia. Szczegóły znajdziesz w przewodniku <a href="/help/reporting">Zgłaszanie problemu</a>.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqGeneralH3">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqGeneralC3" aria-expanded="false" aria-controls="faqGeneralC3">
                Czy mogę zgłosić problem bez logowania?
            </button>
        </h2>
        <div id="faqGeneralC3" class="accordion-collapse collapse" aria-labelledby="faqGeneralH3" data-bs-parent="#faqGeneral">
            <div class="accordion-body">
                To zależy od ustawień Twojej organizacji. Jeśli administrator włączył zgłoszenia anonimowe, każdy może wysłać zgłoszenie skanując kod QR &mdash; konto nie jest wymagane. Jeśli zgłoszenia anonimowe są wyłączone, trzeba się najpierw zalogować.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqGeneralH4">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqGeneralC4" aria-expanded="false" aria-controls="faqGeneralC4">
                Jak zeskanować kod QR?
            </button>
        </h2>
        <div id="faqGeneralC4" class="accordion-collapse collapse" aria-labelledby="faqGeneralH4" data-bs-parent="#faqGeneral">
            <div class="accordion-body">
                Skieruj aparat telefonu na etykietę z kodem QR na urządzeniu. Większość nowoczesnych telefonów automatycznie rozpozna kod i wyświetli link &mdash; kliknij go, aby otworzyć formularz zgłoszenia w przeglądarce. Nie jest potrzebna żadna specjalna aplikacja.
            </div>
        </div>
    </div>
</div>

<h6 class="text-muted text-uppercase small mt-4 mb-3">Zgłoszenia</h6>
<div class="accordion mb-4" id="faqRequests">
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqRequestsH1">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqRequestsC1" aria-expanded="false" aria-controls="faqRequestsC1">
                Co oznaczają poziomy priorytetu?
            </button>
        </h2>
        <div id="faqRequestsC1" class="accordion-collapse collapse" aria-labelledby="faqRequestsH1" data-bs-parent="#faqRequests">
            <div class="accordion-body">
                <ul class="mb-0">
                    <li><strong>Niepilne</strong> &mdash; Drobna usterka, bez natychmiastowego wpływu. Może poczekać na planową konserwację.</li>
                    <li><strong>Normalne</strong> &mdash; Standardowy priorytet. Powinno być rozwiązane w normalnym trybie pracy.</li>
                    <li><strong>Pilne</strong> &mdash; Znaczący wpływ na działalność. Wymaga jak najszybszej uwagi.</li>
                    <li><strong>Awaria</strong> &mdash; Zagrożenie bezpieczeństwa lub awaria krytyczna. Wymaga natychmiastowej reakcji.</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqRequestsH2">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqRequestsC2" aria-expanded="false" aria-controls="faqRequestsC2">
                Jak śledzić moje zgłoszenie?
            </button>
        </h2>
        <div id="faqRequestsC2" class="accordion-collapse collapse" aria-labelledby="faqRequestsH2" data-bs-parent="#faqRequests">
            <div class="accordion-body">
                Jeśli jesteś zalogowany, przejdź do <strong>Pulpitu</strong> i sprawdź sekcję &bdquo;Moje zgłoszenia&rdquo;. Możesz również odwiedzić stronę <strong>Zgłoszenia</strong>, aby zobaczyć wszystkie swoje wpisy i ich aktualny status.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqRequestsH3">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqRequestsC3" aria-expanded="false" aria-controls="faqRequestsC3">
                Czy mogę dodać więcej informacji po wysłaniu zgłoszenia?
            </button>
        </h2>
        <div id="faqRequestsC3" class="accordion-collapse collapse" aria-labelledby="faqRequestsH3" data-bs-parent="#faqRequests">
            <div class="accordion-body">
                Tak. Otwórz swoje zgłoszenie i użyj sekcji komentarzy, aby dodać dodatkowe szczegóły. Możesz również przesłać dodatkowe pliki i zdjęcia po pierwszym wysłaniu zgłoszenia.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqRequestsH4">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqRequestsC4" aria-expanded="false" aria-controls="faqRequestsC4">
                Co się dzieje po wysłaniu zgłoszenia?
            </button>
        </h2>
        <div id="faqRequestsC4" class="accordion-collapse collapse" aria-labelledby="faqRequestsH4" data-bs-parent="#faqRequests">
            <div class="accordion-body">
                Kierownik weryfikuje zgłoszenie w kolejce. Potwierdzi je do dalszej analizy lub bezpośrednio przekształci w zlecenie pracy. Po utworzeniu zlecenia pracy przydzielany jest technik do wykonania naprawy.
            </div>
        </div>
    </div>
</div>

<h6 class="text-muted text-uppercase small mt-4 mb-3">Zlecenia pracy</h6>
<div class="accordion mb-4" id="faqWorkOrders">
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqWorkOrdersH1">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqWorkOrdersC1" aria-expanded="false" aria-controls="faqWorkOrdersC1">
                Jak zobaczyć przydzieloną mi pracę?
            </button>
        </h2>
        <div id="faqWorkOrdersC1" class="accordion-collapse collapse" aria-labelledby="faqWorkOrdersH1" data-bs-parent="#faqWorkOrders">
            <div class="accordion-body">
                Na Pulpicie wyświetlana jest sekcja &bdquo;Moje przydzielone zlecenia&rdquo; z listą wszystkich aktualnie przydzielonych Ci zleceń pracy. To najszybszy sposób, aby zobaczyć, co wymaga Twojej uwagi.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqWorkOrdersH2">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqWorkOrdersC2" aria-expanded="false" aria-controls="faqWorkOrdersC2">
                Jak ukończyć zlecenie pracy?
            </button>
        </h2>
        <div id="faqWorkOrdersC2" class="accordion-collapse collapse" aria-labelledby="faqWorkOrdersH2" data-bs-parent="#faqWorkOrders">
            <div class="accordion-body">
                Kliknij <strong>Rozpocznij pracę</strong>, aby zacząć, następnie wykonaj listę kontrolną, zarejestruj zużyte części i czas pracy, prześlij zdjęcia, a na koniec kliknij <strong>Ukończ</strong>. Zostaniesz poproszony o opisanie, co stwierdzono i co zostało zrobione.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqWorkOrdersH3">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqWorkOrdersC3" aria-expanded="false" aria-controls="faqWorkOrdersC3">
                Czy mogę wstrzymać zadanie?
            </button>
        </h2>
        <div id="faqWorkOrdersC3" class="accordion-collapse collapse" aria-labelledby="faqWorkOrdersH3" data-bs-parent="#faqWorkOrders">
            <div class="accordion-body">
                Tak. Gdy zlecenie pracy jest W realizacji, możesz kliknąć przycisk <strong>Wstrzymaj</strong>. Użyj tej opcji, gdy czekasz na dostawę części, potrzebujesz dostępu do zamkniętego pomieszczenia lub oczekujesz na dodatkowe informacje, zanim będziesz mógł kontynuować.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqWorkOrdersH4">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqWorkOrdersC4" aria-expanded="false" aria-controls="faqWorkOrdersC4">
                Jak zarejestrować części i czas?
            </button>
        </h2>
        <div id="faqWorkOrdersC4" class="accordion-collapse collapse" aria-labelledby="faqWorkOrdersH4" data-bs-parent="#faqWorkOrders">
            <div class="accordion-body">
                Na stronie szczegółów zlecenia pracy użyj listy rozwijanej części, aby wybrać część i podać zużytą ilość &mdash; stan magazynowy jest automatycznie pomniejszany. W przypadku czasu podaj liczbę przepracowanych minut i dodaj notatkę. Możesz dodać wiele wpisów zarówno dla części, jak i czasu.
            </div>
        </div>
    </div>
</div>

<h6 class="text-muted text-uppercase small mt-4 mb-3">Kierownicy</h6>
<div class="accordion mb-4" id="faqSupervisors">
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqSupervisorsH1">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqSupervisorsC1" aria-expanded="false" aria-controls="faqSupervisorsC1">
                Jak weryfikować zgłoszenia?
            </button>
        </h2>
        <div id="faqSupervisorsC1" class="accordion-collapse collapse" aria-labelledby="faqSupervisorsH1" data-bs-parent="#faqSupervisors">
            <div class="accordion-body">
                Na Pulpicie wyświetlana jest kolejka weryfikacji z nowymi i niepotwierdzonymi zgłoszeniami. Przejrzyj każde zgłoszenie i potwierdź je (aby oznaczyć jako widziane i analizowane) lub bezpośrednio przekształć w zlecenie pracy, jeśli sprawa jest jasna.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqSupervisorsH2">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqSupervisorsC2" aria-expanded="false" aria-controls="faqSupervisorsC2">
                Jak przekształcić zgłoszenie w zlecenie pracy?
            </button>
        </h2>
        <div id="faqSupervisorsC2" class="accordion-collapse collapse" aria-labelledby="faqSupervisorsH2" data-bs-parent="#faqSupervisors">
            <div class="accordion-body">
                Otwórz stronę szczegółów zgłoszenia i kliknij przycisk <strong>Przekształć w zlecenie pracy</strong>. Spowoduje to utworzenie nowego zlecenia pracy wstępnie wypełnionego danymi ze zgłoszenia. Następnie możesz je przydzielić technikowi i dodać listę kontrolną.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqSupervisorsH3">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqSupervisorsC3" aria-expanded="false" aria-controls="faqSupervisorsC3">
                Jak przydzielić pracę?
            </button>
        </h2>
        <div id="faqSupervisorsC3" class="accordion-collapse collapse" aria-labelledby="faqSupervisorsH3" data-bs-parent="#faqSupervisors">
            <div class="accordion-body">
                Otwórz stronę szczegółów zlecenia pracy i przejdź do sekcji Przydzielenie. Wybierz technika z listy rozwijanej i zapisz. Technik zobaczy zlecenie pracy w sekcji &bdquo;Moje przydzielone zlecenia&rdquo; na Pulpicie.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqSupervisorsH4">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqSupervisorsC4" aria-expanded="false" aria-controls="faqSupervisorsC4">
                Czym jest raport zamówień?
            </button>
        </h2>
        <div id="faqSupervisorsC4" class="accordion-collapse collapse" aria-labelledby="faqSupervisorsH4" data-bs-parent="#faqSupervisors">
            <div class="accordion-body">
                Raport zamówień pokazuje wszystkie części, których stan magazynowy spadł do lub poniżej poziomu minimalnego. Przejdź do <strong>Części &rarr; Raport zamówień</strong>, aby go wyświetlić. Elementy są pogrupowane według dostawcy, co ułatwia składanie zbiorczych zamówień. Raport można wydrukować.
            </div>
        </div>
    </div>
</div>

<h6 class="text-muted text-uppercase small mt-4 mb-3">Administracja</h6>
<div class="accordion mb-4" id="faqAdmin">
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqAdminH1">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqAdminC1" aria-expanded="false" aria-controls="faqAdminC1">
                Jak dodać nowego użytkownika?
            </button>
        </h2>
        <div id="faqAdminC1" class="accordion-collapse collapse" aria-labelledby="faqAdminH1" data-bs-parent="#faqAdmin">
            <div class="accordion-body">
                Przejdź do <strong>Admin &rarr; Użytkownicy &rarr; Nowy użytkownik</strong>. Podaj imię i nazwisko, adres e-mail i ustaw tymczasowe hasło. Przypisz rolę (Administrator, Kierownik, Technik lub Zgłaszający) i wybierz obiekty, do których użytkownik powinien mieć dostęp.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqAdminH2">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqAdminC2" aria-expanded="false" aria-controls="faqAdminC2">
                Jak włączyć zgłoszenia anonimowe?
            </button>
        </h2>
        <div id="faqAdminC2" class="accordion-collapse collapse" aria-labelledby="faqAdminH2" data-bs-parent="#faqAdmin">
            <div class="accordion-body">
                Przejdź do <strong>Admin &rarr; Ustawienia</strong> i przełącz opcję zgłoszeń anonimowych. Po włączeniu każdy, kto zeskanuje kod QR, może wysłać zgłoszenie konserwacyjne bez konieczności posiadania konta.
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header" id="faqAdminH3">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faqAdminC3" aria-expanded="false" aria-controls="faqAdminC3">
                Jak wydrukować etykiety QR?
            </button>
        </h2>
        <div id="faqAdminC3" class="accordion-collapse collapse" aria-labelledby="faqAdminH3" data-bs-parent="#faqAdmin">
            <div class="accordion-body">
                Przejdź do strony z listą <strong>Majątku</strong> i kliknij <strong>Drukuj wszystkie etykiety QR</strong>. Wybierz elementy, dla których chcesz etykiety, i kliknij Drukuj. Możesz również wydrukować pojedynczą etykietę ze strony szczegółów dowolnego elementu majątku.
            </div>
        </div>
    </div>
</div>"""
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
#  Seed runner
# ═══════════════════════════════════════════════════════════════════════════

def seed():
    inserted = 0
    skipped = 0

    with app.app_context():
        for slug, (title, content) in HELP_PAGES_PL.items():
            existing = HelpContent.query.filter_by(
                page_slug=slug, language="pl"
            ).first()
            if existing:
                print(f"  SKIP  {slug} (pl) — already exists (id={existing.id})")
                skipped += 1
                continue

            record = HelpContent(
                page_slug=slug,
                language="pl",
                title=title,
                content=content,
            )
            db.session.add(record)
            print(f"  ADD   {slug} (pl) — {title}")
            inserted += 1

        db.session.commit()

    print(f"\nDone. Inserted: {inserted}, Skipped: {skipped}, Total: {inserted + skipped}")


if __name__ == "__main__":
    seed()
