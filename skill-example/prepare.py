"""Generate an author-specific public Skill Pack manifest."""
import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--author-id", type=int, required=True, help="Numeric ID from your AutoTask user namespace")
parser.add_argument("--out", default="autotask-skill-pack.json")
args = parser.parse_args()
if args.author_id <= 0:
    parser.error("author ID must be positive")

root = Path(__file__).parent
manifest = json.loads((root / "manifest.template.json").read_text(encoding="utf-8"))
manifest["identity"]["plugin_id"] = f"user-{args.author_id}/repository-review-skill"
Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {args.out}; submit it after reviewing the embedded Skill content.")
