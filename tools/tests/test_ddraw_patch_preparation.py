"""Apply the real DirectDraw video patches to the pinned Wine sources.

Only three source files are needed, fetched from the pinned upstream commit.
Set WINE_SOURCE_DIR to a local Wine Git checkout to run without network access.
This is a patch/lifecycle regression test, not a Wine build or gameplay test.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]


class DirectDrawPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="ozark-ddraw-")
        cls.addClassCleanup(temporary.cleanup)
        cls.source = Path(temporary.name)
        pin = subprocess.check_output(
            ["git", "ls-tree", "HEAD", "wine"], cwd=ROOT, text=True
        ).split()[2]
        for name in ("ddraw.c", "ddraw_private.h", "surface.c"):
            relative = "dlls/ddraw/" + name
            if local := os.environ.get("WINE_SOURCE_DIR"):
                contents = subprocess.check_output(
                    ["git", "show", f"{pin}:{relative}"], cwd=local
                )
            else:
                with urlopen(f"https://raw.githubusercontent.com/ValveSoftware/wine/{pin}/{relative}",
                             timeout=60) as response:
                    contents = response.read()
            destination = cls.source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)

        cls.applied = []
        for patch in sorted((ROOT / "patches/ge-video-rework").glob("*.patch")):
            if "--- a/dlls/ddraw/" not in patch.read_text():
                continue
            result = subprocess.run(
                ["git", "apply", "--include=dlls/ddraw/*", str(patch)],
                cwd=cls.source, text=True, capture_output=True,
            )
            if result.returncode:
                raise AssertionError(f"{patch.name}:\n{result.stderr}")
            cls.applied.append(patch.name)
        cls.surface = (cls.source / "dlls/ddraw/surface.c").read_text()

    def test_dependent_patches_applied(self):
        self.assertIn("0075-ddraw-emulate-one-visible-overlay.patch", self.applied)
        self.assertIn("0076-ddraw-layered-overlay-window-for-godfather-fmvs.patch", self.applied)

    def test_shared_cleanup_closes_window_only_when_restoring(self):
        helper = self.surface.split("static void ddraw_surface_clear_overlay", 1)[1].split(
            "/*****************************************************************************", 1)[0]
        self.assertRegex(helper, r"if \(restore_window\)\s+ddraw_gf_close_overlay_window\(ddraw\);")
        self.assertLess(helper.index("ddraw_gf_close_overlay_window"),
                        helper.index("ddraw->overlay = ddraw->overlay_dst = NULL"))
        # Repositioning uses the same cleanup but must retain its popup.
        self.assertIn("ddraw_surface_clear_overlay(ddraw, FALSE);", self.surface)

    def test_hide_and_teardown_use_shared_cleanup(self):
        self.assertRegex(self.surface, r"if \(flags & DDOVER_HIDE\)\s*\{\s*"
                         r"if \(ddraw->overlay == overlay\)\s*"
                         r"ddraw_surface_clear_overlay\(ddraw, TRUE\);")
        self.assertIn("ddraw_surface_clear_overlay(surface->ddraw, TRUE);", self.surface)


if __name__ == "__main__":
    unittest.main()
