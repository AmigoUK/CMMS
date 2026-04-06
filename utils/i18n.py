"""Database-driven translation engine for CMMS."""

from flask import g, has_request_context

_cache = {}  # {language: {key: value}}


def load_translations(language):
    """Load all translations for a language into memory."""
    if language in _cache:
        return _cache[language]
    from models.translation import Translation
    rows = Translation.query.filter_by(language=language).all()
    _cache[language] = {r.key: r.value for r in rows}
    return _cache[language]


def invalidate_cache():
    """Clear the translation cache. Called when admin edits translations."""
    _cache.clear()


def get_current_language():
    """Get the current language from the request context."""
    if has_request_context():
        return getattr(g, "language", "en")
    return "en"


def translate(key, **kwargs):
    """Look up a translation key. Falls back to English, then to the key itself.

    Usage in templates: {{ _('ui.navbar.dashboard') }}
    Usage in Python:    _('flash.saved', name='Widget')
    """
    lang = get_current_language()

    # Look up in current language
    translations = load_translations(lang)
    text = translations.get(key)

    # Fall back to English
    if text is None and lang != "en":
        en = load_translations("en")
        text = en.get(key)

    # Ultimate fallback: the key itself (formatted nicely)
    if text is None:
        # Convert key like 'ui.navbar.dashboard' to 'Dashboard'
        text = key.rsplit(".", 1)[-1].replace("_", " ").title()

    # Apply format placeholders
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass  # If formatting fails, return unformatted

    return text
