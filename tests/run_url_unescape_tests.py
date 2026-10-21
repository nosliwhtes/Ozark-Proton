#!/usr/bin/env python3
"""Compile unchanged path functions extracted from unixlib.cpp; no Wine startup.

UTF conversion uses libc iconv by default; --wine-ntdll loads the real native Rtl API.
DOS drive lookup and Wine API plumbing are explicit test doubles in the harness.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = None


class UrlUnescapeTests(unittest.TestCase):
    def check_case(self, name):
        result = subprocess.run([str(BINARY), name], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout, end="", flush=True)

    def test_decoder_oom(self):
        self.check_case("decoder_oom")

    def test_caller_oom(self):
        self.check_case("caller_oom")

    def test_final_triplets(self):
        self.check_case("final_triplets")

    def test_trailing_triplets(self):
        self.check_case("trailing_triplets")

    def test_utf8_triplets(self):
        self.check_case("utf8_triplets")

    def test_short_no_allocation(self):
        self.check_case("short_no_allocation")

    def test_ordinary_decoder(self):
        self.check_case("ordinary_decoder")

    def test_malformed_semantics(self):
        self.check_case("malformed_semantics")

    def test_caller_paths(self):
        self.check_case("caller_paths")

    def test_caller_file_urls(self):
        self.check_case("caller_file_urls")

    def test_caller_result_oom(self):
        self.check_case("caller_result_oom")

    def test_existing_unicode_narrowing(self):
        self.check_case("existing_unicode_narrowing")


def main():
    global BINARY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "lsteamclient/unixlib.cpp")
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--wine-ntdll", type=Path, help="native ELF ntdll.so, not PE ntdll.dll")
    args, tests = parser.parse_known_args()
    if args.wine_ntdll:
        os.environ["OZARK_TEST_NTDLL"] = str(args.wine_ntdll.resolve(strict=True))
    else:
        os.environ.pop("OZARK_TEST_NTDLL", None)
    source = args.source.read_text()
    start = source.index("#define IS_ABSOLUTE(")
    end = source.index("\nconst char **steamclient_dos_to_unix_path_array", start)
    # Preserve every byte in the function slice; only its external dependencies are adapted.
    extracted = source[start:end]
    with tempfile.TemporaryDirectory(prefix="ozark-url-tests-", dir=os.environ.get("TMPDIR")) as directory:
        directory = Path(directory)
        (directory / "path_functions.inc").write_text(extracted)
        BINARY = directory / "url_unescape_tests"
        command = [os.environ.get("CXX", "g++"), "-std=c++17", "-Wall", "-Wextra",
                   "-Werror", "-Wno-unused-variable", "-g", "-I", str(directory),
                   str(ROOT / "tests/url_unescape_harness.cpp"), "-ldl", "-o", str(BINARY)]
        if args.sanitize:
            command[1:1] = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-no-pie"]
        print("Compile:", " ".join(command), flush=True)
        subprocess.run(command, check=True, timeout=60)
        unittest.main(argv=[__file__, *tests])


if __name__ == "__main__":
    main()
