"""Exercise the public CLI with synthetic files and isolated failing tools."""

import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "bigitems.sh"
BASH = "/bin/bash"


def gnu_tools():
    found = {}
    for name in ("du", "find", "sort", "head", "numfmt"):
        for candidate in (name, "g" + name):
            executable = shutil.which(candidate)
            if executable:
                result = subprocess.run(
                    [executable, "--version"], capture_output=True, text=True
                )
                if result.returncode == 0 and "GNU" in result.stdout:
                    found[name] = executable
                    break
        else:
            raise RuntimeError(f"Tests require GNU {name}; install coreutils and findutils.")
    return found


class BigItemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = gnu_tools()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bigitems-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data with spaces"
        self.data.mkdir()
        self.scratch = self.root / "scratch"
        self.scratch.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, TMPDIR=str(self.scratch), LC_ALL="C")

    def cli(self, *args, env=None, success=True):
        result = subprocess.run(
            [BASH, str(SCRIPT), *map(str, args)],
            cwd=self.data,
            env=env if env is not None else self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(list(self.scratch.iterdir()), [], "Temporary results leaked")
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
        return result

    @staticmethod
    def rows(result):
        return [
            (size.strip(), path)
            for line in result.stdout.splitlines()
            if "\t" in line
            for size, path in [line.split("\t", 1)]
        ]

    def isolated_path(self, prefix=None):
        for name in ("cat", "mktemp", "rm"):
            (self.bin / name).symlink_to(shutil.which(name))
        if prefix is not None:
            for name, executable in self.tools.items():
                (self.bin / (prefix + name)).symlink_to(executable)
        return dict(self.env, PATH=str(self.bin))

    def failing_tool(self, name):
        # Advertise GNU compatibility, then fail after producing partial data.
        # head's empty-input numeric validation must still succeed.
        tool = self.bin / name
        tool.write_text(
            '#!/bin/bash\n'
            'if [[ $1 == --version ]]; then echo "GNU test double"; exit 0; fi\n'
            'if [[ $1 == --lines=* ]]; then exit 0; fi\n'
            "printf '7\\t./partial\\0'\n"
            f'printf "injected {name} failure\\n" >&2\n'
            'exit 7\n'
        )
        tool.chmod(0o755)
        return dict(self.env, PATH=str(self.bin) + os.pathsep + self.env["PATH"])

    def test_help_without_gnu_tools(self):
        result = self.cli("--help", env=self.isolated_path())
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--apparent-size", result.stdout)

    def test_invalid_arguments(self):
        for args in (
            ("--unknown",), ("--top",), ("--top", "0"), ("--top", "-1"),
            ("--top=",), ("--top", "1.5"), ("--top", "text"), (".", "."),
        ):
            with self.subTest(args=args):
                result = self.cli(*args, success=False)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("Error:", result.stderr)

    def test_large_top_does_not_overflow_shell_arithmetic(self):
        (self.data / "file").write_bytes(b"abc")
        result = self.cli("-f", "--apparent-size", "--top", str(2**63 - 1))
        self.assertEqual(self.rows(result), [("3B", "./file")])

    def test_missing_directory(self):
        result = self.cli("missing", success=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("missing", result.stderr)

    def test_missing_dependency(self):
        result = self.cli(env=self.isolated_path(), success=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("GNU sort is required", result.stderr)
        self.assertIn("brew install coreutils findutils", result.stderr)

    def test_unprefixed_gnu_tools(self):
        (self.data / "file").write_bytes(b"abc")
        result = self.cli("-f", "--apparent-size", env=self.isolated_path(""))
        self.assertEqual(self.rows(result), [("3B", "./file")])

    def test_homebrew_prefixed_gnu_tools(self):
        (self.data / "file").write_bytes(b"abc")
        result = self.cli("-f", "--apparent-size", env=self.isolated_path("g"))
        self.assertEqual(self.rows(result), [("3B", "./file")])

    def test_file_ranking_and_cli_forms(self):
        for name, size in (("c", 1), ("a", 3), ("b", 2)):
            (self.data / name).write_bytes(b"x" * size)
        for args in (("--files", "--top", "2"), ("-ft2",), (".", "-f", "--top=2")):
            with self.subTest(args=args):
                result = self.cli(*args, "--apparent-size")
                self.assertEqual(self.rows(result), [("3B", "./a"), ("2B", "./b")])

    def test_ties_have_stable_path_order(self):
        for name in ("z", "b", "a"):
            (self.data / name).write_bytes(b"x")
        result = self.cli("-f", "--apparent-size", "-t2")
        self.assertEqual(self.rows(result), [("1B", "./a"), ("1B", "./b")])

    def test_directory_trees_and_both_mode(self):
        for name, size in (("large", 4096), ("small", 1)):
            directory = self.data / name
            directory.mkdir()
            (directory / "file").write_bytes(b"x" * size)
        result = self.cli("--dirs", "--apparent-size")
        self.assertEqual([path for _, path in self.rows(result)], [".", "./large", "./small"])
        result = self.cli("--top", "1")
        self.assertEqual(len(self.rows(result)), 2)
        self.assertIn("Largest Directories", result.stdout)
        self.assertIn("Largest Files", result.stdout)
        self.assertNotIn("Largest Directories", self.cli("-df").stdout)

    def test_empty_directory(self):
        self.assertEqual(self.rows(self.cli("--files")), [])
        self.assertEqual([path for _, path in self.rows(self.cli("--dirs"))], ["."])

    def test_sparse_file_changes_ranking(self):
        sparse = self.data / "sparse"
        with sparse.open("wb") as handle:
            handle.truncate(1024 * 1024)
        dense = self.data / "dense"
        dense.write_bytes(b"x" * 4096)
        if sparse.stat().st_blocks >= dense.stat().st_blocks:
            self.skipTest("Fixture filesystem does not provide sparse allocation")
        allocated = self.cli("--files")
        apparent = self.cli("--files", "--apparent-size")
        self.assertEqual([path for _, path in self.rows(allocated)], ["./dense", "./sparse"])
        self.assertEqual(self.rows(apparent)[0], ("1.0MiB", "./sparse"))
        if sparse.stat().st_blocks == 0:
            self.assertEqual(self.rows(allocated)[1][0], "0B")
        self.assertIn("allocated disk space", allocated.stdout)
        self.assertIn("apparent size", apparent.stdout)

    def test_unusual_file_names_are_preserved_and_escaped(self):
        names = ["with space", "line\nbreak", "\ttabs\t", "escape\x1b[31m", "$(touch injected)"]
        for name in names:
            (self.data / name).write_bytes(b"x")
        result = self.cli("--files", "--apparent-size")
        displayed = [path for _, path in self.rows(result)]
        expected = []
        for name in names:
            path = "./" + name
            if any(ord(char) < 32 or ord(char) == 127 for char in path):
                path = subprocess.check_output(
                    [BASH, "-c", 'printf "%q" "$1"', "quote", path], text=True
                )
            expected.append(path)
        self.assertCountEqual(displayed, expected)
        self.assertFalse((self.data / "injected").exists())
        self.assertNotIn("\x1b", result.stdout)

    def test_relative_target_names_that_look_like_options_or_expressions(self):
        for name in ("-archive", "!", "("):
            directory = self.data / name
            directory.mkdir()
            (directory / "file").write_bytes(b"x")
            result = self.cli("-f", "--", name)
            self.assertEqual([path for _, path in self.rows(result)], [f"./{name}/file"])

    def test_target_symlink_is_followed_but_nested_links_are_not(self):
        (self.data / "file").write_bytes(b"x")
        (self.data / "loop").symlink_to(self.data, target_is_directory=True)
        (self.data / "file-link").symlink_to(self.data / "file")
        target = self.root / "target-link"
        target.symlink_to(self.data, target_is_directory=True)
        result = self.cli("-f", target)
        self.assertEqual([path for _, path in self.rows(result)], [str(target / "file")])
        result = self.cli("-d", target)
        self.assertEqual([path for _, path in self.rows(result)], [str(target)])

    def test_file_list_includes_each_hard_link(self):
        (self.data / "file").write_bytes(b"abc")
        os.link(self.data / "file", self.data / "link")
        result = self.cli("-f", "--apparent-size")
        self.assertEqual(self.rows(result), [("3B", "./file"), ("3B", "./link")])

    def test_top_one_does_not_turn_large_sort_into_sigpipe_failure(self):
        for index in range(1500):
            (self.data / (f"{index:04d}-" + "x" * 100)).touch()
        result = self.cli("-ft1")
        self.assertEqual(len(self.rows(result)), 1)

    def test_scan_and_sort_failures_do_not_print_partial_rankings(self):
        for tool, mode in (("du", "-d"), ("find", "-f"), ("sort", "-f")):
            with self.subTest(tool=tool):
                env = self.failing_tool(tool)
                result = self.cli(mode, env=env, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn(f"injected {tool} failure", result.stderr)
                (self.bin / tool).unlink()

    def test_display_failures_are_nonzero(self):
        (self.data / "file").write_bytes(b"x")
        for tool in ("head", "numfmt"):
            with self.subTest(tool=tool):
                result = self.cli("-f", env=self.failing_tool(tool), success=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"injected {tool} failure", result.stderr)
                self.assertIn("display failed", result.stderr)
                (self.bin / tool).unlink()

    def test_both_mode_propagates_second_scan_failure(self):
        result = self.cli(env=self.failing_tool("find"), success=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Largest Directories", result.stdout)
        self.assertNotIn("Largest Files", result.stdout)

    @unittest.skipIf(os.geteuid() == 0, "Root bypasses filesystem permissions")
    def test_permission_error_is_visible(self):
        blocked = self.data / "blocked"
        blocked.mkdir()
        (blocked / "file").write_bytes(b"x")
        blocked.chmod(0)
        self.addCleanup(blocked.chmod, 0o700)
        for mode in ("-f", "-d"):
            with self.subTest(mode=mode):
                result = self.cli(mode, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn("Permission denied", result.stderr)

    def test_unwritable_temporary_location(self):
        env = dict(self.env, TMPDIR=str(self.root / "nonexistent"))
        result = self.cli(env=env, success=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("temporary results file", result.stderr)

    def test_interrupted_scan_cleans_up_and_returns_signal_status(self):
        ready = self.root / "ready"
        tool = self.bin / "find"
        tool.write_text(
            '#!/bin/bash\n'
            'if [[ $1 == --version ]]; then echo "GNU test double"; exit 0; fi\n'
            ': > "$TEST_READY"\n'
            'exec sleep 30\n'
        )
        tool.chmod(0o755)
        env = dict(
            self.env, PATH=str(self.bin) + os.pathsep + self.env["PATH"], TEST_READY=str(ready)
        )
        for signum in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=signum):
                process = subprocess.Popen(
                    [BASH, str(SCRIPT), "-f"], cwd=self.data, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, start_new_session=True,
                )
                try:
                    deadline = time.monotonic() + 5
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(ready.exists(), "Scan did not start")
                    os.killpg(process.pid, signum)
                    stdout, stderr = process.communicate(timeout=5)
                    self.assertEqual(process.returncode, 128 + signum, stderr)
                    self.assertEqual(stdout, "")
                    self.assertEqual(list(self.scratch.iterdir()), [])
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.communicate()
                ready.unlink()


if __name__ == "__main__":
    unittest.main()
