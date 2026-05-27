"""Guard: every `_('key')` in templates must exist in a seed file.

Catches the historical pattern where a developer adds a template string
without the matching seed entry, which silently degrades to an English
title-case fallback (see utils/i18n.py:30-59).

The historical baseline of 179 unseeded keys was cleared in PRs #8, #9
and the closing sweep batch. From now on this is a hard gate: every
new key must ship with a seed entry.
"""

from scripts.check_translation_keys import find_unseeded


def test_every_template_key_has_a_seed_entry():
    missing = find_unseeded()
    assert not missing, (
        "Translation keys used in templates but not seeded in any "
        "seed_translations*.py:\n  - " + "\n  - ".join(missing)
    )
