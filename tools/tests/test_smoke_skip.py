"""Exercise smoke exclusions with fake Steam commands and temporary libraries.

No game, real Steam command, process signal, or network request is used.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "ozark-smoke.sh"


class SmokeSkipTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ozark-smoke-skip-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.steam = self.home / "Steam"
        self.apps = self.steam / "steamapps"
        self.apps.mkdir(parents=True)
        self.events = self.home / "unexpected-commands"
        binaries = self.home / "bin"
        binaries.mkdir()
        for name in ("steam", "xdg-open", "pkill", "pgrep"):
            command = binaries / name
            check = 'if [ "$*" = "-x steam" ]; then exit 0; fi\n' if name == "pgrep" else ""
            command.write_text(
                '#!/bin/sh\n' + check +
                'printf "%s %s\\n" "$0" "$*" >> "$OZARK_TEST_EVENTS"\nexit 1\n'
            )
            command.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "STEAM_ROOT": str(self.steam),
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
            "OZARK_TEST_EVENTS": str(self.events),
            "BOOT_TIMEOUT": "0",
            "WAIT": "0",
        }

    def manifest(self, apps, appid):
        apps.mkdir(parents=True, exist_ok=True)
        (apps / f"appmanifest_{appid}.acf").write_text(
            f'"AppState"\n{{\n"appid" "{appid}"\n"name" "Test game {appid}"\n}}\n'
        )
        (apps / "compatdata" / appid).mkdir(parents=True)

    def run_skip(self, arguments, expected):
        logdir = self.home / "ozark-logs"
        logdir.mkdir(exist_ok=True)
        retained = logdir / "steam-1938090.log"
        retained.write_text("retained diagnostic evidence\n")
        result = subprocess.run(
            ["bash", str(SCRIPT), *arguments], env=self.env,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        reports = list(logdir.glob("smoke-*.md"))
        self.assertEqual(len(reports), 1)
        report = reports[0].read_text()
        for appid in expected:
            self.assertIn(f"| {appid} |", report)
        self.assertEqual(report.count("| SKIP |"), len(expected))
        self.assertIn(f"0 pass · 0 fail · {len(expected)} skipped", report)
        self.assertEqual(retained.read_text(), "retained diagnostic evidence\n")
        self.assertFalse(self.events.exists(), "Skipped titles must not launch or be signalled")
        return report

    def test_explicit_hq_id_is_skipped(self):
        self.manifest(self.apps, "1938090")
        self.run_skip(["1938090"], ["1938090"])
        self.assertFalse((self.home / ".config/ozark/test-mode").exists())

    def test_discovered_hq_in_secondary_library_is_skipped(self):
        library = self.home / "Library with spaces"
        self.manifest(library / "steamapps", "1938090")
        (self.apps / "libraryfolders.vdf").write_text(f'"1" {{ "path" "{library}" }}\n')
        self.run_skip([], ["1938090"])

    def test_existing_exclusions_and_log_flag_are_preserved(self):
        flag = self.home / ".config/ozark/test-mode"
        flag.parent.mkdir(parents=True)
        flag.write_text("owned by another test\n")
        ids = ["553850", "2479810", "1144200", "1938090"]
        for appid in ids:
            self.manifest(self.apps, appid)
        self.run_skip(ids, ids)
        self.assertEqual(flag.read_text(), "owned by another test\n")


if __name__ == "__main__":
    unittest.main()
