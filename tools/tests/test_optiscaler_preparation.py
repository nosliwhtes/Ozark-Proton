"""Check the actual protonfixes prep block and option routing without downloads."""
import ast
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]


class OptiscalerPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory(prefix="ozark-optiscaler-") as directory:
            root = Path(directory)
            dependency = root / "protonfixes"
            dependency.mkdir()
            shutil.copyfile(ROOT / "protonfixes/upscalers.py", dependency / "upscalers.py")
            shutil.copytree(ROOT / "patches/protonfixes", root / "patches/protonfixes")
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C"}
            for args in (("init",), ("add", "upscalers.py"),
                         ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                          "commit", "-m", "Pinned upscalers source")):
                subprocess.run(["git", *args], cwd=dependency, env=env,
                               check=True, capture_output=True)
            prep = (ROOT / "patches/protonprep-valve-staging.sh").read_text()
            helpers = prep.split("### (1) PREP SECTION ###", 1)[0]
            block = prep.split("    pushd protonfixes\n", 1)[1].split("    popd", 1)[0]
            result = subprocess.run(
                ["bash", "-c", helpers + "\npushd protonfixes\n" + block + "\npopd\n"],
                cwd=root, env=env, capture_output=True, text=True, timeout=15,
            )
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            tree = ast.parse((dependency / "upscalers.py").read_text())
            # Execute unchanged production routing functions with mocked I/O helpers.
            cls.routing = compile(ast.Module(body=[
                node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in {"get_version", "setup_upscalers"}
            ], type_ignores=[]), "prepared-upscalers.py", "exec")

    def setUp(self):
        self.scope = {name: Mock(return_value=True) for name in
                      ("setup_upscaler", "setup_optiscaler", "clean_upscaler", "log")}
        exec(self.routing, self.scope)

    def setup(self, options, env):
        self.scope["setup_upscalers"](options, env, "/fake/compat", "/fake/prefix")

    def test_optiscaler_uses_requested_version_and_name(self):
        env = {"PROTON_USE_OPTISCALER": "0.9.0", "PROTON_OPTISCALER_NAME": "version.dll"}
        self.setup({"optiscaler"}, env)
        self.scope["setup_optiscaler"].assert_called_once_with(
            env, "/fake/compat", "/fake/prefix", "0.9.0")
        self.assertEqual(env.get("WINE_OPTISCALER_NAME"), "version.dll")
        self.assertNotIn("WINE_UPSCALER_REPLACE", env)
        self.assertFalse(any(call.args[0] == "fsr4"
                             for call in self.scope["setup_upscaler"].call_args_list))

    def test_fsr4_version_controls_ffx4_unless_explicit(self):
        for explicit, expected in ((False, "4.1.0"), (True, "4.2.0")):
            with self.subTest(explicit=explicit):
                self.scope["setup_upscaler"].reset_mock()
                env = {"PROTON_FSR4_UPGRADE": "4.1.0", "PROTON_FFX4_UPGRADE": "4.2.0"}
                options = {"optiscaler", "fsr4"} | ({"ffx4"} if explicit else set())
                self.setup(options, env)
                self.scope["setup_upscaler"].assert_any_call(
                    "ffx4", "/fake/compat", "/fake/prefix", expected)
                self.assertEqual(env.get("WINE_OPTISCALER_NAME"), "dxgi.dll")

    def test_disabled_optiscaler_does_not_run(self):
        env = {"DXVK_NVAPI_DRS_SETTINGS": "user-choice"}
        self.setup({"dlss"}, env)
        self.scope["setup_optiscaler"].assert_not_called()
        self.assertNotIn("WINE_OPTISCALER_NAME", env)
        self.assertEqual(env["DXVK_NVAPI_DRS_SETTINGS"], "user-choice")
        self.assertEqual(env["WINE_UPSCALER_REPLACE"], "dlss")

    def test_failed_optiscaler_keeps_successful_upscaler_fallback(self):
        self.scope["setup_optiscaler"].return_value = False
        env = {}
        self.setup({"optiscaler"}, env)
        self.assertNotIn("WINE_OPTISCALER_NAME", env)
        self.assertEqual(set(env.get("WINE_UPSCALER_REPLACE", "").split(",")),
                         {"dlss", "xess", "ffx3"})


if __name__ == "__main__":
    unittest.main()
