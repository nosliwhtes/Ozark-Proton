# Compatibility

This is a starter table, not a certification list. No games were launched to create it. The Ozark README says compatibility and performance have not been tested; its inherited GE-Proton "Tested games" table is not evidence of Ozark results.

## Status meanings

- **Works**: a report confirms the stated Ozark version works in the described scenario.
- **Issues**: a report describes a reproducible problem on that Ozark version.
- **Broken**: a report confirms the stated version cannot run the reported scenario.
- **Untested**: there is no documented Ozark test result for that game and version.

Do not turn an upstream compatibility claim, an installed game, or a shipped gamefix into a Works result. Add the tested Ozark version and a report link when updating a row. "Not tested" below means no Ozark version has been verified for that row.

| Game | AppID | Ozark version | Status (Works/Issues/Broken/Untested) | Notes |
| --- | --- | --- | --- | --- |
| HELLDIVERS 2 | 553850 | Not tested | Untested | ANTICHEAT.md records AreWeAntiCheatYet as Running on 2026-09-26, with nProtect GameGuard. That is an external Linux-support status, not an Ozark test. Skipped by the automated smoke test. |
| Gray Zone Warfare | 2479810 | Not tested | Untested | ANTICHEAT.md records AreWeAntiCheatYet as Running on 2026-09-26, with Easy Anti-Cheat + AnyBrain. It also documents an upstream protonfix. Neither is proof of Ozark compatibility. Skipped by the automated smoke test. |
| Ready or Not | 1144200 | Not tested | Untested | ANTICHEAT.md lists no tracker status or anti-cheat entry and says the smoke test skips it as an online-only title. No Ozark result is documented. |
| Warframe | 230410 | Not tested | Untested | The README's inherited GE notes warn about Auto VSync, unlimited frame rate, and NVIDIA GPU-particle freezes. These are upstream cautions, not an Ozark test result. |

The README also documents a Cult of the Lamb gamefix that loads the game's `winhttp.dll` first for BepInEx mods. This documents the intended fix, not a confirmed compatibility result.

## Report a result or problem

1. Search [existing issues](https://github.com/nosliwhtes/Ozark-Proton/issues) for the game and AppID.
2. Open the repository's [Compatibility Report template](https://github.com/nosliwhtes/Ozark-Proton/issues/new?template=compatibility-report.md). Its source is [`.github/ISSUE_TEMPLATE/compatibility-report.md`](https://github.com/nosliwhtes/Ozark-Proton/blob/master/.github/ISSUE_TEMPLATE/compatibility-report.md).
3. Give the game name, Steam AppID, exact Ozark release, GPU and driver, kernel, distribution, and desktop session. Include exact launch options, symptoms, and steps to reproduce. For a working result, state what you actually tested: launch, gameplay, videos, multiplayer, or controller input.
4. Compare with stock GE-Proton and, as the template requests, Proton Experimental and Valve stable. State the versions and results, or write "not tested"; do not tick a confirmation you cannot support. Note any clean-prefix limitation, DRM activation limit, or mods. The inherited template says GE-Proton in several places; identify clearly whether the problem occurs only on Ozark.
5. Attach a Proton log: use `PROTON_LOG=1 %command%` and attach `~/steam-<appid>.log`, or use the fork's `OZARK_TEST=1 %command%` and attach `~/ozark-logs/steam-<appid>.log`. Remove logging afterwards, and review logs and system reports for private information before posting.

Report Ozark-only regressions to this fork and keep stock GE as the fallback. If the same problem occurs on Proton Experimental, follow the template's guidance for [Valve's Proton tracker](https://github.com/ValveSoftware/Proton/issues); do not present it as an Ozark-only bug.

## Anti-cheat limits

Anti-cheat titles are **vendor-controlled**. Game developers must enable and maintain Linux/Proton support. An AreWeAntiCheatYet Running status does not guarantee that a particular Ozark version works, and the snapshot above may change after a vendor update.

See [ANTICHEAT.md](https://github.com/nosliwhtes/Ozark-Proton/blob/master/ANTICHEAT.md) for the repository's documented snapshot and reporting advice. Do not edit or bypass anti-cheat files. The repository skips its listed online-only titles in automated smoke tests; repeated unattended launches and kills are not compatibility evidence.
