import json
import unittest
from pathlib import Path


MANIFEST = json.loads((Path(__file__).parent / "autotask-plugin.json").read_text())


class ExecutorManifestTest(unittest.TestCase):
    def test_generic_worker_contract(self):
        self.assertEqual(MANIFEST["schema_version"], "autotask.plugin.v1")
        executor = MANIFEST["capabilities"]["executors"][0]
        self.assertEqual(executor["executor_id"], "example_executor")
        self.assertEqual(executor["protocol"], "headless_stdio_v1")
        self.assertEqual(executor["surfaces"], ["job"])
        self.assertIn("{task}", executor["entrypoint"]["args"])
        self.assertEqual(executor["invocation"]["task_passthrough"], "argv")
        self.assertEqual(executor["invocation"]["progress_marker"], "example: progress:")
        self.assertNotIn("binary", executor)

    def test_entrypoint_has_no_shell_script(self):
        command = MANIFEST["capabilities"]["executors"][0]["entrypoint"]["command"]
        self.assertNotIn("/", command)
        self.assertNotIn(";", command)
        self.assertNotIn("|", command)


if __name__ == "__main__":
    unittest.main()
