#!/usr/bin/env python3
"""Seed ALL English and Polish translations for CMMS.

Run:  python seed_translations.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.translation import Translation

app = create_app()

# ═══════════════════════════════════════════════════════════════════════
#  Format: {(key, category): {'en': 'English', 'pl': 'Polish'}}
# ═══════════════════════════════════════════════════════════════════════

TRANSLATIONS = {

    # ───────────────────────────────────────────────────────────────────
    #  NAVIGATION  (ui.navbar.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.navbar.dashboard', 'ui'): {
        'en': 'Dashboard',
        'pl': 'Pulpit',
    },
    ('ui.navbar.requests', 'ui'): {
        'en': 'Requests',
        'pl': 'Zgłoszenia',
    },
    ('ui.navbar.work_orders', 'ui'): {
        'en': 'Work Orders',
        'pl': 'Zlecenia pracy',
    },
    ('ui.navbar.property', 'ui'): {
        'en': 'Property',
        'pl': 'Majątek',
    },
    ('ui.navbar.locations', 'ui'): {
        'en': 'Locations',
        'pl': 'Lokalizacje',
    },
    ('ui.navbar.parts', 'ui'): {
        'en': 'Parts',
        'pl': 'Części',
    },
    ('ui.navbar.admin', 'ui'): {
        'en': 'Admin',
        'pl': 'Administracja',
    },
    ('ui.navbar.help_centre', 'ui'): {
        'en': 'Help Centre',
        'pl': 'Centrum pomocy',
    },
    ('ui.navbar.change_password', 'ui'): {
        'en': 'Change Password',
        'pl': 'Zmień hasło',
    },
    ('ui.navbar.sign_out', 'ui'): {
        'en': 'Sign Out',
        'pl': 'Wyloguj się',
    },
    ('ui.navbar.select_site', 'ui'): {
        'en': 'Select Site',
        'pl': 'Wybierz lokalizację',
    },

    # ───────────────────────────────────────────────────────────────────
    #  PAGE TITLES & HEADINGS  (ui.page.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.page.sign_in', 'ui'): {
        'en': 'Sign In',
        'pl': 'Logowanie',
    },
    ('ui.page.sign_in_subtitle', 'ui'): {
        'en': 'Sign in to your account',
        'pl': 'Zaloguj się na swoje konto',
    },
    ('ui.page.cmms_full', 'ui'): {
        'en': 'Computerised Maintenance Management System',
        'pl': 'Komputerowy system zarządzania konserwacją',
    },
    ('ui.page.dashboard', 'ui'): {
        'en': 'Dashboard',
        'pl': 'Pulpit',
    },
    ('ui.page.requests', 'ui'): {
        'en': 'Requests',
        'pl': 'Zgłoszenia',
    },
    ('ui.page.request_detail', 'ui'): {
        'en': 'Request #{id}',
        'pl': 'Zgłoszenie #{id}',
    },
    ('ui.page.report_problem', 'ui'): {
        'en': 'Report a Problem',
        'pl': 'Zgłoś problem',
    },
    ('ui.page.work_orders', 'ui'): {
        'en': 'Work Orders',
        'pl': 'Zlecenia pracy',
    },
    ('ui.page.new_work_order', 'ui'): {
        'en': 'New Work Order',
        'pl': 'Nowe zlecenie pracy',
    },
    ('ui.page.edit_work_order', 'ui'): {
        'en': 'Edit Work Order',
        'pl': 'Edytuj zlecenie pracy',
    },
    ('ui.page.property', 'ui'): {
        'en': 'Property',
        'pl': 'Majątek',
    },
    ('ui.page.new_property', 'ui'): {
        'en': 'New Property',
        'pl': 'Nowy majątek',
    },
    ('ui.page.edit_property', 'ui'): {
        'en': 'Edit Property',
        'pl': 'Edytuj majątek',
    },
    ('ui.page.locations', 'ui'): {
        'en': 'Locations',
        'pl': 'Lokalizacje',
    },
    ('ui.page.new_location', 'ui'): {
        'en': 'New Location',
        'pl': 'Nowa lokalizacja',
    },
    ('ui.page.edit_location', 'ui'): {
        'en': 'Edit Location',
        'pl': 'Edytuj lokalizację',
    },
    ('ui.page.parts_inventory', 'ui'): {
        'en': 'Parts Inventory',
        'pl': 'Magazyn części',
    },
    ('ui.page.new_part', 'ui'): {
        'en': 'New Part',
        'pl': 'Nowa część',
    },
    ('ui.page.edit_part', 'ui'): {
        'en': 'Edit Part',
        'pl': 'Edytuj część',
    },
    ('ui.page.reorder_report', 'ui'): {
        'en': 'Reorder Report',
        'pl': 'Raport zamówień',
    },
    ('ui.page.user_management', 'ui'): {
        'en': 'User Management',
        'pl': 'Zarządzanie użytkownikami',
    },
    ('ui.page.new_user', 'ui'): {
        'en': 'New User',
        'pl': 'Nowy użytkownik',
    },
    ('ui.page.edit_user', 'ui'): {
        'en': 'Edit User',
        'pl': 'Edytuj użytkownika',
    },
    ('ui.page.team_management', 'ui'): {
        'en': 'Team Management',
        'pl': 'Zarządzanie zespołami',
    },
    ('ui.page.new_team', 'ui'): {
        'en': 'New Team',
        'pl': 'Nowy zespół',
    },
    ('ui.page.edit_team', 'ui'): {
        'en': 'Edit Team',
        'pl': 'Edytuj zespół',
    },
    ('ui.page.site_management', 'ui'): {
        'en': 'Site Management',
        'pl': 'Zarządzanie obiektami',
    },
    ('ui.page.new_site', 'ui'): {
        'en': 'New Site',
        'pl': 'Nowy obiekt',
    },
    ('ui.page.edit_site', 'ui'): {
        'en': 'Edit Site',
        'pl': 'Edytuj obiekt',
    },
    ('ui.page.settings', 'ui'): {
        'en': 'Settings',
        'pl': 'Ustawienia',
    },
    ('ui.page.change_password', 'ui'): {
        'en': 'Change Password',
        'pl': 'Zmień hasło',
    },
    ('ui.page.print_qr_labels', 'ui'): {
        'en': 'Print QR Labels',
        'pl': 'Drukuj etykiety QR',
    },
    ('ui.page.qr_labels', 'ui'): {
        'en': 'QR Labels',
        'pl': 'Etykiety QR',
    },
    ('ui.page.report_submitted', 'ui'): {
        'en': 'Report Submitted',
        'pl': 'Zgłoszenie wysłane',
    },
    ('ui.page.access_denied', 'ui'): {
        'en': 'Access Denied',
        'pl': 'Brak dostępu',
    },
    ('ui.page.page_not_found', 'ui'): {
        'en': 'Page Not Found',
        'pl': 'Strona nie znaleziona',
    },
    ('ui.page.server_error', 'ui'): {
        'en': 'Something Went Wrong',
        'pl': 'Coś poszło nie tak',
    },
    ('ui.page.help_centre', 'ui'): {
        'en': 'Help Centre',
        'pl': 'Centrum pomocy',
    },
    ('ui.page.getting_started', 'ui'): {
        'en': 'Getting Started',
        'pl': 'Rozpoczęcie pracy',
    },
    ('ui.page.reporting', 'ui'): {
        'en': 'Reporting',
        'pl': 'Raportowanie',
    },
    ('ui.page.faq', 'ui'): {
        'en': 'FAQ',
        'pl': 'FAQ',
    },
    ('ui.page.admin_guide', 'ui'): {
        'en': 'Admin Guide',
        'pl': 'Przewodnik administratora',
    },

    # ───────────────────────────────────────────────────────────────────
    #  BUTTONS  (ui.button.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.button.sign_in', 'ui'): {
        'en': 'Sign In',
        'pl': 'Zaloguj się',
    },
    ('ui.button.cancel', 'ui'): {
        'en': 'Cancel',
        'pl': 'Anuluj',
    },
    ('ui.button.confirm', 'ui'): {
        'en': 'Confirm',
        'pl': 'Potwierdź',
    },
    ('ui.button.save_changes', 'ui'): {
        'en': 'Save Changes',
        'pl': 'Zapisz zmiany',
    },
    ('ui.button.save_settings', 'ui'): {
        'en': 'Save Settings',
        'pl': 'Zapisz ustawienia',
    },
    ('ui.button.update_password', 'ui'): {
        'en': 'Update Password',
        'pl': 'Zmień hasło',
    },
    ('ui.button.create_work_order', 'ui'): {
        'en': 'Create Work Order',
        'pl': 'Utwórz zlecenie pracy',
    },
    ('ui.button.create_property', 'ui'): {
        'en': 'Create Property',
        'pl': 'Utwórz majątek',
    },
    ('ui.button.create_location', 'ui'): {
        'en': 'Create Location',
        'pl': 'Utwórz lokalizację',
    },
    ('ui.button.create_part', 'ui'): {
        'en': 'Create Part',
        'pl': 'Utwórz część',
    },
    ('ui.button.create_user', 'ui'): {
        'en': 'Create User',
        'pl': 'Utwórz użytkownika',
    },
    ('ui.button.create_team', 'ui'): {
        'en': 'Create Team',
        'pl': 'Utwórz zespół',
    },
    ('ui.button.create_site', 'ui'): {
        'en': 'Create Site',
        'pl': 'Utwórz obiekt',
    },
    ('ui.button.new_request', 'ui'): {
        'en': 'New Request',
        'pl': 'Nowe zgłoszenie',
    },
    ('ui.button.new_work_order', 'ui'): {
        'en': 'New Work Order',
        'pl': 'Nowe zlecenie pracy',
    },
    ('ui.button.new_property', 'ui'): {
        'en': 'New Property',
        'pl': 'Nowy majątek',
    },
    ('ui.button.new_location', 'ui'): {
        'en': 'New Location',
        'pl': 'Nowa lokalizacja',
    },
    ('ui.button.new_part', 'ui'): {
        'en': 'New Part',
        'pl': 'Nowa część',
    },
    ('ui.button.new_user', 'ui'): {
        'en': 'New User',
        'pl': 'Nowy użytkownik',
    },
    ('ui.button.new_team', 'ui'): {
        'en': 'New Team',
        'pl': 'Nowy zespół',
    },
    ('ui.button.new_site', 'ui'): {
        'en': 'New Site',
        'pl': 'Nowy obiekt',
    },
    ('ui.button.view', 'ui'): {
        'en': 'View',
        'pl': 'Zobacz',
    },
    ('ui.button.edit', 'ui'): {
        'en': 'Edit',
        'pl': 'Edytuj',
    },
    ('ui.button.delete', 'ui'): {
        'en': 'Delete',
        'pl': 'Usuń',
    },
    ('ui.button.back', 'ui'): {
        'en': 'Back',
        'pl': 'Wstecz',
    },
    ('ui.button.back_to_dashboard', 'ui'): {
        'en': 'Back to Dashboard',
        'pl': 'Wróć do pulpitu',
    },
    ('ui.button.back_to_property', 'ui'): {
        'en': 'Back to Property',
        'pl': 'Wróć do majątku',
    },
    ('ui.button.back_to_parts', 'ui'): {
        'en': 'Back to Parts',
        'pl': 'Wróć do części',
    },
    ('ui.button.back_to_locations', 'ui'): {
        'en': 'Back to Locations',
        'pl': 'Wróć do lokalizacji',
    },
    ('ui.button.back_to_users', 'ui'): {
        'en': 'Back to Users',
        'pl': 'Wróć do użytkowników',
    },
    ('ui.button.back_to_teams', 'ui'): {
        'en': 'Back to Teams',
        'pl': 'Wróć do zespołów',
    },
    ('ui.button.back_to_sites', 'ui'): {
        'en': 'Back to Sites',
        'pl': 'Wróć do obiektów',
    },
    ('ui.button.back_to_selection', 'ui'): {
        'en': 'Back to Selection',
        'pl': 'Wróć do wyboru',
    },
    ('ui.button.print', 'ui'): {
        'en': 'Print',
        'pl': 'Drukuj',
    },
    ('ui.button.print_labels', 'ui'): {
        'en': 'Print Labels',
        'pl': 'Drukuj etykiety',
    },
    ('ui.button.print_selected_labels', 'ui'): {
        'en': 'Print Selected Labels',
        'pl': 'Drukuj wybrane etykiety',
    },
    ('ui.button.print_all_qr_labels', 'ui'): {
        'en': 'Print All QR Labels',
        'pl': 'Drukuj wszystkie etykiety QR',
    },
    ('ui.button.qr_label', 'ui'): {
        'en': 'QR Label',
        'pl': 'Etykieta QR',
    },
    ('ui.button.upload', 'ui'): {
        'en': 'Upload',
        'pl': 'Prześlij',
    },
    ('ui.button.comment', 'ui'): {
        'en': 'Comment',
        'pl': 'Komentarz',
    },
    ('ui.button.acknowledge', 'ui'): {
        'en': 'Acknowledge',
        'pl': 'Potwierdź odbiór',
    },
    ('ui.button.convert_to_wo', 'ui'): {
        'en': 'Convert to Work Order',
        'pl': 'Przekształć w zlecenie pracy',
    },
    ('ui.button.cancel_request', 'ui'): {
        'en': 'Cancel Request',
        'pl': 'Anuluj zgłoszenie',
    },
    ('ui.button.start_work', 'ui'): {
        'en': 'Start Work',
        'pl': 'Rozpocznij pracę',
    },
    ('ui.button.put_on_hold', 'ui'): {
        'en': 'Put on Hold',
        'pl': 'Wstrzymaj',
    },
    ('ui.button.resume_work', 'ui'): {
        'en': 'Resume Work',
        'pl': 'Wznów pracę',
    },
    ('ui.button.complete', 'ui'): {
        'en': 'Complete',
        'pl': 'Zakończ',
    },
    ('ui.button.mark_complete', 'ui'): {
        'en': 'Mark Complete',
        'pl': 'Oznacz jako zakończone',
    },
    ('ui.button.close', 'ui'): {
        'en': 'Close',
        'pl': 'Zamknij',
    },
    ('ui.button.assign', 'ui'): {
        'en': 'Assign',
        'pl': 'Przypisz',
    },
    ('ui.button.add', 'ui'): {
        'en': 'Add',
        'pl': 'Dodaj',
    },
    ('ui.button.add_part', 'ui'): {
        'en': 'Add Part',
        'pl': 'Dodaj część',
    },
    ('ui.button.log_time', 'ui'): {
        'en': 'Log Time',
        'pl': 'Zapisz czas',
    },
    ('ui.button.link', 'ui'): {
        'en': 'Link',
        'pl': 'Połącz',
    },
    ('ui.button.remove', 'ui'): {
        'en': 'Remove',
        'pl': 'Usuń',
    },
    ('ui.button.filter', 'ui'): {
        'en': 'Filter',
        'pl': 'Filtruj',
    },
    ('ui.button.search', 'ui'): {
        'en': 'Search',
        'pl': 'Szukaj',
    },
    ('ui.button.select_all', 'ui'): {
        'en': 'Select All',
        'pl': 'Zaznacz wszystko',
    },
    ('ui.button.select_none', 'ui'): {
        'en': 'None',
        'pl': 'Żaden',
    },
    ('ui.button.submit_request', 'ui'): {
        'en': 'Submit Request',
        'pl': 'Wyślij zgłoszenie',
    },
    ('ui.button.submit_report', 'ui'): {
        'en': 'Submit Report',
        'pl': 'Wyślij raport',
    },
    ('ui.button.report_problem', 'ui'): {
        'en': 'Report a Problem',
        'pl': 'Zgłoś problem',
    },
    ('ui.button.view_all', 'ui'): {
        'en': 'View All',
        'pl': 'Zobacz wszystko',
    },
    ('ui.button.reset_password', 'ui'): {
        'en': 'Reset Password',
        'pl': 'Resetuj hasło',
    },
    ('ui.button.reorder_report', 'ui'): {
        'en': 'Reorder Report',
        'pl': 'Raport zamówień',
    },
    ('ui.button.sign_in_to_track', 'ui'): {
        'en': 'Sign in to track this request',
        'pl': 'Zaloguj się, aby śledzić to zgłoszenie',
    },
    ('ui.button.add_first_property', 'ui'): {
        'en': 'Add First Property',
        'pl': 'Dodaj pierwszy majątek',
    },
    ('ui.button.add_first_location', 'ui'): {
        'en': 'Add First Location',
        'pl': 'Dodaj pierwszą lokalizację',
    },
    ('ui.button.create_first_team', 'ui'): {
        'en': 'Create First Team',
        'pl': 'Utwórz pierwszy zespół',
    },
    ('ui.button.create_first_site', 'ui'): {
        'en': 'Create First Site',
        'pl': 'Utwórz pierwszy obiekt',
    },
    ('ui.button.deactivate', 'ui'): {
        'en': 'Deactivate',
        'pl': 'Dezaktywuj',
    },
    ('ui.button.activate', 'ui'): {
        'en': 'Activate',
        'pl': 'Aktywuj',
    },
    ('ui.button.needs_reorder', 'ui'): {
        'en': 'Needs Reorder',
        'pl': 'Wymaga zamówienia',
    },

    # ───────────────────────────────────────────────────────────────────
    #  FORM LABELS  (ui.label.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.label.username', 'ui'): {
        'en': 'Username',
        'pl': 'Nazwa użytkownika',
    },
    ('ui.label.password', 'ui'): {
        'en': 'Password',
        'pl': 'Hasło',
    },
    ('ui.label.remember_me', 'ui'): {
        'en': 'Remember me',
        'pl': 'Zapamiętaj mnie',
    },
    ('ui.label.current_password', 'ui'): {
        'en': 'Current Password',
        'pl': 'Obecne hasło',
    },
    ('ui.label.new_password', 'ui'): {
        'en': 'New Password',
        'pl': 'Nowe hasło',
    },
    ('ui.label.confirm_password', 'ui'): {
        'en': 'Confirm New Password',
        'pl': 'Potwierdź nowe hasło',
    },
    ('ui.label.title', 'ui'): {
        'en': 'Title',
        'pl': 'Tytuł',
    },
    ('ui.label.description', 'ui'): {
        'en': 'Description',
        'pl': 'Opis',
    },
    ('ui.label.priority', 'ui'): {
        'en': 'Priority',
        'pl': 'Priorytet',
    },
    ('ui.label.status', 'ui'): {
        'en': 'Status',
        'pl': 'Status',
    },
    ('ui.label.location', 'ui'): {
        'en': 'Location',
        'pl': 'Lokalizacja',
    },
    ('ui.label.property', 'ui'): {
        'en': 'Property',
        'pl': 'Majątek',
    },
    ('ui.label.asset', 'ui'): {
        'en': 'Asset',
        'pl': 'Zasób',
    },
    ('ui.label.date', 'ui'): {
        'en': 'Date',
        'pl': 'Data',
    },
    ('ui.label.actions', 'ui'): {
        'en': 'Actions',
        'pl': 'Akcje',
    },
    ('ui.label.type', 'ui'): {
        'en': 'Type',
        'pl': 'Typ',
    },
    ('ui.label.assigned_to', 'ui'): {
        'en': 'Assigned To',
        'pl': 'Przypisany do',
    },
    ('ui.label.assign_to', 'ui'): {
        'en': 'Assign To',
        'pl': 'Przypisz do',
    },
    ('ui.label.due_date', 'ui'): {
        'en': 'Due Date',
        'pl': 'Termin',
    },
    ('ui.label.created', 'ui'): {
        'en': 'Created',
        'pl': 'Utworzono',
    },
    ('ui.label.created_by', 'ui'): {
        'en': 'Created By',
        'pl': 'Utworzony przez',
    },
    ('ui.label.submitted', 'ui'): {
        'en': 'Submitted',
        'pl': 'Zgłoszono',
    },
    ('ui.label.reported_by', 'ui'): {
        'en': 'Reported by',
        'pl': 'Zgłoszone przez',
    },
    ('ui.label.anonymous', 'ui'): {
        'en': 'Anonymous',
        'pl': 'Anonimowy',
    },
    ('ui.label.requester', 'ui'): {
        'en': 'Requester',
        'pl': 'Zgłaszający',
    },
    ('ui.label.wo_number', 'ui'): {
        'en': 'WO #',
        'pl': 'Nr zlecenia',
    },
    ('ui.label.work_order', 'ui'): {
        'en': 'Work Order',
        'pl': 'Zlecenie pracy',
    },
    ('ui.label.name', 'ui'): {
        'en': 'Name',
        'pl': 'Nazwa',
    },
    ('ui.label.email', 'ui'): {
        'en': 'Email',
        'pl': 'E-mail',
    },
    ('ui.label.display_name', 'ui'): {
        'en': 'Display Name',
        'pl': 'Nazwa wyświetlana',
    },
    ('ui.label.phone', 'ui'): {
        'en': 'Phone',
        'pl': 'Telefon',
    },
    ('ui.label.role', 'ui'): {
        'en': 'Role',
        'pl': 'Rola',
    },
    ('ui.label.team', 'ui'): {
        'en': 'Team',
        'pl': 'Zespół',
    },
    ('ui.label.sites', 'ui'): {
        'en': 'Sites',
        'pl': 'Obiekty',
    },
    ('ui.label.active', 'ui'): {
        'en': 'Active',
        'pl': 'Aktywny',
    },
    ('ui.label.inactive', 'ui'): {
        'en': 'Inactive',
        'pl': 'Nieaktywny',
    },
    ('ui.label.code', 'ui'): {
        'en': 'Code',
        'pl': 'Kod',
    },
    ('ui.label.address', 'ui'): {
        'en': 'Address',
        'pl': 'Adres',
    },
    ('ui.label.users', 'ui'): {
        'en': 'Users',
        'pl': 'Użytkownicy',
    },
    ('ui.label.teams', 'ui'): {
        'en': 'Teams',
        'pl': 'Zespoły',
    },
    ('ui.label.members', 'ui'): {
        'en': 'Members',
        'pl': 'Członkowie',
    },
    ('ui.label.tag_id', 'ui'): {
        'en': 'Tag / ID',
        'pl': 'Oznaczenie / ID',
    },
    ('ui.label.tag', 'ui'): {
        'en': 'Tag',
        'pl': 'Oznaczenie',
    },
    ('ui.label.category', 'ui'): {
        'en': 'Category',
        'pl': 'Kategoria',
    },
    ('ui.label.manufacturer', 'ui'): {
        'en': 'Manufacturer',
        'pl': 'Producent',
    },
    ('ui.label.model', 'ui'): {
        'en': 'Model',
        'pl': 'Model',
    },
    ('ui.label.serial_number', 'ui'): {
        'en': 'Serial Number',
        'pl': 'Numer seryjny',
    },
    ('ui.label.criticality', 'ui'): {
        'en': 'Criticality',
        'pl': 'Krytyczność',
    },
    ('ui.label.install_date', 'ui'): {
        'en': 'Install Date',
        'pl': 'Data instalacji',
    },
    ('ui.label.warranty_expiry', 'ui'): {
        'en': 'Warranty Expiry',
        'pl': 'Wygaśnięcie gwarancji',
    },
    ('ui.label.last_updated', 'ui'): {
        'en': 'Last Updated',
        'pl': 'Ostatnia aktualizacja',
    },
    ('ui.label.notes', 'ui'): {
        'en': 'Notes',
        'pl': 'Notatki',
    },
    ('ui.label.image', 'ui'): {
        'en': 'Image',
        'pl': 'Zdjęcie',
    },
    ('ui.label.replace_image', 'ui'): {
        'en': 'Replace image',
        'pl': 'Zmień zdjęcie',
    },
    ('ui.label.upload_image', 'ui'): {
        'en': 'Upload image',
        'pl': 'Prześlij zdjęcie',
    },
    ('ui.label.remove_current_image', 'ui'): {
        'en': 'Remove current image',
        'pl': 'Usuń obecne zdjęcie',
    },
    ('ui.label.remove_image', 'ui'): {
        'en': 'Remove image',
        'pl': 'Usuń zdjęcie',
    },
    ('ui.label.part_number', 'ui'): {
        'en': 'Part Number',
        'pl': 'Numer części',
    },
    ('ui.label.unit', 'ui'): {
        'en': 'Unit',
        'pl': 'Jednostka',
    },
    ('ui.label.unit_cost', 'ui'): {
        'en': 'Unit Cost',
        'pl': 'Koszt jednostkowy',
    },
    ('ui.label.storage_location', 'ui'): {
        'en': 'Storage Location',
        'pl': 'Miejsce przechowywania',
    },
    ('ui.label.quantity_on_hand', 'ui'): {
        'en': 'Quantity on Hand',
        'pl': 'Ilość na stanie',
    },
    ('ui.label.minimum_stock', 'ui'): {
        'en': 'Minimum Stock',
        'pl': 'Minimalny zapas',
    },
    ('ui.label.maximum_stock', 'ui'): {
        'en': 'Maximum Stock',
        'pl': 'Maksymalny zapas',
    },
    ('ui.label.stock_level', 'ui'): {
        'en': 'Stock Level',
        'pl': 'Poziom zapasu',
    },
    ('ui.label.supplier', 'ui'): {
        'en': 'Supplier',
        'pl': 'Dostawca',
    },
    ('ui.label.supplier_name', 'ui'): {
        'en': 'Supplier Name',
        'pl': 'Nazwa dostawcy',
    },
    ('ui.label.supplier_part_number', 'ui'): {
        'en': 'Supplier Part Number',
        'pl': 'Numer katalogowy dostawcy',
    },
    ('ui.label.supplier_email', 'ui'): {
        'en': 'Supplier Email',
        'pl': 'E-mail dostawcy',
    },
    ('ui.label.on_hand', 'ui'): {
        'en': 'on hand',
        'pl': 'na stanie',
    },
    ('ui.label.min', 'ui'): {
        'en': 'Min',
        'pl': 'Min',
    },
    ('ui.label.max', 'ui'): {
        'en': 'Max',
        'pl': 'Maks',
    },
    ('ui.label.in_stock', 'ui'): {
        'en': 'in stock',
        'pl': 'w magazynie',
    },
    ('ui.label.part', 'ui'): {
        'en': 'Part',
        'pl': 'Część',
    },
    ('ui.label.qty', 'ui'): {
        'en': 'Qty',
        'pl': 'Ilość',
    },
    ('ui.label.cost', 'ui'): {
        'en': 'Cost',
        'pl': 'Koszt',
    },
    ('ui.label.total', 'ui'): {
        'en': 'Total',
        'pl': 'Razem',
    },
    ('ui.label.subtotal', 'ui'): {
        'en': 'Subtotal',
        'pl': 'Suma częściowa',
    },
    ('ui.label.estimated_total', 'ui'): {
        'en': 'Estimated Total',
        'pl': 'Szacunkowa suma',
    },
    ('ui.label.order_qty', 'ui'): {
        'en': 'Order Qty',
        'pl': 'Zamówienie',
    },
    ('ui.label.line_total', 'ui'): {
        'en': 'Line Total',
        'pl': 'Suma pozycji',
    },
    ('ui.label.technician', 'ui'): {
        'en': 'Technician',
        'pl': 'Technik',
    },
    ('ui.label.duration', 'ui'): {
        'en': 'Duration',
        'pl': 'Czas trwania',
    },
    ('ui.label.duration_minutes', 'ui'): {
        'en': 'Duration (minutes)',
        'pl': 'Czas trwania (minuty)',
    },
    ('ui.label.completion_notes', 'ui'): {
        'en': 'Completion Notes',
        'pl': 'Notatki z wykonania',
    },
    ('ui.label.findings', 'ui'): {
        'en': 'Findings',
        'pl': 'Ustalenia',
    },
    ('ui.label.parent_location', 'ui'): {
        'en': 'Parent Location',
        'pl': 'Lokalizacja nadrzędna',
    },
    ('ui.label.location_type', 'ui'): {
        'en': 'Type',
        'pl': 'Typ',
    },
    ('ui.label.site_access', 'ui'): {
        'en': 'Site Access',
        'pl': 'Dostęp do obiektu',
    },
    ('ui.label.account_details', 'ui'): {
        'en': 'Account Details',
        'pl': 'Dane konta',
    },
    ('ui.label.role_and_team', 'ui'): {
        'en': 'Role & Team',
        'pl': 'Rola i zespół',
    },
    ('ui.label.contractor_team', 'ui'): {
        'en': 'Contractor team',
        'pl': 'Zespół wykonawców',
    },
    ('ui.label.is_contractor', 'ui'): {
        'en': 'Contractor',
        'pl': 'Wykonawca',
    },
    ('ui.label.internal', 'ui'): {
        'en': 'Internal',
        'pl': 'Wewnętrzny',
    },
    ('ui.label.your_name', 'ui'): {
        'en': 'Your Name',
        'pl': 'Twoje imię',
    },
    ('ui.label.email_or_phone', 'ui'): {
        'en': 'Email or Phone',
        'pl': 'E-mail lub telefon',
    },
    ('ui.label.request_number', 'ui'): {
        'en': 'Request Number',
        'pl': 'Numer zgłoszenia',
    },
    ('ui.label.add_file', 'ui'): {
        'en': 'Add file',
        'pl': 'Dodaj plik',
    },
    ('ui.label.add_photo', 'ui'): {
        'en': 'Add a photo',
        'pl': 'Dodaj zdjęcie',
    },
    ('ui.label.optional', 'ui'): {
        'en': 'optional',
        'pl': 'opcjonalnie',
    },
    ('ui.label.whats_wrong', 'ui'): {
        'en': "What's wrong?",
        'pl': 'Co się stało?',
    },
    ('ui.label.describe_problem', 'ui'): {
        'en': 'Describe the problem',
        'pl': 'Opisz problem',
    },
    ('ui.label.how_urgent', 'ui'): {
        'en': 'How urgent is this?',
        'pl': 'Jak pilne jest to?',
    },
    ('ui.label.not_urgent', 'ui'): {
        'en': 'Not urgent',
        'pl': 'Niepilne',
    },
    ('ui.label.normal', 'ui'): {
        'en': 'Normal',
        'pl': 'Normalne',
    },
    ('ui.label.urgent', 'ui'): {
        'en': 'Urgent',
        'pl': 'Pilne',
    },
    ('ui.label.emergency', 'ui'): {
        'en': 'Emergency',
        'pl': 'Awaryjne',
    },
    ('ui.label.all', 'ui'): {
        'en': 'All',
        'pl': 'Wszystkie',
    },
    ('ui.label.all_statuses', 'ui'): {
        'en': 'All Statuses',
        'pl': 'Wszystkie statusy',
    },
    ('ui.label.all_priorities', 'ui'): {
        'en': 'All Priorities',
        'pl': 'Wszystkie priorytety',
    },
    ('ui.label.overdue', 'ui'): {
        'en': 'Overdue',
        'pl': 'Zaległe',
    },
    ('ui.label.selected', 'ui'): {
        'en': '{count} selected',
        'pl': '{count} wybranych',
    },
    ('ui.label.items', 'ui'): {
        'en': '{count} items',
        'pl': '{count} pozycji',
    },
    ('ui.label.labels_count', 'ui'): {
        'en': '{count} label(s)',
        'pl': '{count} etykiet(y)',
    },
    ('ui.label.uncategorised', 'ui'): {
        'en': 'Uncategorised',
        'pl': 'Bez kategorii',
    },
    ('ui.label.scan_to_open', 'ui'): {
        'en': 'Scan to open',
        'pl': 'Zeskanuj, aby otworzyć',
    },
    ('ui.label.scan_to_report', 'ui'): {
        'en': 'Scan to report',
        'pl': 'Zeskanuj, aby zgłosić',
    },
    ('ui.label.compatible_property', 'ui'): {
        'en': 'Compatible Property',
        'pl': 'Kompatybilny majątek',
    },
    ('ui.label.compatible_parts', 'ui'): {
        'en': 'Compatible Parts',
        'pl': 'Kompatybilne części',
    },
    ('ui.label.work_order_history', 'ui'): {
        'en': 'Work Order History',
        'pl': 'Historia zleceń pracy',
    },
    ('ui.label.recent_usage', 'ui'): {
        'en': 'Recent Usage',
        'pl': 'Ostatnie użycie',
    },
    ('ui.label.used_by', 'ui'): {
        'en': 'Used By',
        'pl': 'Użyte przez',
    },
    ('ui.label.low_stock', 'ui'): {
        'en': 'Low Stock',
        'pl': 'Niski zapas',
    },
    ('ui.label.out_of_stock', 'ui'): {
        'en': 'Out of Stock',
        'pl': 'Brak na stanie',
    },
    ('ui.label.low_stock_parts', 'ui'): {
        'en': 'Low Stock Parts',
        'pl': 'Części z niskim zapasem',
    },
    ('ui.label.low_stock_alert', 'ui'): {
        'en': 'Low Stock Alert',
        'pl': 'Alert niskiego zapasu',
    },
    ('ui.label.adjust_stock', 'ui'): {
        'en': 'Adjust Stock',
        'pl': 'Skoryguj zapas',
    },
    ('ui.label.add_stock', 'ui'): {
        'en': 'Add Stock',
        'pl': 'Dodaj zapas',
    },
    ('ui.label.restock', 'ui'): {
        'en': 'Restock',
        'pl': 'Uzupełnienie',
    },
    ('ui.label.correction', 'ui'): {
        'en': 'Correction',
        'pl': 'Korekta',
    },
    ('ui.label.recent_adjustments', 'ui'): {
        'en': 'Recent adjustments',
        'pl': 'Ostatnie korekty',
    },
    ('ui.label.before', 'ui'): {
        'en': 'Before',
        'pl': 'Przed',
    },
    ('ui.label.after', 'ui'): {
        'en': 'After',
        'pl': 'Po',
    },
    ('ui.label.reversed', 'ui'): {
        'en': 'Reversed',
        'pl': 'Cofnięte',
    },
    ('ui.label.reason', 'ui'): {
        'en': 'Reason',
        'pl': 'Powód',
    },
    ('ui.label.by', 'ui'): {
        'en': 'By',
        'pl': 'Przez',
    },
    ('ui.text.adjustment_reason_placeholder', 'ui'): {
        'en': 'e.g. Delivery received, stocktake correction',
        'pl': 'np. Odebrano dostawę, korekta inwentaryzacji',
    },
    ('ui.button.reverse', 'ui'): {
        'en': 'Reverse',
        'pl': 'Cofnij',
    },
    ('ui.label.grouped_by_supplier', 'ui'): {
        'en': 'Grouped by Supplier',
        'pl': 'Pogrupowane wg dostawcy',
    },
    ('ui.label.no_supplier_specified', 'ui'): {
        'en': 'No supplier specified',
        'pl': 'Brak dostawcy',
    },
    ('ui.label.generated', 'ui'): {
        'en': 'Generated',
        'pl': 'Wygenerowano',
    },

    # ── Card headers / sections ──
    ('ui.label.property_information', 'ui'): {
        'en': 'Property Information',
        'pl': 'Informacje o majątku',
    },
    ('ui.label.classification_location', 'ui'): {
        'en': 'Classification & Location',
        'pl': 'Klasyfikacja i lokalizacja',
    },
    ('ui.label.property_details', 'ui'): {
        'en': 'Property Details',
        'pl': 'Szczegóły majątku',
    },
    ('ui.label.status_dates', 'ui'): {
        'en': 'Status & Dates',
        'pl': 'Status i daty',
    },
    ('ui.label.details', 'ui'): {
        'en': 'Details',
        'pl': 'Szczegóły',
    },
    ('ui.label.assignment', 'ui'): {
        'en': 'Assignment',
        'pl': 'Przypisanie',
    },
    ('ui.label.checklist', 'ui'): {
        'en': 'Checklist',
        'pl': 'Lista zadań',
    },
    ('ui.label.parts_used', 'ui'): {
        'en': 'Parts Used',
        'pl': 'Użyte części',
    },
    ('ui.label.time_log', 'ui'): {
        'en': 'Time Log',
        'pl': 'Rejestr czasu',
    },
    ('ui.label.attachments', 'ui'): {
        'en': 'Attachments',
        'pl': 'Załączniki',
    },
    ('ui.label.activity', 'ui'): {
        'en': 'Activity',
        'pl': 'Aktywność',
    },
    ('ui.label.findings_notes', 'ui'): {
        'en': 'Findings & Notes',
        'pl': 'Ustalenia i notatki',
    },
    ('ui.label.linked_request', 'ui'): {
        'en': 'Linked Request',
        'pl': 'Powiązane zgłoszenie',
    },
    ('ui.label.part_information', 'ui'): {
        'en': 'Part Information',
        'pl': 'Informacje o części',
    },
    ('ui.label.part_details', 'ui'): {
        'en': 'Part Details',
        'pl': 'Szczegóły części',
    },
    ('ui.label.stock_levels', 'ui'): {
        'en': 'Stock Levels',
        'pl': 'Poziomy zapasów',
    },
    ('ui.label.stock_supplier', 'ui'): {
        'en': 'Stock & Supplier',
        'pl': 'Zapas i dostawca',
    },
    ('ui.label.storage', 'ui'): {
        'en': 'Storage',
        'pl': 'Magazyn',
    },
    ('ui.label.select_property_to_print', 'ui'): {
        'en': 'Select Property to Print',
        'pl': 'Wybierz majątek do druku',
    },
    ('ui.label.anonymous_qr_reporting', 'ui'): {
        'en': 'Anonymous QR Reporting',
        'pl': 'Anonimowe zgłaszanie QR',
    },
    ('ui.label.allow_anonymous_requests', 'ui'): {
        'en': 'Allow anonymous requests via QR scan',
        'pl': 'Zezwól na anonimowe zgłoszenia przez skanowanie QR',
    },
    ('ui.label.require_reporter_name', 'ui'): {
        'en': "Require reporter's name",
        'pl': 'Wymagaj imienia zgłaszającego',
    },
    ('ui.label.require_reporter_email', 'ui'): {
        'en': "Require reporter's email or phone",
        'pl': 'Wymagaj e-maila lub telefonu zgłaszającego',
    },
    ('ui.label.confirm_action', 'ui'): {
        'en': 'Confirm Action',
        'pl': 'Potwierdź akcję',
    },
    ('ui.label.are_you_sure', 'ui'): {
        'en': 'Are you sure?',
        'pl': 'Czy na pewno?',
    },
    ('ui.label.select', 'ui'): {
        'en': '— Select —',
        'pl': '— Wybierz —',
    },
    ('ui.label.select_location', 'ui'): {
        'en': '— Select location (optional) —',
        'pl': '— Wybierz lokalizację (opcjonalnie) —',
    },
    ('ui.label.select_property', 'ui'): {
        'en': '— Select property (optional) —',
        'pl': '— Wybierz majątek (opcjonalnie) —',
    },
    ('ui.label.select_asset', 'ui'): {
        'en': '— Select asset (optional) —',
        'pl': '— Wybierz zasób (opcjonalnie) —',
    },
    ('ui.label.unassigned', 'ui'): {
        'en': '— Unassigned —',
        'pl': '— Nieprzypisany —',
    },
    ('ui.label.none_top_level', 'ui'): {
        'en': '— None (top level) —',
        'pl': '— Brak (najwyższy poziom) —',
    },
    ('ui.label.none', 'ui'): {
        'en': '— None —',
        'pl': '— Brak —',
    },
    ('ui.label.add_property', 'ui'): {
        'en': '— Add property —',
        'pl': '— Dodaj majątek —',
    },

    # ───────────────────────────────────────────────────────────────────
    #  TEXT / DESCRIPTIONS  (ui.text.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.text.password_min_chars', 'ui'): {
        'en': 'Must be at least 8 characters.',
        'pl': 'Musi mieć co najmniej 8 znaków.',
    },
    ('ui.text.password_keep_current', 'ui'): {
        'en': 'leave blank to keep current',
        'pl': 'pozostaw puste, aby zachować obecne',
    },
    ('ui.text.open_requests', 'ui'): {
        'en': 'Open Requests',
        'pl': 'Otwarte zgłoszenia',
    },
    ('ui.text.open_work_orders', 'ui'): {
        'en': 'Open Work Orders',
        'pl': 'Otwarte zlecenia',
    },
    ('ui.text.overdue', 'ui'): {
        'en': 'Overdue',
        'pl': 'Zaległe',
    },
    ('ui.text.triage_queue', 'ui'): {
        'en': 'Triage Queue',
        'pl': 'Kolejka segregacji',
    },
    ('ui.text.my_assigned_work_orders', 'ui'): {
        'en': 'My Assigned Work Orders',
        'pl': 'Moje przypisane zlecenia',
    },
    ('ui.text.recent_work_orders', 'ui'): {
        'en': 'Recent Work Orders',
        'pl': 'Ostatnie zlecenia pracy',
    },
    ('ui.text.my_recent_requests', 'ui'): {
        'en': 'My Recent Requests',
        'pl': 'Moje ostatnie zgłoszenia',
    },
    ('ui.text.no_site_selected', 'ui'): {
        'en': 'No site is currently selected. Please ask an administrator to assign you to a site.',
        'pl': 'Nie wybrano żadnego obiektu. Poproś administratora o przypisanie do obiektu.',
    },
    ('ui.text.no_requests_found', 'ui'): {
        'en': 'No requests found.',
        'pl': 'Nie znaleziono zgłoszeń.',
    },
    ('ui.text.no_work_orders_found', 'ui'): {
        'en': 'No work orders found.',
        'pl': 'Nie znaleziono zleceń pracy.',
    },
    ('ui.text.no_property_found', 'ui'): {
        'en': 'No property found.',
        'pl': 'Nie znaleziono majątku.',
    },
    ('ui.text.no_locations_defined', 'ui'): {
        'en': 'No locations defined yet.',
        'pl': 'Brak zdefiniowanych lokalizacji.',
    },
    ('ui.text.no_parts_found', 'ui'): {
        'en': 'No parts found.',
        'pl': 'Nie znaleziono części.',
    },
    ('ui.text.no_parts_need_reorder', 'ui'): {
        'en': 'No parts need reordering.',
        'pl': 'Brak części wymagających zamówienia.',
    },
    ('ui.text.no_users_found', 'ui'): {
        'en': 'No users found.',
        'pl': 'Nie znaleziono użytkowników.',
    },
    ('ui.text.no_teams_defined', 'ui'): {
        'en': 'No teams defined yet.',
        'pl': 'Brak zdefiniowanych zespołów.',
    },
    ('ui.text.no_sites_defined', 'ui'): {
        'en': 'No sites defined yet.',
        'pl': 'Brak zdefiniowanych obiektów.',
    },
    ('ui.text.no_sites_available', 'ui'): {
        'en': 'No sites available. Create sites first.',
        'pl': 'Brak dostępnych obiektów. Najpierw utwórz obiekty.',
    },
    ('ui.text.no_property_at_site', 'ui'): {
        'en': 'No property found at this site.',
        'pl': 'Nie znaleziono majątku w tym obiekcie.',
    },
    ('ui.text.no_attachments', 'ui'): {
        'en': 'No attachments.',
        'pl': 'Brak załączników.',
    },
    ('ui.text.no_activity_recorded', 'ui'): {
        'en': 'No activity recorded yet.',
        'pl': 'Brak zarejestrowanej aktywności.',
    },
    ('ui.text.no_tasks_yet', 'ui'): {
        'en': 'No tasks yet.',
        'pl': 'Brak zadań.',
    },
    ('ui.text.no_parts_recorded', 'ui'): {
        'en': 'No parts recorded.',
        'pl': 'Brak zarejestrowanych części.',
    },
    ('ui.text.no_time_logged', 'ui'): {
        'en': 'No time logged.',
        'pl': 'Brak zarejestrowanego czasu.',
    },
    ('ui.text.no_notes_recorded', 'ui'): {
        'en': 'No notes recorded yet.',
        'pl': 'Brak zapisanych notatek.',
    },
    ('ui.text.no_work_orders_for_property', 'ui'): {
        'en': 'No work orders for this property.',
        'pl': 'Brak zleceń pracy dla tego majątku.',
    },
    ('ui.text.no_property_linked', 'ui'): {
        'en': 'No property linked yet.',
        'pl': 'Brak powiązanego majątku.',
    },
    ('ui.text.no_usage_recorded', 'ui'): {
        'en': 'No usage recorded.',
        'pl': 'Brak zarejestrowanego zużycia.',
    },
    ('ui.text.all_stock_healthy', 'ui'): {
        'en': 'All stock levels are healthy',
        'pl': 'Wszystkie poziomy zapasów są prawidłowe',
    },
    ('ui.text.no_parts_need_reorder_now', 'ui'): {
        'en': 'No parts need reordering at this time.',
        'pl': 'Żadne części nie wymagają teraz zamówienia.',
    },
    ('ui.text.of_complete', 'ui'): {
        'en': '{done} of {total} complete',
        'pl': '{done} z {total} ukończonych',
    },
    ('ui.text.select_sites_access', 'ui'): {
        'en': 'Select which sites this user can access.',
        'pl': 'Wybierz, do których obiektów ten użytkownik ma dostęp.',
    },
    ('ui.text.select_compatible_property', 'ui'): {
        'en': 'Select which machines, tools, or equipment this part fits.',
        'pl': 'Wybierz, do jakich maszyn, narzędzi lub urządzeń pasuje ta część.',
    },
    ('ui.text.reorder_alert_trigger', 'ui'): {
        'en': 'Reorder alert triggers at this level.',
        'pl': 'Alert zamówienia uruchamia się na tym poziomie.',
    },
    ('ui.text.target_level', 'ui'): {
        'en': 'Target level for reorder quantity.',
        'pl': 'Docelowy poziom ilości zamówienia.',
    },
    ('ui.text.contractor_team_help', 'ui'): {
        'en': 'Check if this team consists of external contractors.',
        'pl': 'Zaznacz, jeśli ten zespół składa się z zewnętrznych wykonawców.',
    },
    ('ui.text.site_code_help', 'ui'): {
        'en': 'Short identifier (e.g. HQ, WEST, FAC-01). Will be uppercased.',
        'pl': 'Krótki identyfikator (np. HQ, WEST, FAC-01). Zostanie zamieniony na wielkie litery.',
    },
    ('ui.text.image_formats', 'ui'): {
        'en': 'JPEG, PNG, WebP, or GIF. Max 16 MB.',
        'pl': 'JPEG, PNG, WebP lub GIF. Maks. 16 MB.',
    },
    ('ui.text.image_formats_short', 'ui'): {
        'en': 'JPEG, PNG, WebP, or GIF.',
        'pl': 'JPEG, PNG, WebP lub GIF.',
    },
    ('ui.text.priority_help', 'ui'): {
        'en': 'Not urgent = no impact. Normal = fix within days. Urgent = significant impact. Emergency = safety risk or operations stopped.',
        'pl': 'Niepilne = brak wpływu. Normalne = naprawa w ciągu dni. Pilne = znaczny wpływ. Awaryjne = zagrożenie bezpieczeństwa lub wstrzymanie operacji.',
    },
    ('ui.text.wo_type_help', 'ui'): {
        'en': 'Corrective = fix a fault. Preventive = scheduled service. Inspection = condition check. Emergency = immediate safety/production risk.',
        'pl': 'Korekcyjne = naprawa usterki. Prewencyjne = planowy serwis. Inspekcja = kontrola stanu. Awaryjne = natychmiastowe zagrożenie bezpieczeństwa/produkcji.',
    },
    ('ui.text.anonymous_reporting_help', 'ui'): {
        'en': 'When enabled, anyone who scans a QR code on a piece of property can submit a maintenance request without logging in. Their name and contact details are captured on the form instead.',
        'pl': 'Po włączeniu każdy, kto zeskanuje kod QR na majątku, może wysłać zgłoszenie konserwacji bez logowania. Imię i dane kontaktowe zostaną pobrane z formularza.',
    },
    ('ui.text.report_received', 'ui'): {
        'en': 'Your report has been received and the maintenance team will review it shortly.',
        'pl': 'Twoje zgłoszenie zostało odebrane i zespół konserwacji wkrótce je rozpatrzy.',
    },
    ('ui.text.what_happens_next', 'ui'): {
        'en': 'What happens next?',
        'pl': 'Co dalej?',
    },
    ('ui.text.next_step_review', 'ui'): {
        'en': 'A supervisor will review your report',
        'pl': 'Przełożony sprawdzi Twoje zgłoszenie',
    },
    ('ui.text.next_step_assign', 'ui'): {
        'en': 'A technician will be assigned to fix the problem',
        'pl': 'Technik zostanie przypisany do naprawy problemu',
    },
    ('ui.text.next_step_check', 'ui'): {
        'en': 'You can check back by scanning the same QR code',
        'pl': 'Możesz sprawdzić status, skanując ten sam kod QR',
    },
    ('ui.text.cmms_maintenance_reporting', 'ui'): {
        'en': 'CMMS Maintenance Reporting',
        'pl': 'CMMS Raportowanie konserwacji',
    },
    ('ui.text.access_denied_message', 'ui'): {
        'en': 'You do not have permission to access this page.',
        'pl': 'Nie masz uprawnień do wyświetlenia tej strony.',
    },
    ('ui.text.page_not_found_message', 'ui'): {
        'en': 'The page you are looking for does not exist.',
        'pl': 'Strona, której szukasz, nie istnieje.',
    },
    ('ui.text.server_error_message', 'ui'): {
        'en': 'An unexpected error occurred. Please try again later.',
        'pl': 'Wystąpił nieoczekiwany błąd. Spróbuj ponownie później.',
    },
    ('ui.text.cancel_this_request', 'ui'): {
        'en': 'Cancel this request?',
        'pl': 'Anulować to zgłoszenie?',
    },
    ('ui.text.close_this_wo', 'ui'): {
        'en': 'Close this work order?',
        'pl': 'Zamknąć to zlecenie pracy?',
    },
    ('ui.text.remove_this_link', 'ui'): {
        'en': 'Remove this link?',
        'pl': 'Usunąć to powiązanie?',
    },
    ('ui.text.no_site_assigned', 'ui'): {
        'en': 'No site assigned to your account. Contact an administrator.',
        'pl': 'Brak przypisanego obiektu do Twojego konta. Skontaktuj się z administratorem.',
    },
    ('ui.text.reorder_quantity', 'ui'): {
        'en': 'Reorder {qty} {unit}(s)',
        'pl': 'Zamów {qty} {unit}',
    },
    ('ui.text.to_reach_maximum', 'ui'): {
        'en': 'to reach maximum ({max})',
        'pl': 'aby osiągnąć maksimum ({max})',
    },
    ('ui.text.to_reach_safe_level', 'ui'): {
        'en': 'to reach safe level',
        'pl': 'aby osiągnąć bezpieczny poziom',
    },
    ('ui.text.est_cost', 'ui'): {
        'en': 'est. cost',
        'pl': 'szacunkowy koszt',
    },
    ('ui.text.search_property_placeholder', 'ui'): {
        'en': 'Search by name, tag, or serial number...',
        'pl': 'Szukaj wg nazwy, oznaczenia lub numeru seryjnego...',
    },
    ('ui.text.search_parts_placeholder', 'ui'): {
        'en': 'Search by name, part number, or supplier...',
        'pl': 'Szukaj wg nazwy, numeru części lub dostawcy...',
    },
    ('ui.text.wo_title_placeholder', 'ui'): {
        'en': 'Work order title',
        'pl': 'Tytuł zlecenia pracy',
    },
    ('ui.text.wo_description_placeholder', 'ui'): {
        'en': 'Detailed description...',
        'pl': 'Szczegółowy opis...',
    },
    ('ui.text.add_comment_placeholder', 'ui'): {
        'en': 'Add a comment...',
        'pl': 'Dodaj komentarz...',
    },
    ('ui.text.add_task_placeholder', 'ui'): {
        'en': 'Add a task...',
        'pl': 'Dodaj zadanie...',
    },
    ('ui.text.completion_notes_placeholder', 'ui'): {
        'en': 'What was done to resolve the issue...',
        'pl': 'Co zrobiono, aby rozwiązać problem...',
    },
    ('ui.text.findings_placeholder', 'ui'): {
        'en': 'Root cause, observations, recommendations...',
        'pl': 'Przyczyna, obserwacje, zalecenia...',
    },
    ('ui.text.time_notes_placeholder', 'ui'): {
        'en': 'What was done...',
        'pl': 'Co zostało zrobione...',
    },
    ('ui.text.enter_username', 'ui'): {
        'en': 'Enter username',
        'pl': 'Wprowadź nazwę użytkownika',
    },
    ('ui.text.enter_password', 'ui'): {
        'en': 'Enter password',
        'pl': 'Wprowadź hasło',
    },
    ('ui.text.problem_placeholder', 'ui'): {
        'en': "e.g. Fridge not cold, door won't close, strange noise",
        'pl': 'np. Lodówka nie chłodzi, drzwi się nie zamykają, dziwny dźwięk',
    },
    ('ui.text.problem_desc_placeholder', 'ui'): {
        'en': 'What did you notice? When did it start? Is it getting worse?',
        'pl': 'Co zauważyłeś? Kiedy to się zaczęło? Czy się pogarsza?',
    },
    ('ui.text.reporter_name_placeholder', 'ui'): {
        'en': 'e.g. John Smith',
        'pl': 'np. Jan Kowalski',
    },
    ('ui.text.reporter_contact_placeholder', 'ui'): {
        'en': 'e.g. john@example.com',
        'pl': 'np. jan@example.com',
    },
    ('ui.text.reporter_followup_placeholder', 'ui'): {
        'en': 'So we can follow up with you',
        'pl': 'Abyśmy mogli się z Tobą skontaktować',
    },
    ('ui.text.storage_location_placeholder', 'ui'): {
        'en': 'e.g. Shelf A3',
        'pl': 'np. Półka A3',
    },
    ('ui.text.property_in_location', 'ui'): {
        'en': 'Property in this location',
        'pl': 'Majątek w tej lokalizacji',
    },

    # ── Admin sub-nav ──
    ('ui.text.admin_tab_users', 'ui'): {
        'en': 'Users',
        'pl': 'Użytkownicy',
    },
    ('ui.text.admin_tab_teams', 'ui'): {
        'en': 'Teams',
        'pl': 'Zespoły',
    },
    ('ui.text.admin_tab_sites', 'ui'): {
        'en': 'Sites',
        'pl': 'Obiekty',
    },
    ('ui.text.admin_tab_settings', 'ui'): {
        'en': 'Settings',
        'pl': 'Ustawienia',
    },

    # ───────────────────────────────────────────────────────────────────
    #  FLASH MESSAGES  (flash.*)
    # ───────────────────────────────────────────────────────────────────

    # auth
    ('flash.login_required', 'flash'): {
        'en': 'Please sign in to access this page.',
        'pl': 'Zaloguj się, aby uzyskać dostęp do tej strony.',
    },
    ('flash.too_many_attempts', 'flash'): {
        'en': 'Too many login attempts. Please wait and try again.',
        'pl': 'Zbyt wiele prób logowania. Poczekaj i spróbuj ponownie.',
    },
    ('flash.welcome_back', 'flash'): {
        'en': 'Welcome back, {name}!',
        'pl': 'Witaj ponownie, {name}!',
    },
    ('flash.invalid_credentials', 'flash'): {
        'en': 'Invalid username or password.',
        'pl': 'Nieprawidłowa nazwa użytkownika lub hasło.',
    },
    ('flash.signed_out', 'flash'): {
        'en': 'You have been signed out.',
        'pl': 'Zostałeś wylogowany.',
    },
    ('flash.current_password_incorrect', 'flash'): {
        'en': 'Current password is incorrect.',
        'pl': 'Obecne hasło jest nieprawidłowe.',
    },
    ('flash.password_too_short', 'flash'): {
        'en': 'New password must be at least 8 characters.',
        'pl': 'Nowe hasło musi mieć co najmniej 8 znaków.',
    },
    ('flash.passwords_no_match', 'flash'): {
        'en': 'New passwords do not match.',
        'pl': 'Nowe hasła nie pasują do siebie.',
    },
    ('flash.password_changed', 'flash'): {
        'en': 'Password changed successfully.',
        'pl': 'Hasło zostało zmienione pomyślnie.',
    },

    # dashboard
    ('flash.no_site_access', 'flash'): {
        'en': 'You do not have access to that site.',
        'pl': 'Nie masz dostępu do tego obiektu.',
    },
    ('flash.switched_site', 'flash'): {
        'en': 'Switched to {name}.',
        'pl': 'Przełączono na {name}.',
    },
    ('flash.property_not_found_qr', 'flash'): {
        'en': 'Property not found. Please report the problem manually.',
        'pl': 'Majątek nie znaleziony. Zgłoś problem ręcznie.',
    },

    # requests
    ('flash.title_description_required', 'flash'): {
        'en': 'Title and description are required.',
        'pl': 'Tytuł i opis są wymagane.',
    },
    ('flash.request_submitted', 'flash'): {
        'en': 'Request submitted successfully.',
        'pl': 'Zgłoszenie zostało wysłane pomyślnie.',
    },
    ('flash.request_acknowledged', 'flash'): {
        'en': 'Request acknowledged.',
        'pl': 'Zgłoszenie potwierdzone.',
    },
    ('flash.request_already_has_wo', 'flash'): {
        'en': 'This request already has a linked work order.',
        'pl': 'To zgłoszenie ma już powiązane zlecenie pracy.',
    },
    ('flash.wo_created_from_request', 'flash'): {
        'en': 'Work order created from request.',
        'pl': 'Zlecenie pracy utworzone ze zgłoszenia.',
    },
    ('flash.request_cancelled', 'flash'): {
        'en': 'Request cancelled.',
        'pl': 'Zgłoszenie anulowane.',
    },
    ('flash.no_file_selected', 'flash'): {
        'en': 'No file selected.',
        'pl': 'Nie wybrano pliku.',
    },
    ('flash.file_type_not_allowed', 'flash'): {
        'en': 'File type not allowed.',
        'pl': 'Niedozwolony typ pliku.',
    },
    ('flash.file_uploaded', 'flash'): {
        'en': 'File uploaded.',
        'pl': 'Plik przesłany.',
    },
    ('flash.comment_empty', 'flash'): {
        'en': 'Comment cannot be empty.',
        'pl': 'Komentarz nie może być pusty.',
    },
    ('flash.comment_added', 'flash'): {
        'en': 'Comment added.',
        'pl': 'Komentarz dodany.',
    },
    ('flash.name_required', 'flash'): {
        'en': 'Your name is required.',
        'pl': 'Twoje imię jest wymagane.',
    },
    ('flash.email_required', 'flash'): {
        'en': 'Your email or phone is required.',
        'pl': 'Twój e-mail lub telefon jest wymagany.',
    },

    # work orders
    ('flash.title_required', 'flash'): {
        'en': 'Title is required.',
        'pl': 'Tytuł jest wymagany.',
    },
    ('flash.invalid_due_date', 'flash'): {
        'en': 'Invalid due date format.',
        'pl': 'Nieprawidłowy format daty.',
    },
    ('flash.wo_created', 'flash'): {
        'en': 'Work order created.',
        'pl': 'Zlecenie pracy utworzone.',
    },
    ('flash.wo_updated', 'flash'): {
        'en': 'Work order updated.',
        'pl': 'Zlecenie pracy zaktualizowane.',
    },
    ('flash.wo_assigned', 'flash'): {
        'en': 'Work order assigned.',
        'pl': 'Zlecenie pracy przypisane.',
    },
    ('flash.work_started', 'flash'): {
        'en': 'Work started.',
        'pl': 'Praca rozpoczęta.',
    },
    ('flash.wo_completed', 'flash'): {
        'en': 'Work order marked as completed.',
        'pl': 'Zlecenie pracy oznaczone jako zakończone.',
    },
    ('flash.wo_closed', 'flash'): {
        'en': 'Work order closed.',
        'pl': 'Zlecenie pracy zamknięte.',
    },
    ('flash.wo_on_hold', 'flash'): {
        'en': 'Work order put on hold.',
        'pl': 'Zlecenie pracy wstrzymane.',
    },
    ('flash.task_description_required', 'flash'): {
        'en': 'Task description is required.',
        'pl': 'Opis zadania jest wymagany.',
    },
    ('flash.task_added', 'flash'): {
        'en': 'Task added.',
        'pl': 'Zadanie dodane.',
    },
    ('flash.select_part_quantity', 'flash'): {
        'en': 'Select a part and enter a valid quantity.',
        'pl': 'Wybierz część i wprowadź prawidłową ilość.',
    },
    ('flash.part_recorded', 'flash'): {
        'en': 'Part recorded.',
        'pl': 'Część zarejestrowana.',
    },
    ('flash.duration_min_1', 'flash'): {
        'en': 'Duration must be at least 1 minute.',
        'pl': 'Czas trwania musi wynosić co najmniej 1 minutę.',
    },
    ('flash.time_logged', 'flash'): {
        'en': 'Time logged.',
        'pl': 'Czas zarejestrowany.',
    },

    # assets
    ('flash.property_name_required', 'flash'): {
        'en': 'Property name is required.',
        'pl': 'Nazwa majątku jest wymagana.',
    },
    ('flash.property_created', 'flash'): {
        'en': 'Property created successfully.',
        'pl': 'Majątek został utworzony pomyślnie.',
    },
    ('flash.asset_name_required', 'flash'): {
        'en': 'Asset name is required.',
        'pl': 'Nazwa zasobu jest wymagana.',
    },
    ('flash.property_updated', 'flash'): {
        'en': 'Property updated successfully.',
        'pl': 'Majątek został zaktualizowany pomyślnie.',
    },
    ('flash.no_property_selected', 'flash'): {
        'en': 'No property selected.',
        'pl': 'Nie wybrano majątku.',
    },

    # locations
    ('flash.location_name_required', 'flash'): {
        'en': 'Location name is required.',
        'pl': 'Nazwa lokalizacji jest wymagana.',
    },
    ('flash.location_created', 'flash'): {
        'en': 'Location created successfully.',
        'pl': 'Lokalizacja została utworzona pomyślnie.',
    },
    ('flash.location_updated', 'flash'): {
        'en': 'Location updated successfully.',
        'pl': 'Lokalizacja została zaktualizowana pomyślnie.',
    },
    ('flash.location_activated', 'flash'): {
        'en': 'Location activated.',
        'pl': 'Lokalizacja aktywowana.',
    },
    ('flash.location_deactivated', 'flash'): {
        'en': 'Location deactivated.',
        'pl': 'Lokalizacja dezaktywowana.',
    },

    # parts
    ('flash.part_name_required', 'flash'): {
        'en': 'Part name is required.',
        'pl': 'Nazwa części jest wymagana.',
    },
    ('flash.part_created', 'flash'): {
        'en': 'Part created successfully.',
        'pl': 'Część została utworzona pomyślnie.',
    },
    ('flash.part_updated', 'flash'): {
        'en': 'Part updated successfully.',
        'pl': 'Część została zaktualizowana pomyślnie.',
    },
    ('flash.linked_asset_to_part', 'flash'): {
        'en': 'Linked {asset} to {part}.',
        'pl': 'Powiązano {asset} z {part}.',
    },
    ('flash.removed_asset_from_part', 'flash'): {
        'en': 'Removed {asset} from {part}.',
        'pl': 'Usunięto {asset} z {part}.',
    },

    # admin - users
    ('flash.user_fields_required', 'flash'): {
        'en': 'Username, email, display name, and password are required.',
        'pl': 'Nazwa użytkownika, e-mail, nazwa wyświetlana i hasło są wymagane.',
    },
    ('flash.username_exists', 'flash'): {
        'en': 'Username already exists.',
        'pl': 'Nazwa użytkownika już istnieje.',
    },
    ('flash.email_exists', 'flash'): {
        'en': 'Email already exists.',
        'pl': 'Adres e-mail już istnieje.',
    },
    ('flash.user_created', 'flash'): {
        'en': "User '{username}' created successfully.",
        'pl': "Użytkownik '{username}' został utworzony pomyślnie.",
    },
    ('flash.user_fields_required_edit', 'flash'): {
        'en': 'Username, email, and display name are required.',
        'pl': 'Nazwa użytkownika, e-mail i nazwa wyświetlana są wymagane.',
    },
    ('flash.user_updated', 'flash'): {
        'en': "User '{username}' updated successfully.",
        'pl': "Użytkownik '{username}' został zaktualizowany pomyślnie.",
    },
    ('flash.cannot_deactivate_self', 'flash'): {
        'en': 'You cannot deactivate your own account.',
        'pl': 'Nie możesz dezaktywować własnego konta.',
    },
    ('flash.user_activated', 'flash'): {
        'en': "User '{username}' activated.",
        'pl': "Użytkownik '{username}' aktywowany.",
    },
    ('flash.user_deactivated', 'flash'): {
        'en': "User '{username}' deactivated.",
        'pl': "Użytkownik '{username}' dezaktywowany.",
    },
    ('flash.password_reset', 'flash'): {
        'en': "Password for '{username}' has been reset. Temporary password: {temp_password}",
        'pl': "Hasło dla '{username}' zostało zresetowane. Tymczasowe hasło: {temp_password}",
    },

    # admin - teams
    ('flash.team_name_required', 'flash'): {
        'en': 'Team name is required.',
        'pl': 'Nazwa zespołu jest wymagana.',
    },
    ('flash.team_created', 'flash'): {
        'en': "Team '{name}' created successfully.",
        'pl': "Zespół '{name}' został utworzony pomyślnie.",
    },
    ('flash.team_updated', 'flash'): {
        'en': "Team '{name}' updated successfully.",
        'pl': "Zespół '{name}' został zaktualizowany pomyślnie.",
    },

    # admin - sites
    ('flash.site_name_code_required', 'flash'): {
        'en': 'Site name and code are required.',
        'pl': 'Nazwa i kod obiektu są wymagane.',
    },
    ('flash.site_code_exists', 'flash'): {
        'en': 'Site code already exists.',
        'pl': 'Kod obiektu już istnieje.',
    },
    ('flash.site_created', 'flash'): {
        'en': "Site '{name}' created successfully.",
        'pl': "Obiekt '{name}' został utworzony pomyślnie.",
    },
    ('flash.site_updated', 'flash'): {
        'en': "Site '{name}' updated successfully.",
        'pl': "Obiekt '{name}' został zaktualizowany pomyślnie.",
    },

    # admin - settings
    ('flash.settings_saved', 'flash'): {
        'en': 'Settings saved.',
        'pl': 'Ustawienia zapisane.',
    },

    # ───────────────────────────────────────────────────────────────────
    #  REQUEST STATUSES  (status.request.*)
    # ───────────────────────────────────────────────────────────────────
    ('status.request.new', 'status'): {
        'en': 'New',
        'pl': 'Nowe',
    },
    ('status.request.acknowledged', 'status'): {
        'en': 'Acknowledged',
        'pl': 'Potwierdzone',
    },
    ('status.request.in_progress', 'status'): {
        'en': 'In Progress',
        'pl': 'W trakcie',
    },
    ('status.request.resolved', 'status'): {
        'en': 'Resolved',
        'pl': 'Rozwiązane',
    },
    ('status.request.closed', 'status'): {
        'en': 'Closed',
        'pl': 'Zamknięte',
    },
    ('status.request.cancelled', 'status'): {
        'en': 'Cancelled',
        'pl': 'Anulowane',
    },

    # ───────────────────────────────────────────────────────────────────
    #  WORK ORDER STATUSES  (status.wo.*)
    # ───────────────────────────────────────────────────────────────────
    ('status.wo.open', 'status'): {
        'en': 'Open',
        'pl': 'Otwarte',
    },
    ('status.wo.assigned', 'status'): {
        'en': 'Assigned',
        'pl': 'Przypisane',
    },
    ('status.wo.in_progress', 'status'): {
        'en': 'In Progress',
        'pl': 'W trakcie',
    },
    ('status.wo.on_hold', 'status'): {
        'en': 'On Hold',
        'pl': 'Wstrzymane',
    },
    ('status.wo.completed', 'status'): {
        'en': 'Completed',
        'pl': 'Zakończone',
    },
    ('status.wo.closed', 'status'): {
        'en': 'Closed',
        'pl': 'Zamknięte',
    },
    ('status.wo.cancelled', 'status'): {
        'en': 'Cancelled',
        'pl': 'Anulowane',
    },

    # ───────────────────────────────────────────────────────────────────
    #  PRIORITY LABELS  (status.priority.*)
    # ───────────────────────────────────────────────────────────────────
    ('status.priority.low', 'status'): {
        'en': 'Low',
        'pl': 'Niski',
    },
    ('status.priority.medium', 'status'): {
        'en': 'Medium',
        'pl': 'Średni',
    },
    ('status.priority.high', 'status'): {
        'en': 'High',
        'pl': 'Wysoki',
    },
    ('status.priority.critical', 'status'): {
        'en': 'Critical',
        'pl': 'Krytyczny',
    },

    # ───────────────────────────────────────────────────────────────────
    #  ASSET STATUSES  (status.asset.*)
    # ───────────────────────────────────────────────────────────────────
    ('status.asset.operational', 'status'): {
        'en': 'Operational',
        'pl': 'Sprawny',
    },
    ('status.asset.needs_repair', 'status'): {
        'en': 'Needs Repair',
        'pl': 'Wymaga naprawy',
    },
    ('status.asset.out_of_service', 'status'): {
        'en': 'Out of Service',
        'pl': 'Wyłączony z użytku',
    },
    ('status.asset.decommissioned', 'status'): {
        'en': 'Decommissioned',
        'pl': 'Wycofany',
    },

    # ───────────────────────────────────────────────────────────────────
    #  ASSET CRITICALITIES  (status.criticality.*)
    # ───────────────────────────────────────────────────────────────────
    ('status.criticality.low', 'status'): {
        'en': 'Low',
        'pl': 'Niska',
    },
    ('status.criticality.medium', 'status'): {
        'en': 'Medium',
        'pl': 'Średnia',
    },
    ('status.criticality.high', 'status'): {
        'en': 'High',
        'pl': 'Wysoka',
    },
    ('status.criticality.critical', 'status'): {
        'en': 'Critical',
        'pl': 'Krytyczna',
    },

    # ───────────────────────────────────────────────────────────────────
    #  ROLE LABELS  (label.role.*)
    # ───────────────────────────────────────────────────────────────────
    ('label.role.user', 'label'): {
        'en': 'User',
        'pl': 'Użytkownik',
    },
    ('label.role.contractor', 'label'): {
        'en': 'Contractor',
        'pl': 'Wykonawca',
    },
    ('label.role.technician', 'label'): {
        'en': 'Technician',
        'pl': 'Technik',
    },
    ('label.role.supervisor', 'label'): {
        'en': 'Supervisor',
        'pl': 'Przełożony',
    },
    ('label.role.admin', 'label'): {
        'en': 'Admin',
        'pl': 'Administrator',
    },

    # ───────────────────────────────────────────────────────────────────
    #  WORK ORDER TYPE LABELS  (label.wo_type.*)
    # ───────────────────────────────────────────────────────────────────
    ('label.wo_type.corrective', 'label'): {
        'en': 'Corrective',
        'pl': 'Korekcyjne',
    },
    ('label.wo_type.preventive', 'label'): {
        'en': 'Preventive',
        'pl': 'Prewencyjne',
    },
    ('label.wo_type.inspection', 'label'): {
        'en': 'Inspection',
        'pl': 'Inspekcja',
    },
    ('label.wo_type.emergency', 'label'): {
        'en': 'Emergency',
        'pl': 'Awaryjne',
    },

    # ───────────────────────────────────────────────────────────────────
    #  LOCATION TYPE LABELS  (label.location_type.*)
    # ───────────────────────────────────────────────────────────────────
    ('label.location_type.building', 'label'): {
        'en': 'Building',
        'pl': 'Budynek',
    },
    ('label.location_type.floor', 'label'): {
        'en': 'Floor',
        'pl': 'Piętro',
    },
    ('label.location_type.area', 'label'): {
        'en': 'Area',
        'pl': 'Obszar',
    },
    ('label.location_type.room', 'label'): {
        'en': 'Room',
        'pl': 'Pomieszczenie',
    },

    # ───────────────────────────────────────────────────────────────────
    #  ASSET CATEGORY LABELS  (label.category.*)
    # ───────────────────────────────────────────────────────────────────
    ('label.category.machine', 'label'): {
        'en': 'Machine',
        'pl': 'Maszyna',
    },
    ('label.category.tool', 'label'): {
        'en': 'Tool',
        'pl': 'Narzędzie',
    },
    ('label.category.vehicle', 'label'): {
        'en': 'Vehicle',
        'pl': 'Pojazd',
    },
    ('label.category.building', 'label'): {
        'en': 'Building',
        'pl': 'Budynek',
    },

    # ───────────────────────────────────────────────────────────────────
    #  UNIT LABELS  (label.unit.*)
    # ───────────────────────────────────────────────────────────────────
    ('label.unit.each', 'label'): {
        'en': 'Each',
        'pl': 'Sztuka',
    },
    ('label.unit.meter', 'label'): {
        'en': 'Meter',
        'pl': 'Metr',
    },
    ('label.unit.liter', 'label'): {
        'en': 'Liter',
        'pl': 'Litr',
    },
    ('label.unit.kg', 'label'): {
        'en': 'Kg',
        'pl': 'Kg',
    },
    ('label.unit.set', 'label'): {
        'en': 'Set',
        'pl': 'Komplet',
    },
    ('label.unit.pair', 'label'): {
        'en': 'Pair',
        'pl': 'Para',
    },
    ('label.unit.box', 'label'): {
        'en': 'Box',
        'pl': 'Pudełko',
    },

    # ───────────────────────────────────────────────────────────────────
    #  RELATIVE DATE STRINGS  (filter.date.*)
    # ───────────────────────────────────────────────────────────────────
    ('filter.date.today', 'filter'): {
        'en': 'Today',
        'pl': 'Dzisiaj',
    },
    ('filter.date.yesterday', 'filter'): {
        'en': 'Yesterday',
        'pl': 'Wczoraj',
    },
    ('filter.date.tomorrow', 'filter'): {
        'en': 'Tomorrow',
        'pl': 'Jutro',
    },
    ('filter.date.days_ago', 'filter'): {
        'en': '{count} days ago',
        'pl': '{count} dni temu',
    },
    ('filter.date.in_days', 'filter'): {
        'en': 'In {count} days',
        'pl': 'Za {count} dni',
    },

    # ───────────────────────────────────────────────────────────────────
    #  SUPPLIER MODULE
    # ───────────────────────────────────────────────────────────────────
    ('ui.navbar.suppliers', 'ui'): {
        'en': 'Suppliers',
        'pl': 'Dostawcy',
    },
    ('ui.page.suppliers', 'ui'): {
        'en': 'Suppliers',
        'pl': 'Dostawcy',
    },
    ('ui.page.new_supplier', 'ui'): {
        'en': 'New Supplier',
        'pl': 'Nowy dostawca',
    },
    ('ui.page.edit_supplier', 'ui'): {
        'en': 'Edit Supplier',
        'pl': 'Edytuj dostawcę',
    },
    ('ui.label.contact_person', 'ui'): {
        'en': 'Contact Person',
        'pl': 'Osoba kontaktowa',
    },
    ('ui.label.address', 'ui'): {
        'en': 'Address',
        'pl': 'Adres',
    },
    ('ui.label.shop_url', 'ui'): {
        'en': 'Online Shop URL',
        'pl': 'Adres sklepu internetowego',
    },
    ('ui.label.supplier_information', 'ui'): {
        'en': 'Supplier Information',
        'pl': 'Informacje o dostawcy',
    },
    ('ui.label.none', 'ui'): {
        'en': 'None',
        'pl': 'Brak',
    },
    ('ui.label.parts', 'ui'): {
        'en': 'Parts',
        'pl': 'Części',
    },
    ('ui.label.stock', 'ui'): {
        'en': 'Stock',
        'pl': 'Zapas',
    },
    ('ui.label.activate', 'ui'): {
        'en': 'Activate',
        'pl': 'Aktywuj',
    },
    ('ui.label.deactivate', 'ui'): {
        'en': 'Deactivate',
        'pl': 'Dezaktywuj',
    },
    ('ui.button.new_supplier', 'ui'): {
        'en': 'New Supplier',
        'pl': 'Nowy dostawca',
    },
    ('ui.button.create_supplier', 'ui'): {
        'en': 'Create Supplier',
        'pl': 'Utwórz dostawcę',
    },
    ('ui.button.back_to_suppliers', 'ui'): {
        'en': 'Back to Suppliers',
        'pl': 'Powrót do dostawców',
    },
    ('ui.button.order_online', 'ui'): {
        'en': 'Order Online',
        'pl': 'Zamów online',
    },
    ('ui.text.search_suppliers_placeholder', 'ui'): {
        'en': 'Search by name, contact, or email...',
        'pl': 'Szukaj po nazwie, kontakcie lub emailu...',
    },
    ('ui.text.no_suppliers_found', 'ui'): {
        'en': 'No suppliers found.',
        'pl': 'Nie znaleziono dostawców.',
    },
    ('ui.text.no_parts_from_supplier', 'ui'): {
        'en': 'No parts linked to this supplier yet.',
        'pl': 'Brak części przypisanych do tego dostawcy.',
    },
    ('ui.text.parts_from_supplier', 'ui'): {
        'en': 'Parts from this Supplier',
        'pl': 'Części od tego dostawcy',
    },
    ('ui.text.shop_url_hint', 'ui'): {
        'en': 'Link to supplier online shop or ordering system',
        'pl': 'Link do sklepu internetowego lub systemu zamówień dostawcy',
    },
    ('ui.text.supplier_notes_placeholder', 'ui'): {
        'en': 'e.g. Account number, payment terms, delivery notes...',
        'pl': 'np. Numer konta, warunki płatności, uwagi do dostaw...',
    },
    ('ui.text.parts_below_minimum', 'ui'): {
        'en': 'parts below minimum stock level',
        'pl': 'części poniżej minimalnego poziomu zapasu',
    },

    # ───────────────────────────────────────────────────────────────────
    #  HELP PAGES  (ui.help.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.help.index', 'ui'): {
        'en': 'Help Centre',
        'pl': 'Centrum pomocy',
    },
    ('ui.help.getting_started', 'ui'): {
        'en': 'Getting Started',
        'pl': 'Rozpoczęcie pracy',
    },
    ('ui.help.reporting', 'ui'): {
        'en': 'Reporting Problems',
        'pl': 'Zgłaszanie problemów',
    },
    ('ui.help.requests', 'ui'): {
        'en': 'Managing Requests',
        'pl': 'Zarządzanie zgłoszeniami',
    },
    ('ui.help.work_orders', 'ui'): {
        'en': 'Work Orders',
        'pl': 'Zlecenia pracy',
    },
    ('ui.help.property', 'ui'): {
        'en': 'Property Management',
        'pl': 'Zarządzanie majątkiem',
    },
    ('ui.help.admin_guide', 'ui'): {
        'en': 'Admin Guide',
        'pl': 'Przewodnik administratora',
    },
    ('ui.help.faq', 'ui'): {
        'en': 'FAQ',
        'pl': 'Najczęściej zadawane pytania',
    },

    # ───────────────────────────────────────────────────────────────────
    #  MISC / TIME UNITS  (ui.time.*)
    # ───────────────────────────────────────────────────────────────────
    ('ui.time.min', 'ui'): {
        'en': 'min',
        'pl': 'min',
    },
    ('ui.time.hrs', 'ui'): {
        'en': 'hrs',
        'pl': 'godz.',
    },
    ('ui.time.minutes', 'ui'): {
        'en': 'minutes',
        'pl': 'minut',
    },
    ('ui.time.hours', 'ui'): {
        'en': 'hours',
        'pl': 'godzin',
    },
}

# ═══════════════════════════════════════════════════════════════════════
#  SEED LOGIC
# ═══════════════════════════════════════════════════════════════════════

with app.app_context():
    added = 0
    skipped = 0
    for (key, category), values in TRANSLATIONS.items():
        for lang, value in values.items():
            exists = Translation.query.filter_by(key=key, language=lang).first()
            if not exists:
                t = Translation(
                    key=key, language=lang, value=value, category=category
                )
                db.session.add(t)
                added += 1
            else:
                skipped += 1
    db.session.commit()

    unique_keys = len(TRANSLATIONS)
    total_entries = sum(len(v) for v in TRANSLATIONS.values())
    print(f"Translation keys defined: {unique_keys}")
    print(f"Translations seeded: {added} added, {skipped} already existed")
    print(f"Total entries in DB:  {total_entries}")
