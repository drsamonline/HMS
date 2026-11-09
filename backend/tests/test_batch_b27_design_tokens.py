"""Gate tests for build-plan batch B27: design tokens.

The interface carried its own values: eleven shades of blue-grey, six surface tints
and four shadows, none named. A change to "the border colour" meant finding
fourteen hex codes and hoping they were all the border.

Two properties are testable and worth testing:

* no colour is written literally in the application stylesheet - everything comes
  from a token, so a redesign touches one file;
* every token referenced exists, and every foreground/background pair the interface
  actually uses meets WCAG AA contrast.

The second is the one that matters clinically: grey-on-grey is the classic way a
hospital interface becomes unreadable on a ward monitor.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "frontend" / "css"
TOKENS = CSS / "tokens.css"
APP = CSS / "app.css"
ENTRY = ROOT / "frontend" / "index.html"

#: Print styles are deliberately black on white for paper, and are exempt.
PRINT_EXEMPT = {"print.css"}

COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)")
TOKEN_DEF = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
TOKEN_USE = re.compile(r"var\((--[a-z0-9-]+)\)")


def _tokens() -> dict[str, str]:
    return {
        name: value.strip()
        for name, value in TOKEN_DEF.findall(TOKENS.read_text(encoding="utf-8"))
    }


# ------------------------------------------------------------------ structure
def test_the_token_stylesheet_is_linked_before_the_app_stylesheet() -> None:
    """A token used before it is defined resolves to nothing."""

    html = ENTRY.read_text(encoding="utf-8")
    tokens_at = html.index("tokens.css")
    app_at = html.index("app.css")
    assert tokens_at < app_at, "tokens.css must be loaded before app.css"


def test_every_category_of_token_is_defined() -> None:
    tokens = _tokens()
    required = {
        "surface": "--surface-page",
        "panel": "--surface-panel",
        "ink": "--ink",
        "strong ink": "--ink-strong",
        "muted ink": "--ink-muted",
        "border": "--border",
        "danger": "--state-danger-ink",
        "spacing": "--space-4",
        "type": "--text-base",
        "radius": "--radius-md",
    }
    missing = {label: name for label, name in required.items() if name not in tokens}
    assert not missing, f"tokens missing: {missing}"


def test_no_colour_is_written_literally_in_the_app_stylesheet() -> None:
    """Everything comes from a token, so a redesign touches one file."""

    literal = COLOUR.findall(APP.read_text(encoding="utf-8"))
    assert not literal, (
        f"app.css still carries literal colours: {sorted(set(literal))}. "
        "Add a token to tokens.css and use it."
    )


def test_every_token_referenced_is_defined() -> None:
    """A var() with no definition resolves to nothing, silently."""

    tokens = _tokens()
    used = set(TOKEN_USE.findall(APP.read_text(encoding="utf-8")))
    undefined = used - set(tokens)
    assert not undefined, f"app.css uses undefined tokens: {sorted(undefined)}"


def test_every_colour_token_is_used() -> None:
    """An unused colour token is a shade nobody chose.

    Colour is fully tokenised, so every colour token must be referenced. The
    spacing, type, radius and shadow scales are a different matter: they are
    defined now and applied as the interface is rebuilt in the rest of wave 6, so
    they are allowed to be defined before they are used - stated here rather than
    quietly exempted.
    """

    tokens = _tokens()
    used = set(TOKEN_USE.findall(APP.read_text(encoding="utf-8")))

    reserved_prefixes = (
        "--space-", "--text-", "--leading-", "--radius-", "--shadow-",
        "--layer-", "--font-",
    )
    colour_tokens = {
        name
        for name, value in tokens.items()
        if not name.startswith(reserved_prefixes)
    }
    orphans = colour_tokens - used
    assert not orphans, f"colour tokens defined and never used: {sorted(orphans)}"


# ------------------------------------------------------------------- contrast
def _rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        srgb = value / 255
        return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(component) for component in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(foreground: str, background: str) -> float:
    light, dark = sorted(
        (_luminance(_rgb(foreground)), _luminance(_rgb(background))), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


#: The pairs the interface actually renders. AA for normal text is 4.5:1.
PAIRS = [
    ("--ink", "--surface-panel"),
    ("--ink", "--surface-page"),
    ("--ink-strong", "--surface-panel"),
    ("--ink-muted", "--surface-panel"),
    ("--ink-faint", "--surface-panel"),
    ("--ink-on-brand", "--surface-brand"),
    ("--ink-link", "--surface-panel"),
    ("--state-danger-ink", "--state-danger-surface"),
]


def test_every_text_pair_meets_wcag_aa() -> None:
    """Grey-on-grey is how a hospital interface becomes unreadable on a ward."""

    tokens = _tokens()
    failures = []
    for foreground, background in PAIRS:
        ratio = _contrast(tokens[foreground], tokens[background])
        if ratio < 4.5:
            failures.append(f"{foreground} on {background}: {ratio:.2f}:1")
    assert not failures, f"below AA (4.5:1): {failures}"


def test_the_contrast_helper_agrees_with_known_values() -> None:
    """A contrast test that always passes is worse than none."""

    assert _contrast("#000000", "#ffffff") == pytest.approx(21, rel=1e-3)
    assert _contrast("#ffffff", "#ffffff") == pytest.approx(1, rel=1e-3)


import pytest  # noqa: E402 - used by the helper test above
