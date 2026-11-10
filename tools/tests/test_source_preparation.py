"""Apply the real helper/client preparation block without dependencies or games."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class SourcePreparationTests(unittest.TestCase):
    def test_helper_and_client_patches_apply_to_tracked_sources(self):
        prep = (ROOT / "patches/protonprep-valve-staging.sh").read_text()
        helpers = prep.split("### (1) PREP SECTION ###", 1)[0]
        block = prep.split("### END PREP SECTION ###", 1)[1].split("### (2) WINE PATCHING ###", 1)[0]
        with tempfile.TemporaryDirectory(prefix="ozark-source-prep-") as directory:
            root = Path(directory)
            for name in ("lsteamclient", "steam_helper", "umu_helper", "vrclient_x64", "patches"):
                shutil.copytree(ROOT / name, root / name, symlinks=True)
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C"}
            for args in (("init",), ("add", ".")):
                subprocess.run(["git", *args], cwd=root, env=env,
                               check=True, capture_output=True, timeout=30)
            # git checkout restores the index, so a commit is not needed.
            for attempt in range(2):
                result = subprocess.run(["bash", "-c", helpers + block], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0,
                                 f"Preparation attempt {attempt + 1}:\n" + result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
