"""Cult of the Lamb (Ozark local fix)

Load a game-folder winhttp.dll (BepInEx mod loader) before Wine's builtin.
Harmless when no winhttp.dll is present: Wine falls back to builtin.
Pinned here so a prefix rebuild can't silently drop the override.
"""

from protonfixes import util


def main() -> None:
    """Prefer native winhttp for mod loader support"""
    util.winedll_override('winhttp', util.OverrideOrder.NATIVE_BUILTIN)
