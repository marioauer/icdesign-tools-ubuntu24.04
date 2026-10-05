import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildTests(unittest.TestCase):
    def test_selection(self):
        control = dict.fromkeys(build.PACKAGES, True)
        control["vacask"] = False
        self.assertEqual(build.select(control), ["ngspice", "openvaf", "xschem"])
        self.assertEqual(build.select(control, ("vacask",)), ["vacask"])
        self.assertEqual(build.select(control, all_packages=True), list(build.PACKAGES))
        with self.assertRaises(ValueError):
            build.select({"ngspice": True})

    def test_build_dependency_union(self):
        deps = build.build_dependencies(("ngspice",))
        self.assertIn("git", deps)
        self.assertIn("libedit-dev", deps)
        self.assertNotIn("llvm-18-dev", deps)
        self.assertNotIn("cmake", deps)
        union = build.build_dependencies(("openvaf", "vacask"))
        self.assertEqual(union.count("llvm-18-dev"), 1)
        self.assertEqual(union, build.build_dependencies(("vacask", "openvaf")))
        self.assertEqual(build.build_dependencies(()),
                         sorted(build.load(ROOT / "shared/build-dependencies.json")["common"]))

    def test_invalid_build_dependencies(self):
        for invalid in ("git", ["git; echo bad"], [123], [[]]):
            with self.subTest(invalid=invalid), patch.object(build, "load", return_value={"common": invalid}):
                with self.assertRaises(ValueError):
                    build.build_dependencies(())
        with patch.object(build, "load", side_effect=[{"common": ["git"]}, {"runtime": [], "sources": {}}]):
            with self.assertRaises(ValueError):
                build.build_dependencies(("ngspice",))

    def test_list_build_dependencies(self):
        for options, packages in ((["--all"], build.PACKAGES), (["--package", "ngspice"], ("ngspice",))):
            result = subprocess.check_output(
                [sys.executable, ROOT / "scripts/build.py", "--list-build-deps", *options], text=True)
            self.assertEqual(result.splitlines(), build.build_dependencies(packages))

    def test_manifests(self):
        self.assertIn("libclang-18-dev", build.build_dependencies())
        for package in build.PACKAGES:
            self.assertTrue(build.runtime_dependencies(package))
            args = build.source_build_args(package)
            self.assertIn("--build-arg", args)
            self.assertTrue(any("_COMMIT=" in arg for arg in args))
        self.assertIn("BOOST_SHA256=3621533e820dcab1e8012afd583c0c73cf0f77694952b81352bf38c1488f9cb4",
                      build.source_build_args("vacask"))
        openvaf = build.load(ROOT / "packages/openvaf/dependencies.json")["sources"]["openvaf"]
        vacask = build.load(ROOT / "packages/vacask/dependencies.json")["sources"]["openvaf"]
        self.assertEqual(openvaf, vacask)
        result = subprocess.check_output([sys.executable, ROOT / "scripts/build.py", "--list"], text=True)
        self.assertEqual(result.splitlines(), list(build.PACKAGES))

    def test_retains_disabled_from_previous_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous = root / "previous"
            previous.mkdir()
            old_name = "icdesign-vacask_0.3.4-2_amd64.deb"
            (previous / old_name).write_bytes(b"old")
            (previous / "manifest.json").write_text(json.dumps({"vacask": old_name}))
            dist = root / "dist"
            dist.mkdir()
            new_name = "icdesign-ngspice_47-1_amd64.deb"
            (dist / new_name).write_bytes(b"new")
            site = root / "site"
            subprocess.run([sys.executable, ROOT / "scripts/prepare_site.py", "--dist", dist,
                            "--site", site, "--previous-url", previous.as_uri()], check=True)
            self.assertEqual(json.loads((site / "manifest.json").read_text()),
                             {"ngspice": new_name, "vacask": old_name})
            self.assertEqual((site / old_name).read_bytes(), b"old")

    def test_site_from_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            site = Path(tmp) / "site"
            dist.mkdir()
            (dist / "icdesign-ngspice_47-1_amd64.deb").write_bytes(b"test")
            subprocess.run([sys.executable, ROOT / "scripts/prepare_site.py", "--dist", dist, "--site", site], check=True)
            self.assertEqual(json.loads((site / "manifest.json").read_text()),
                             {"ngspice": "icdesign-ngspice_47-1_amd64.deb"})
            self.assertTrue((site / "icdesign-ngspice_47-1_amd64.deb").exists())


if __name__ == "__main__":
    unittest.main()
