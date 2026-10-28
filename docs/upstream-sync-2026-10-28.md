# October 28 upstream integration and sync repair

This update starts from Ozark `bf1ee075491937571b561f78151cee2fe6677554`,
the merged source of `Ozark-Proton-2026-10-25`, and retains its ancestry.
It merges GE master `107d34ec7c562c56448ab59f13b3f2d88d056e81`:
39 commits after the official GE-Proton11-11 release
`c0c2ee35e6d4d3bff4d39c6246ac46636434feb8`. They are unreleased GE changes,
not a new official GE release. `VERSION` therefore remains `GE-Proton11-11`.

The upstream changes cover video decoding/seeking, Wayland window presentation,
controller compatibility, Wine-Mono/default-prefix build ordering and launcher
prefix migration. Native Wayland HDR now uses the standard color-management
information; the new `PROTON_FORCE_HDR` override remains opt-in. These are source
changes, not evidence that a particular game works on this computer.

Wine and graphics pins are unchanged from the [GE11-11 integration](ge11-11-integration.md).
The owned protonfixes URL remains `nosliwhtes/umu-protonfixes`. Its merged revision
`6c358c3264530cd0d5fe8deaa6f17dec3b418395` combines the shipped Ozark
`e6082b5b696be86972c066e0f080c70ca464cf00` and GE's required
`96b9fc078958f11eeea80240f233c4b1639806a0`. The missing-stage guard,
early-stage exception handling, CRLF normalization and stage smoke test remain.

Two review corrections preserve intended settings. The new Sony Windows-device
name fallback runs after `user_settings.py` is loaded, retaining launch environment
over settings over fallback precedence for Steam and UMU IDs. Star Citizen's
post-dotnet48 Windows 10 reset bypasses the installed-verb cache: pinned Winetricks
can change the prefix to Windows 7 without recording a version verb, so an old
Windows 10 log entry cannot establish the current state. Other protontricks calls
retain their existing cache behavior. These are source and mocked-process tests,
not controller or Star Citizen gameplay verification.

## OptiScaler preservation

GE commit `634051b3` removes two preparation overlays because OptiScaler was
merged into upstream protonfixes. However, GE's selected dependency `96b9fc0`
predates that implementation: its `upscalers.py` is identical to Ozark's previous
unprepared file and has no OptiScaler handler. Accepting the overlay removal with
that pin would silently lose the existing opt-in feature.

Ozark retains the two existing files in `patches/protonfixes/` and their real
preparation step. This preserves the already-shipped implementation, including
explicit FSR4 opt-in and FFX4 version selection, without importing unrelated
dependency-master changes. Remove the overlays only when the selected dependency
contains the replacement and the prepared-behavior regression passes.

The default settings, Cult of the Lamb override, URL-decoder repairs, overlay
lifecycle/overflow fixes, Wine-Mono checksum verification, fail-fast preparation,
release checksums/provenance and COD HQ smoke exclusion remain in place. This
update adds no MW4 driver or anti-cheat compatibility mechanism.

## Future syncs

The scheduled workflow still follows GE master and retains its existing schedule
and permission scopes. It initializes only protonfixes and fetches the required
upstream dependency history before Git decides whether its gitlink is already
contained in the reviewed fork. Initialization is not a substitute for merging
genuinely divergent dependency changes.

Each upstream revision uses `upstream-sync-<12-character-commit>`. Refreshing an
existing branch merges current Ozark master and retains review changes. Normal
pushes reject concurrent conflicting updates instead of overwriting them.

On a protonfixes conflict:

1. Compare both dependency histories and merge the required revision in an
   isolated checkout of the owned fork. Preserve its guards and check whether
   the parent preparation overlays are still required.
2. Test and publish the dependency commit before referencing it from Ozark.
3. Update the Ozark gitlink, reconcile the source merge and review the complete
   integration. Never resolve the conflict by blindly choosing either gitlink.

The workflow stops before publishing a branch on an unresolved conflict. It does
not merge dependency histories automatically, push master, or publish a release.

## Validation

`Validate` runs five real-Git fixture cases: no-op, a custom descendant,
a reviewed dependency merge, unresolved divergence without publication, and a
refresh preserving review commits. Four preparation tests execute the actual
protonfixes preparation block in a disposable repository and exercise the
unchanged prepared option-routing functions with mocked download helpers.
They check OptiScaler version/name, FSR4/FFX4 routing, disabled behavior and failed
OptiScaler fallback. No Steam process, game, real prefix or DLL download is used.
Four launcher tests cover defaults and explicit overrides through the complete
production constructor and settings initialization, stopped before driver/prefix
work. The dependency's 38 unit tests include stale-log Windows-version reset,
unchanged ordinary verb caching, and failed-reset reporting.

```sh
git submodule update --init protonfixes
python3 tools/tests/test_upstream_sync.py
python3 tools/tests/test_optiscaler_preparation.py
python3 tools/tests/test_smoke_skip.py
python3 tools/tests/test_session_defaults.py
python3 protonfixes/gamefixes_smoke_test.py
python3 tests/run_url_unescape_tests.py --sanitize
OZARK_WINE_SOURCE=/path/to/pinned/wine python3 tools/tests/test_overlay_patch.py
```

Offline checks and source review are separate from full recursive preparation,
compilation and packaging. A release must complete its build/release/upload jobs
and pass downloaded artifact checksums and source-provenance verification before
installation. Keep older runtimes and game selections intact. Installation and
Steam registration do not establish gameplay compatibility.
