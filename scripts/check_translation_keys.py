"""Find translation keys used in templates but not present in any seed file.

Used as a CI guard against the historical class of bugs where a template
renders `{{ _('ui.button.something') }}` but no seed file defines that
key, so the i18n fallback chain emits an English title-case string and
breaks Polish UX (utils/i18n.py:30-59).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
BASELINE = ROOT / "tests" / "i18n_keys_baseline.txt"

SEED_KEY = re.compile(r"""\(\s*['"]([\w.]+)['"]\s*,\s*['"]\w+['"]\s*\)\s*:""")
TEMPLATE_USAGE = re.compile(r"""_\(\s*['"]([\w.]+)['"]""")


def seeded_keys() -> set[str]:
    keys: set[str] = set()
    for seed_file in ROOT.glob("seed_translations*.py"):
        text = seed_file.read_text(encoding="utf-8")
        keys.update(SEED_KEY.findall(text))
    return keys


def used_keys() -> set[str]:
    keys: set[str] = set()
    for tpl in TEMPLATES.rglob("*.html"):
        text = tpl.read_text(encoding="utf-8")
        keys.update(TEMPLATE_USAGE.findall(text))
    return keys


def find_unseeded() -> list[str]:
    used = used_keys()
    # Skip dynamic prefixes: `_('label.role.' + r)` matches as `label.role.`,
    # but the real keys (`label.role.admin`, ...) are individually seeded.
    real_keys = {k for k in used if not k.endswith(".")}
    return sorted(real_keys - seeded_keys())


def baseline_keys() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {
        line.strip()
        for line in BASELINE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def find_new_unseeded() -> list[str]:
    """Unseeded keys that are NOT in the historical baseline.

    The baseline file (tests/i18n_keys_baseline.txt) lists the pre-existing
    debt of unseeded keys; this returns only keys introduced after that
    snapshot. CI fails on these.
    """
    return sorted(set(find_unseeded()) - baseline_keys())


def main() -> int:
    missing = find_unseeded()
    if missing:
        print(
            f"{len(missing)} translation keys used in templates but not "
            f"seeded in any seed_translations*.py:",
        )
        for key in missing:
            print(f"  - {key}")
        return 1
    print(f"OK - all {len(used_keys())} template translation keys are seeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
