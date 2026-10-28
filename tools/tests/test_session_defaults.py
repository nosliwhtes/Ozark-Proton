"""Exercise the real Session constructor and settings load without starting Wine."""
import ast
import os
from pathlib import Path
import platform
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
KEY = "PROTON_SONY_WINDOWS_DEVICE_NAMES"
APPIDS = ("2909400", "2420110", "2561580")


class SettingsLoaded(Exception):
    """Stop before driver detection, prefix updates and process execution."""


class SessionDefaultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((ROOT / "proton").read_text())
        session = next(node for node in tree.body
                       if isinstance(node, ast.ClassDef) and node.name == "Session")
        # Preserve both complete methods; the driver probe stops init_session
        # after configuration/defaults, before any prefix or game operations.
        session.body = [node for node in session.body if isinstance(node, ast.FunctionDef)
                        and node.name in {"__init__", "init_session"}]
        cls.code = compile(ast.Module(body=[session], type_ignores=[]), "proton", "exec")

    def launch_settings(self, environment, settings):
        scope = {
            "os": os, "platform": platform, "sys": sys, "log": Mock(),
            "default_compat_config": set, "default_cpu_limit": {},
            "file_exists": lambda *args, **kwargs: True,
            "g_proton": SimpleNamespace(xrandr_bin="xrandr", host_pe_arch="x86_64-windows",
                                       lib_dir="/unused/lib", user_settings_file="unused.py"),
            "g_compatdata": SimpleNamespace(prefix_dir="/unused/prefix"),
            "utilities": SimpleNamespace(is_driver_loaded=Mock(side_effect=SettingsLoaded)),
        }
        exec(self.code, scope)
        with patch.dict(os.environ, environment, clear=True), patch.dict(
                sys.modules, {"user_settings": SimpleNamespace(user_settings=settings)}):
            session = scope["Session"]()
            with self.assertRaises(SettingsLoaded):
                session.init_session(False)
        return session.env

    def test_target_defaults_for_steam_and_umu(self):
        for appid in APPIDS:
            for env in ({"SteamGameId": appid}, {"UMU_ID": "umu-" + appid}):
                with self.subTest(env=env):
                    self.assertEqual(self.launch_settings(env, {})[KEY], "1")

    def test_user_settings_override_default(self):
        for appid in APPIDS:
            for env in ({"SteamGameId": appid}, {"UMU_ID": "umu-" + appid}):
                with self.subTest(env=env):
                    self.assertEqual(self.launch_settings(env, {KEY: "0"})[KEY], "0")

    def test_launch_environment_wins_over_settings(self):
        for launch, setting in (("0", "1"), ("1", "0")):
            for appid in APPIDS:
                with self.subTest(appid=appid, launch=launch):
                    env = {"SteamGameId": appid, KEY: launch}
                    self.assertEqual(self.launch_settings(env, {KEY: setting})[KEY], launch)

    def test_unrelated_or_invalid_app_has_no_new_default(self):
        for env in ({}, {"SteamGameId": "123"}, {"UMU_ID": "umu-invalid"},
                    {"SteamGameId": "123", "UMU_ID": "umu-2909400"}):
            with self.subTest(env=env):
                self.assertNotIn(KEY, self.launch_settings(env, {}))


if __name__ == "__main__":
    unittest.main()
