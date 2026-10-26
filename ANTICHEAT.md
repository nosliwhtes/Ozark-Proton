# Anti-cheat and Ozark-Proton

Some games' anti-cheat decides whether they run on Linux, not Proton. The developer has to turn on
Proton support in the anti-cheat's settings. If they don't, or if they turn it off later, no Proton
build can fix that: not Ozark, not GE, not Valve's.

## Games in this library

The first three entries use [AreWeAntiCheatYet](https://areweanticheatyet.com), checked
2026-09-26. The HQ entry uses Valve and Activision evidence checked 2026-10-25, below.
These are external support reports, not Ozark gameplay results.

| AppID | Game | Anti-cheat | Reported support | In smoke test |
|---|---|---|---|---|
| 553850 | HELLDIVERS 2 | nProtect GameGuard | Running | Skipped |
| 2479810 | Gray Zone Warfare | Easy Anti-Cheat + AnyBrain | Running | Skipped |
| 1144200 | Ready or Not | (not listed) | — | Skipped |
| 1938090 | Call of Duty HQ (including Modern Warfare 4) | RICOCHET | Unsupported anti-cheat (Valve) | Skipped |

The smoke test skips these titles even when their app IDs are supplied explicitly. Repeated
unattended launch/stop cycles cannot establish anti-cheat compatibility. A skipped entry is
not a passing gameplay test.

Gray Zone Warfare has an upstream protonfix: it makes two EAC-checked cache files read-only so the
game can't change them and fail EAC's check.

## Call of Duty HQ / Modern Warfare 4

The October 25 investigation identified app `1938090` and an installed executable whose
metadata names Modern Warfare 4 SP. This is separate from the original Call of Duty 4
(app `7940`). Retained October 24 bootstrapper logs report four failures starting
`atvi-randgrid_sr` with error `1114`. The registered kernel-driver service points to an
existing `Randgrid.sys` through a valid drive mapping. Static inspection found Windows
kernel imports; it did not identify the exact failing initialization instruction or prove
file integrity.

[Valve's app-specific report](https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport?nAppID=1938090)
flags unsupported anti-cheat for SteamOS and Steam Deck.
[Activision's RICOCHET overview](https://support.activision.com/articles/ricochet-overview)
lists MW4 and requires its kernel driver for protected PC games.
[Valve's Proton documentation](https://partner.steamgames.com/doc/steamhardware/proton)
describes kernel-space anti-cheat as unsupported.

No supported Ozark runtime repair or successful gameplay was established. The investigation
did not launch the game or alter its files, prefix or services. The smoke-test exclusion
prevents automated retries; it does not change normal Steam launches. Do not treat error
1114 as proof of a missing ordinary DLL or add speculative service/driver overrides.
GE11-11's Call of Duty (2003) fix and GE11-10's Ghosts fix concern different games and do
not establish HQ/MW4 support.

## If an anti-cheat game stops launching

1. Check its AreWeAntiCheatYet page and SteamDB news. Most breaks come from a game or anti-cheat
   update, not Proton.
2. Try stock GE-Proton (Properties → Compatibility). If GE fails too, the problem isn't in Ozark.
3. If only Ozark fails, pin the game to GE and open an issue with `PROTON_LOG=1` output.

Never add a gamefix that edits anti-cheat files or gets around it. That can get the account banned.
