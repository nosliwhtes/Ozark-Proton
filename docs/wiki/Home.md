# Ozark-Proton

Ozark-Proton is an unofficial, experimental fork of [GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom). It includes newer DXVK and VKD3D-Proton revisions than GE-Proton11-7 and focuses on an NVIDIA RTX 5080 on Linux. Valve and GloriousEggroll do not make or support Ozark; report Ozark problems to [this repository](https://github.com/nosliwhtes/Ozark-Proton/issues), not to them.

Keep stock GE-Proton installed as a fallback. Ozark's README says its game compatibility and performance have not been tested. A patch being present is not proof that a game works or runs faster.

## Install

1. Download the `Ozark-Proton<version>.tar.gz` release tarball and its matching `.sha512sum` file from [Releases](https://github.com/nosliwhtes/Ozark-Proton/releases).
2. In the download folder, verify the checksum before extracting:
   ```sh
   sha512sum -c Ozark-Proton<version>.sha512sum
   ```
   Replace `<version>` with the exact version you downloaded. Continue only if the check reports `OK`.
3. Create the compatibility tools folder if needed, then extract the tarball into it:
   - Regular Steam: `~/.steam/steam/compatibilitytools.d/`
   - Flatpak Steam: `~/.var/app/com.valvesoftware.Steam/.steam/steam/compatibilitytools.d/`

   The repository README documents the Flatpak data-directory form, `~/.var/app/com.valvesoftware.Steam/data/Steam/compatibilitytools.d/`. Use the path that belongs to your Steam installation; do not create a second Steam data directory just to install Ozark.
4. Restart Steam.
5. Right-click the game, open **Properties → Compatibility**, enable **Force the use of a specific Steam Play compatibility tool**, and select the installed Ozark version.

If a game regresses, select stock GE-Proton in the same menu.

## Settings and opt-in tuning

The fork's defaults are in [`user_settings.py`](https://github.com/nosliwhtes/Ozark-Proton/blob/master/user_settings.py). The README documents enabled NVAPI and NVIDIA shader-cache defaults; launch options override those defaults. Extra tuning, native Wayland, upscaler downloads, and diagnostic logging should be enabled per game only when needed, not assumed to improve every game.

For an Ozark diagnostic log, add `OZARK_TEST=1 %command%` to that game's launch options. Logs go to `~/ozark-logs/steam-<appid>.log`; logging is off otherwise. Remove the option when finished. See the [README settings](https://github.com/nosliwhtes/Ozark-Proton/blob/master/README.md#settings) for details.

## Compatibility

See [Compatibility](Compatibility.md) for the starter table and reporting instructions. Anti-cheat support is vendor-controlled; a newer Proton build cannot enable support that a game developer has disabled.

These pages are based on the repository's [README](https://github.com/nosliwhtes/Ozark-Proton/blob/master/README.md) and [anti-cheat notes](https://github.com/nosliwhtes/Ozark-Proton/blob/master/ANTICHEAT.md), not on new game tests.

## Publishing these pages

GitHub has not initialized this repository's Wiki yet. A maintainer must create and save one first page through the [Wiki web UI](https://github.com/nosliwhtes/Ozark-Proton/wiki). After that, clone `https://github.com/nosliwhtes/Ozark-Proton.wiki.git`, copy `Home.md` and `Compatibility.md` from `docs/wiki/`, and commit and push them to the Wiki repository. Change the relative Compatibility link above to `Compatibility` when publishing on GitHub Wiki.
