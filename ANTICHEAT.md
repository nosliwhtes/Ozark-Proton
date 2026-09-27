# Anti-cheat and Ozark-Proton

Some games' anti-cheat decides whether they run on Linux, not Proton. The developer has to turn on
Proton support in the anti-cheat's settings. If they don't, or if they turn it off later, no Proton
build can fix that: not Ozark, not GE, not Valve's.

## Games in this library

Status from [AreWeAntiCheatYet](https://areweanticheatyet.com), checked 2026-09-26.

| AppID | Game | Anti-cheat | AWACY status | In smoke test |
|---|---|---|---|---|
| 553850 | HELLDIVERS 2 | nProtect GameGuard | Running | Skipped |
| 2479810 | Gray Zone Warfare | Easy Anti-Cheat + AnyBrain | Running | Skipped |
| 1144200 | Ready or Not | (not listed) | — | Skipped |

The smoke test skips these three because they're online-only. Repeatedly starting and killing them
tests the servers and the anti-cheat handshake, not Proton, and it could look suspicious to the
anti-cheat. Test them by hand after a release.

Gray Zone Warfare has an upstream protonfix: it makes two EAC-checked cache files read-only so the
game can't change them and fail EAC's check.

## If an anti-cheat game stops launching

1. Check its AreWeAntiCheatYet page and SteamDB news. Most breaks come from a game or anti-cheat
   update, not Proton.
2. Try stock GE-Proton (Properties → Compatibility). If GE fails too, the problem isn't in Ozark.
3. If only Ozark fails, pin the game to GE and open an issue with `PROTON_LOG=1` output.

Never add a gamefix that edits anti-cheat files or gets around it. That can get the account banned.
