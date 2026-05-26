"""Guard: every `_('key')` in templates must exist in a seed file.

Catches the historical pattern where a developer adds a template string
without the matching seed entry, which silently degrades to an English
title-case fallback (see utils/i18n.py:30-59).
"""

from scripts.check_translation_keys import find_new_unseeded


def test_no_new_unseeded_translation_keys():
    """Fail when a template uses a `_('key')` not present in any seed file.

    A baseline file (tests/i18n_keys_baseline.txt) captures the pre-existing
    debt of unseeded keys, so this test gates only NEW additions. To clear
    a key from the baseline, add the matching entry to a seed_translations*
    file, then run `uv run python scripts/check_translation_keys.py` to
    confirm and trim the baseline.
    """
    missing = find_new_unseeded()
    assert not missing, (
        "New translation keys used in templates but not seeded in any "
        "seed_translations*.py:\n  - " + "\n  - ".join(missing)
    )
