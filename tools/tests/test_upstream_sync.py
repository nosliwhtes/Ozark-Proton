"""Run the real workflow merge step against disposable, local Git remotes."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/upstream-sync.yml").read_text())
MERGE = next(step["run"] for step in WORKFLOW["jobs"]["sync"]["steps"]
             if step.get("id") == "merge")


class UpstreamSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ozark-sync-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.env = {**os.environ, "HOME": str(self.root), "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "3",
                    "GIT_CONFIG_KEY_0": "protocol.file.allow", "GIT_CONFIG_VALUE_0": "always",
                    "GIT_CONFIG_KEY_1": f"url.{self.root}/ge.git.insteadOf",
                    "GIT_CONFIG_VALUE_1": "https://github.com/GloriousEggroll/proton-ge-custom.git",
                    "GIT_CONFIG_KEY_2": f"url.{self.root}/dependency-upstream.git.insteadOf",
                    "GIT_CONFIG_VALUE_2": "https://github.com/Open-Wine-Components/umu-protonfixes.git"}
        self.dep = self.root / "dependency"
        self.git(self.root, "init", "-b", "master", str(self.dep))
        self.dep_base = self.commit(self.dep, "base.py", "# dependency base\n")
        self.git(self.root, "clone", "--bare", str(self.dep), "dependency-upstream.git")
        self.dep_custom = self.commit(self.dep, "guard.py", "# custom stage guard\n")
        self.git(self.root, "clone", "--bare", str(self.dep), "dependency-fork.git")
        self.fork = self.root / "fork"
        self.git(self.root, "init", "-b", "master", str(self.fork))
        self.git(self.fork, "submodule", "add", str(self.root / "dependency-fork.git"), "protonfixes")
        self.git(self.fork / "protonfixes", "checkout", self.dep_base)
        self.base = self.commit(self.fork, "README", "base\n")
        self.git(self.fork / "protonfixes", "checkout", self.dep_custom)
        self.commit(self.fork, "custom-settings", "preserve\n")
        self.git(self.root, "clone", "--bare", str(self.fork), "origin.git")
        self.ge = self.root / "ge"
        self.git(self.root, "clone", str(self.fork), str(self.ge))
        self.git(self.ge, "reset", "--hard", self.base)
        self.git(self.root, "clone", "--bare", str(self.ge), "ge.git")
        self.worker_count = 0

    def git(self, directory, *args, check=True):
        return subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
            cwd=directory, env=self.env, capture_output=True, text=True,
            check=check, timeout=20,
        ).stdout.strip()

    def commit(self, directory, filename, text):
        (directory / filename).write_text(text)
        self.git(directory, "add", "-A")
        self.git(directory, "commit", "-m", filename)
        return self.git(directory, "rev-parse", "HEAD")

    def advance_upstream(self, dependency=False):
        if dependency:
            self.git(self.dep, "checkout", "-b", "upstream", self.dep_base)
            self.dep_upstream = self.commit(self.dep, "new-fix.py", "# upstream fix\n")
            self.git(self.dep, "push", str(self.root / "dependency-upstream.git"), "HEAD:master")
            self.git(self.ge, "update-index", "--cacheinfo", f"160000,{self.dep_upstream},protonfixes")
            # Keep the gitlink staged; commit()'s add -A would drop an empty submodule.
            (self.ge / "upstream-change").write_text("new\n")
            self.git(self.ge, "add", "upstream-change")
            self.git(self.ge, "commit", "-m", "upstream and dependency")
        else:
            self.commit(self.ge, "upstream-change", "new\n")
        self.ge_head = self.git(self.ge, "rev-parse", "HEAD")
        self.git(self.ge, "push", str(self.root / "ge.git"), "master")

    def run_workflow(self):
        self.worker_count += 1
        worker = self.root / f"worker-{self.worker_count}"
        self.git(self.root, "clone", str(self.root / "origin.git"), str(worker))
        output = self.root / f"output-{self.worker_count}"
        result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", MERGE],
                                cwd=worker, env={**self.env, "GITHUB_OUTPUT": str(output)},
                                text=True, capture_output=True, timeout=30)
        outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
        return result, outputs, worker

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_noop_does_not_publish(self):
        result, outputs, _ = self.run_workflow()
        self.assert_success(result)
        self.assertEqual(outputs["behind"], "0")
        self.assertEqual(self.git(self.root / "origin.git", "for-each-ref", "--format=%(refname)",
                                  "refs/heads"), "refs/heads/master")

    def test_custom_descendant_is_preserved_with_upstream_changes(self):
        self.advance_upstream()
        result, outputs, worker = self.run_workflow()
        self.assert_success(result)
        self.assertIn("branch", outputs)
        self.assertEqual(self.git(worker, "rev-parse", "HEAD:protonfixes"), self.dep_custom)
        self.git(worker, "merge-base", "--is-ancestor", self.ge_head, "HEAD")

    def test_reconciled_dependency_merge_is_preserved(self):
        self.advance_upstream(dependency=True)
        self.git(self.dep, "checkout", "master")
        self.git(self.dep, "merge", "--no-ff", "--no-edit", self.dep_upstream)
        merged = self.git(self.dep, "rev-parse", "HEAD")
        self.git(self.dep, "push", str(self.root / "dependency-fork.git"), "master")
        self.git(self.fork / "protonfixes", "fetch", "origin")
        self.git(self.fork / "protonfixes", "checkout", merged)
        self.commit(self.fork, "dependency-reconciliation", "reviewed\n")
        self.git(self.fork, "push", str(self.root / "origin.git"), "master")
        result, _, worker = self.run_workflow()
        self.assert_success(result)
        self.assertEqual(self.git(worker, "rev-parse", "HEAD:protonfixes"), merged)

    def test_divergent_dependency_stops_before_publication(self):
        self.advance_upstream(dependency=True)
        before = self.git(self.root / "origin.git", "show-ref")
        result, _, _ = self.run_workflow()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protonfixes", result.stdout + result.stderr)
        self.assertEqual(self.git(self.root / "origin.git", "show-ref"), before)

    def test_refresh_retains_review_branch_commits(self):
        self.advance_upstream()
        result, outputs, worker = self.run_workflow()
        self.assert_success(result)
        self.assertIn("branch", outputs)
        branch = outputs["branch"]
        reviewed = self.commit(worker, "review-fix", "keep this\n")
        self.git(worker, "push", "origin", f"HEAD:{branch}")
        self.commit(self.fork, "master-update", "new base\n")
        self.git(self.fork, "push", str(self.root / "origin.git"), "master")
        result, refreshed, worker = self.run_workflow()
        self.assert_success(result)
        self.assertEqual(refreshed["branch"], branch)
        self.git(worker, "merge-base", "--is-ancestor", reviewed, "HEAD")
        self.git(worker, "merge-base", "--is-ancestor", "origin/master", "HEAD")


if __name__ == "__main__":
    unittest.main()
