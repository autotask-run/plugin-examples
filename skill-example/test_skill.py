import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate import validate_bundle


ROOT = Path(__file__).parent


class SkillBundleTest(unittest.TestCase):
    def test_reference_bundle_is_valid(self):
        self.assertEqual(validate_bundle(ROOT / "SKILL.md", ROOT / "manifest.template.json"), [])

    def test_required_frontmatter_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "SKILL.md"
            skill.write_text((ROOT / "SKILL.md").read_text().replace("description:", "summary:", 1))
            errors = validate_bundle(skill, ROOT / "manifest.template.json")
            self.assertTrue(any("frontmatter missing description" in error for error in errors), errors)

    def test_absolute_bundle_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads((ROOT / "manifest.template.json").read_text())
            manifest["capabilities"]["skills"][0]["bundle_ref"] = "/tmp/skill"
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            errors = validate_bundle(ROOT / "SKILL.md", path)
            self.assertTrue(any("bundle_ref" in error for error in errors), errors)

    def test_cli_validation(self):
        result = subprocess.run([sys.executable, str(ROOT / "validate.py")], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Skill bundle contract OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
