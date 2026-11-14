# November 10 upstream integration

This integration starts from Ozark master
`7145c05f4b8c085b288e620a820713d2b0083444` and merges GE master
`cc7c349356ef198f3ffb9c7e3b7a9188ab299a82`, preserving both histories.
It includes 39 upstream commits missing from that Ozark revision. These are
unreleased changes after GE-Proton11-12, not a new official GE release.

The scheduled [November 9 sync](https://github.com/nosliwhtes/Ozark-Proton/actions/runs/42704654478)
stopped on a README conflict, before publishing a branch. The resolution keeps
Ozark's corrected DualSense Bluetooth audio description and adds the new
DualShock 4 Bluetooth input/audio options from GE. The conflict was not a runner
or network failure, and the workflow's fail-on-conflict behavior is unchanged.

Upstream changes include controller and overlay focus handling, looped video
playback, Ubisoft Connect shutdown, OpenXR probe behavior, Le Mans Ultimate
compatibility patches and a built-in MIDI synthesizer. The latter adds the
GeneralUser GS soundfont and its upstream license. The new SBC dependency supports
DualShock 4 Bluetooth audio. This is a source integration, not game testing.

## Preserved Ozark changes

Wine, Wine staging, DXVK and VKD3D-Proton stay on their existing pinned revisions.
The owned protonfixes dependency remains
`17c0938a7315db48832f005c60ed984c39b14c7b`, which contains GE's required
`28a02c25e4b895131c9ebdeda411ec3646b38151` plus the fork's fixes.
The withdrawn `run`/`runinprefix` upscaler workaround remains removed, while normal
`waitforexitandrun` OptiScaler setup is covered by the prepared-dependency tests.
Ozark settings precedence, URL-decoder repairs, fail-fast patch preparation,
release checksums/provenance and the Call of Duty HQ smoke exclusion remain.

## Release patch failure

The [November 8 release build](https://github.com/nosliwhtes/Ozark-Proton/actions/runs/42435038652)
failed separately while applying DirectDraw patch 0076. It still expected the
inline overlay cleanup that Ozark's earlier 0075 patch had refactored. Rebase
0076 onto the shared cleanup helper, preserving Ozark's lifecycle and overflow
fixes. The temporary Godfather overlay window closes on hide, destination
changes and teardown, but stays open when repositioning the same overlay.

The new DirectDraw regression fetches only three source files at the pinned Wine
revision (or reads a local Git checkout through `WINE_SOURCE_DIR`) and applies
all DirectDraw patches in the GE video series. It checks the shared cleanup
integration as well as patch applicability. The old patch reproduces the failure;
the corrected patch passes. This does not change the historical release tag or
publish replacement release assets.

## Validation

The launcher test fixture now loads the real `nonzero` helper and supplies the
soundfont path needed by the expanded upstream constructor. It still exercises
the full constructor and settings load, and adds checks for the default/custom
MIDI soundfont and disabled/missing soundfont behavior.

A new regression executes the real helper/client preparation block twice in an
isolated copy, checking both initial preparation and repeatability. It includes
Discord RPC, Ubisoft launcher and lsteamclient focus patches, without building
Proton or launching a game.

The complete integrated Wine preparation section also passed twice from the
pinned sources, including staging and all later hotfixes: 1,983 file patch
applications per run, no rejects, with identical final DirectDraw source hashes.
This replay stopped before autoreconf and compilation. The URL-decoder suite
passed 12 cases both unsanitized and with AddressSanitizer/UndefinedBehaviorSanitizer
using the libc iconv adapter. LeakSanitizer was disabled for the sanitized run
because it cannot run under this executor's process tracing; this was not native
Wine decoding or leak validation.

Validation of this source branch is separate from a complete Development build,
release packaging and gameplay verification. Do not treat passing lightweight
checks as proof of any game's compatibility or install this integration over a
known working release without the separate build and artifact checks.

## Submodule host resilience

The [November 13 release build](https://github.com/nosliwhtes/Ozark-Proton/actions/runs/43544384199)
failed after two `git.kernel.org` connections timed out at 132 seconds each, so
the new `sbc` submodule never cloned. The same patch tree had already built
successfully in a Development run, which makes this a host problem rather than a
source problem. The `sbc` submodule now points at `kernel.googlesource.com`, an
official mirror that carries the pinned commit `b3deb8a5`, and the Patch step
retries the recursive submodule update three times before failing. Run
`git submodule sync` in an existing checkout that already initialized `sbc` from
kernel.org.
