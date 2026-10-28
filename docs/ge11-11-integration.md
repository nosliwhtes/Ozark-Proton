# GE-Proton11-11 integration

This document records the October 25 release integration. The subsequent
[October 28 update](upstream-sync-2026-10-28.md) includes later, unreleased GE
changes and a newer merged protonfixes revision.

This source update merges the [official GE-Proton11-11 release](https://github.com/GloriousEggroll/proton-ge-custom/releases/tag/GE-Proton11-11)
(`c0c2ee35e6d4d3bff4d39c6246ac46636434feb8`) into Ozark master
`85386425b3997fc6f01982bdb3865b7395276671`. It retains both histories.
`VERSION` is now `GE-Proton11-11`; later, unreleased GE master changes are excluded.
This is a source integration, not a published or installed Ozark runtime.

## Components

| Component | Integrated revision |
|---|---|
| Wine | `c53678ab22a85f0fad3588dd34f0452a463bd015` |
| DXVK | `2cb40186c43d617b5bd349a3756721aa4bd24b6d` |
| VKD3D-Proton | `0bb64c56c8f0dcc11ecc0f6c56e00e4f7bd8d506` |
| D7VK | `bcd66d0c95e7530e3b24bdab1ee5e7aae7131059` |
| FEX | `741e146fdf5a89517e1a67e3c899907cfba6131a` |
| Ozark protonfixes merge | `e6082b5b696be86972c066e0f080c70ca464cf00` |

The protonfixes merge combines Ozark `a760c4f882d513d8658fccf483ccc3af607343e5`
with the release's upstream pin `f4940924eefd2c973f5ec57dac26aa3dcefb33ca`.
Its URL remains `nosliwhtes/umu-protonfixes`. Missing-stage handling, early-stage
exception handling, line-ending normalization and the dependency-free smoke test
remain present. The new dependency commit must be made available in that fork
before a remote checkout/build can use the superproject update.

## Ozark behavior retained

The integration preserves the shipped settings and Cult of the Lamb override,
distribution-copy rules, URL decoder fixes and tests, overlay lifecycle and
overflow fixes and tests, Wine-Mono source checksum verification, and release
checksum/provenance workflows. Those implementation files are unchanged from
the starting Ozark master. The preparation script retains `set -e`, the renamed
Black Desert Wine patch, and Ozark's video patch filenames/order. Removed
syscall-emulation patches follow the official release's updated Wine integration.
Patch validation uses `LC_ALL=C` to preserve the checked ordering.

## MW4 finding and prevention

Hermes completed its investigation on October 25, 2026. Call of Duty HQ app
`1938090`, including the installed Modern Warfare 4 executable, reaches a
RICOCHET Windows kernel-driver startup barrier. No working Proton repair or
successful gameplay was established. [Anti-cheat notes](../ANTICHEAT.md) record
the retained local evidence, first-party sources and limits.

The smoke script now skips HQ for explicit IDs and library discovery. Offline
tests use temporary libraries and fake Steam/process commands to verify that
the script does not launch or signal skipped titles, delete retained logs, or
remove a logging flag it did not create. Normal Steam launches are unchanged.
No driver, service, gamefix, DLL override or anti-cheat workaround was added for HQ.

## Validation and remaining gates

Local checks cover:

- Workflow YAML, shell syntax and fail-fast preparation guards.
- Smoke exclusion regression: three tests, first observed failing before the change.
- URL decoder: 12 tests both normally and with ASan/UBSan. LeakSanitizer requires
  execution outside the ptrace-based sandbox on this host.
- Overlay lifecycle: 14 cases in one test, using the pinned Wine source and UBSan.
- Protonfixes parsing/stage smoke test, including after its preparation overlay.
- The original DXVK, D7VK, OpenVR and VKD3D-Proton preparation blocks against
  pinned sources: all apply, with some line offsets and no fuzz.
- Lsteamclient and vrclient patch application; URL tests also pass against the
  prepared lsteamclient source.
- Cumulative active video-patch replay: 95 baseline and 102 candidate patches
  apply with no rejected hunks or fuzz, after restoring generated configure
  and replaying the recorded earlier file-specific prerequisites. This checks
  the video series, not every Wine/staging preparation step.

These checks do not establish a full recursive preparation, Proton build, CI
result or gameplay compatibility. Full build verification and review remain
required before release; game verification is a separate, explicit action.
Existing installed runtimes, Steam settings and separate unfinished corrective
worktrees were not changed.

Useful local test commands:

```sh
python3 tools/tests/test_smoke_skip.py
python3 tests/run_url_unescape_tests.py
python3 tests/run_url_unescape_tests.py --sanitize
OZARK_WINE_SOURCE=/path/to/pinned/wine-git python3 tools/tests/test_overlay_patch.py
(cd protonfixes && python3 gamefixes_smoke_test.py)
```
