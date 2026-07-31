from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "codex-swap"


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.codex_home = root / "codex"
        self.swap_home = root / "swap"
        self.codex_home.mkdir()
        self.env = os.environ.copy()
        self.env.update(
            {
                "CODEX_HOME": str(self.codex_home),
                "CODEX_SWAP_HOME": str(self.swap_home),
            }
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_auth(self, label: str) -> None:
        (self.codex_home / "auth.json").write_text(
            json.dumps(
                {
                    "auth_mode": "chatgpt",
                    "tokens": {"access_token": f"fake-{label}"},
                    "OPENAI_API_KEY": None,
                }
            )
        )

    def run_cli(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(CLI), *args], env=self.env, text=True, capture_output=True
        )
        if ok and result.returncode != 0:
            self.fail(f"command failed: {result.stderr}")
        return result

    def test_add_switch_and_preserve_refreshed_token(self) -> None:
        self.write_auth("personal-v1")
        self.run_cli("add", "personal")
        self.write_auth("work-v1")
        self.run_cli("add", "work")

        result = self.run_cli("switch", "personal")
        self.assertIn("Switched Codex", result.stdout)
        live = json.loads((self.codex_home / "auth.json").read_text())
        self.assertEqual(live["tokens"]["access_token"], "fake-personal-v1")

        self.write_auth("personal-refreshed")
        self.run_cli("switch", "work")
        saved = json.loads((self.swap_home / "profiles" / "personal.json").read_text())
        self.assertEqual(saved["tokens"]["access_token"], "fake-personal-refreshed")

    def test_private_permissions(self) -> None:
        self.write_auth("personal")
        self.run_cli("add", "personal")
        profile = self.swap_home / "profiles" / "personal.json"
        self.assertEqual(stat.S_IMODE(profile.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.swap_home.stat().st_mode), 0o700)

    def test_json_list(self) -> None:
        self.write_auth("personal")
        self.run_cli("add", "personal")
        payload = json.loads(self.run_cli("list", "--json").stdout)
        self.assertEqual(payload["active"], "personal")
        self.assertEqual(payload["profiles"][0]["name"], "personal")

    def test_switch_without_name_rotates(self) -> None:
        self.write_auth("personal")
        self.run_cli("add", "personal")
        self.write_auth("work")
        self.run_cli("add", "work")
        self.run_cli("switch")
        status_payload = json.loads(self.run_cli("status", "--json").stdout)
        self.assertEqual(status_payload["active"], "personal")

    def test_invalid_name_is_rejected(self) -> None:
        self.write_auth("personal")
        result = self.run_cli("add", "../oops", ok=False)
        self.assertNotEqual(result.returncode, 0)

    def test_active_remove_requires_force(self) -> None:
        self.write_auth("personal")
        self.run_cli("add", "personal")
        result = self.run_cli("remove", "personal", ok=False)
        self.assertIn("active profile", result.stderr)

    def test_login_is_isolated_and_never_calls_logout(self) -> None:
        self.write_auth("personal")
        self.run_cli("add", "personal")

        fake_bin = Path(self.temp.name) / "bin"
        fake_bin.mkdir()
        fake_codex = fake_bin / "codex"
        fake_codex.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"logout\" ]; then exit 91; fi\n"
            "mkdir -p \"$CODEX_HOME\"\n"
            "printf '%s' '{\"auth_mode\":\"chatgpt\",\"tokens\":"
            "{\"access_token\":\"fake-work\"},\"OPENAI_API_KEY\":null}' "
            "> \"$CODEX_HOME/auth.json\"\n"
        )
        fake_codex.chmod(0o755)
        self.env["PATH"] = f"{fake_bin}:{self.env['PATH']}"

        self.run_cli("login", "work")
        live = json.loads((self.codex_home / "auth.json").read_text())
        saved_personal = json.loads(
            (self.swap_home / "profiles" / "personal.json").read_text()
        )
        self.assertEqual(live["tokens"]["access_token"], "fake-work")
        self.assertEqual(
            saved_personal["tokens"]["access_token"], "fake-personal"
        )


if __name__ == "__main__":
    unittest.main()
