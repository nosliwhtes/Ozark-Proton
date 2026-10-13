# URL decoder fix — implementation and verification

## Scope

Approved contract: `github-sweep/docs/plans/sweep-fixes-20261013/approved-contract.md`, section A.
Worktree: `/home/nosliwhtes/Projects/ozark-url-unescape-fix`.
Branch: `fix/url-unescape-sweep-20261013`.
Base: `816b030c28a88d783e093fa570fda749b62d1d0e`.

Only production change: `lsteamclient/unixlib.cpp`.

- Make the private decoder return `bool`: short input and normal completion succeed; failed allocation returns `false` before any write or conversion.
- Its only caller immediately returns `NULL` on decoder failure, before path collapse, filesystem lookup, or output allocation. Returning through the existing `done` path would incorrectly produce a partial `file://` result.
- Include the final possible triplet with `i <= len - 3`. The preceding short-input guard prevents unsigned underflow.

No changes to malformed-hex handling, literal WCHAR narrowing, UTF conversion status handling, relative-path policy, or other allocation sites. The existing decoding logic now also runs at the previously omitted final triplet position.

## Run focused tests

From this worktree:

```sh
python3 tests/run_url_unescape_tests.py -v
python3 tests/run_url_unescape_tests.py --sanitize -v
python3 tests/run_url_unescape_tests.py --sanitize \
  --wine-ntdll /usr/lib/x86_64-linux-gnu/wine/x86_64-unix/ntdll.so -v
```

The runner extracts the unchanged source slice beginning at `IS_ABSOLUTE` and ending before the array-conversion function. It compiles the actual `collapse_path`, `get_unix_file_name`, `hexdigit`, `url_unescape`, caller, and free helper, not a decoder reimplementation. `--source` allows testing a baseline or disposable mutation without editing this worktree. The old void signature is supported solely so baseline tests execute and fail behaviorally rather than at compile time.

All 12 final test groups pass in plain mode and with AddressSanitizer/UndefinedBehaviorSanitizer. Both final sanitized conversion backends pass. Cases cover forced decoder allocation failure, unchanged input on failure, caller failure propagation/no lookup, output allocation failure after successful conversion, short no-allocation inputs, exact `%41`, trailing `abc%41`, adjacent escapes, lowercase hex, 2/3/4-byte UTF-8 escapes, ordinary paths, file URLs, suffix preservation, path collapse, and unchanged representative malformed-input behavior.

## Evidence

All logs are under `evidence/fixes-20261013/`:

| File | Result |
| --- | --- |
| `01-oom-red.txt` | Original source: direct/caller OOM fail with sanitizer-confirmed null writes. |
| `02-oom-green.txt` | OOM slice: 2 tests pass after allocation guard and propagation. |
| `03-boundary-red.txt` | Boundary slice: new exact-triplet test fails; OOM remains green. |
| `04-boundary-green.txt` | 3 tests pass after loop-bound fix. |
| `05-full-sanitized-green.txt` | Intermediate 10-group suite passes. |
| `06-baseline-characterizations.txt` | Original source: 5 characterization groups pass with iconv. |
| `07-mutation-boundary-red.txt` | Disposable reversion of bound: exact, trailing and UTF-8 groups all fail. |
| `07-mutation-caller-red.txt` | Ignoring decoder failure while retaining allocation guard fails caller test. |
| `08-final-plain.txt` | 12 groups pass without sanitizers. |
| `09-final-native-wine-sanitized.txt` | Final harness: 12 groups pass using actual native Wine UTF conversion. |
| `10-final-iconv-sanitized.txt` | Final harness: 12 groups pass using libc iconv adapter. |
| `11-baseline-native-characterizations.txt` | Original source: same 5 characterization groups pass using native Wine. |
| `environment.txt` | Base/branch, compiler, native library identity/hash, uninitialized submodule status. |

Logs retain real process output and exit status; earlier logs reflect the test suite at that TDD stage. Negative mutation runs are expected failures, not final-suite failures.

## Conversion boundaries and limitations

Native mode loads the installed ELF `ntdll.so` with `dlopen` and calls its exported `RtlUTF8ToUnicodeN` using the native Unix ABI. Its ABI was inspected and a direct UTF-8-to-UTF-16 probe succeeded. This does not run Wine, create a prefix, or start Wine services. It is the host's installed Wine implementation, not a build of this repository's pinned Wine.

Default mode adapts `RtlUTF8ToUnicodeN` through real libc iconv. Both modes stub Wine's locale-dependent `ntdll_umbstowcs` with UTF-8 iconv, filesystem/drive lookup with a captured NT-path-to-Z:-drive mapping, `lstrcpynA`, and logging. WCHAR is 16-bit; `wcslen` is adapted accordingly. The iconv adapter covers valid UTF-8, not all Wine invalid-byte semantics. The inherited unused `c` variable is why this extracted compile suppresses unused-variable warnings; other enabled warnings are errors. Native Wine itself is not sanitizer-instrumented.

**Adjacent defect proved, intentionally not fixed:** direct decoding of `u"abc\u0100def"` produces `u"abc"`: the existing WCHAR-to-char assignment narrows U+0100 to zero, and `strlen(tmp)` truncates conversion. Both original and fixed functions demonstrate this with real native Wine conversion. The characterization documents the defect; it is not an endorsement of the behavior.

No full Proton/submodule build or game/runtime compatibility test was run. No submodules were initialized or modified. No game, Steam, live configuration, wiki, release, remote push, or PR action was performed. Independent ordered SPEC then QUALITY review and any publication remain the parent's responsibility.
