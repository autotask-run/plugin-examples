import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ADAPTER = ROOT / "adapter.py"
PROTOCOL = "autotask.agent-adapter.protocol.v1"


def invoke(operation, payload):
    request = {
        "protocol": PROTOCOL,
        "operation": operation,
        "adapter_id": "example.agent",
        "payload": payload,
    }
    completed = subprocess.run(
        [sys.executable, str(ADAPTER)],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise AssertionError(f"expected one response line, got {lines!r}")
    return json.loads(lines[0])


class AgentAdapterTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="autotask-agent-adapter-"))
        self.host = {
            "home": str(self.home),
            "config_dir": str(self.home / ".config"),
            "platform": "linux",
            "cli_version": "0.1.2",
        }

    def test_discover_returns_a_home_scoped_json_target(self):
        response = invoke("discover", {"host": self.host})
        self.assertEqual(response["protocol"], PROTOCOL)
        self.assertEqual(
            response["targets"],
            [{"path": str(self.home / ".config/example-agent/config.json"), "format": "json"}],
        )

    def test_plan_preserves_unrelated_settings_and_is_idempotent(self):
        original = {
            "existing": {"keep": True},
            "mcpServers": {"other": {"url": "https://other.example/mcp"}},
            "model": "user-selected-model",
        }
        target_path = self.home / ".config/example-agent/config.json"
        payload = {
            "request": {
                "agent": "example.agent",
                "server_url": "https://app.autotask.run",
                "gateway_url": "https://app.autotask.run/v1",
                "mcp_url": "https://app.autotask.run/mcp/stream",
                "model": "example-model",
                "token_env": "EXAMPLE_TOKEN",
                "transport": "remote",
                "replace": False,
            },
            "host": self.host,
            "targets": [
                {
                    "path": str(target_path),
                    "format": "json",
                    "original_content": json.dumps(original),
                }
            ],
        }
        response = invoke("plan", payload)
        self.assertEqual(response["protocol"], PROTOCOL)
        planned = json.loads(response["files"][0]["content"])
        self.assertEqual(planned["existing"], {"keep": True})
        self.assertEqual(planned["mcpServers"]["other"], original["mcpServers"]["other"])
        self.assertEqual(planned["model"], "user-selected-model")
        self.assertEqual(planned["mcpServers"]["autotask"]["url"], payload["request"]["mcp_url"])
        self.assertIn("${EXAMPLE_TOKEN}", response["files"][0]["content"])

        payload["targets"][0]["original_content"] = response["files"][0]["content"]
        second = invoke("plan", payload)
        self.assertEqual(second["files"][0]["content"], response["files"][0]["content"])

    def test_stdio_plan_does_not_emit_a_token_value(self):
        target_path = self.home / ".config/example-agent/config.json"
        response = invoke(
            "plan",
            {
                "request": {
                    "server_url": "https://app.autotask.run",
                    "mcp_url": "https://app.autotask.run/mcp/stream",
                    "token_env": "EXAMPLE_TOKEN",
                    "transport": "stdio",
                },
                "host": self.host,
                "targets": [{"path": str(target_path), "format": "json"}],
            },
        )
        content = response["files"][0]["content"]
        self.assertNotIn("EXAMPLE_TOKEN", content)
        self.assertEqual(json.loads(content)["mcpServers"]["autotask"]["transport"], "stdio")


if __name__ == "__main__":
    unittest.main()
