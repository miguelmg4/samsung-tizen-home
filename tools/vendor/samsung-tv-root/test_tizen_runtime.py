"""Regression check for the custom dotnet host on TU50DU7105KXXC."""
import unittest

from samsung_tv_root.archive_root import ArchiveRootError, _check_target
from samsung_tv_root.sdb import CaptureResult


class Client:
    path = "/usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9"
    runtime_exists = True

    def connect(self):
        pass

    require_device = connect
    require_shell_injection = connect

    def capture(self, command, timeout=15):
        if command.startswith("getcap"):
            output = ("/usr/bin/dotnet = cap_setgid,cap_sys_admin+ei\n"
                      "/usr/sbin/sdbd-tarlauncher = cap_setgid,cap_setuid+eip")
        elif "--list-runtimes" in command:
            return CaptureResult("Unknown option --list-runtimes.\n[exit:255]\n", 0)
        elif command.startswith("readlink"):
            output = self.path
        elif command.startswith("test -f"):
            return CaptureResult("\n[exit:0]\n" if self.runtime_exists else "\n[exit:1]\n", 0)
        elif "tar --help" in command:
            output = "--to-command"
        else:
            output = "original-file-hashes"
        return CaptureResult(output + "\n[exit:0]\n", 0)


class RuntimeTest(unittest.TestCase):
    def test_tizen_runtime(self):
        self.assertEqual(_check_target(Client()).runtime, "6.0")

    def test_rejects_invalid_or_missing_runtime(self):
        for path, exists in [("/tmp/6.0.9", True), (Client.path + ";id", True), (Client.path, False)]:
            with self.subTest(path=path, exists=exists):
                client = Client()
                client.path, client.runtime_exists = path, exists
                with self.assertRaises(ArchiveRootError):
                    _check_target(client)


if __name__ == "__main__":
    unittest.main()
