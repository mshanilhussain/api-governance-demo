
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "api-template.yaml"
CATALOGUE = ROOT / "governance" / "catalogue.json"


def main():
    parser = argparse.ArgumentParser(
        description="Create and register a new API."
    )
    parser.add_argument("api_name")
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    name = args.api_name

    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        sys.exit("ERROR: API name must start with a lowercase letter "
                 "and contain only lowercase letters, digits, or hyphens.")

    target_dir = ROOT / "specs" / name
    target_file = target_dir / f"{name}.yaml"

    if not TEMPLATE.is_file():
        sys.exit(f"ERROR: Template not found: {TEMPLATE}")

    if target_dir.exists() or name in json.loads(
        CATALOGUE.read_text(encoding="utf-8")
    ).get("apis", {}):
        sys.exit(f"ERROR: API already exists: {name}")

    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if not isinstance(catalogue.get("apis"), dict):
        sys.exit("ERROR: Catalogue must contain an 'apis' object.")

    # Build the spec from the existing template.
    spec = TEMPLATE.read_text(encoding="utf-8")
    spec = spec.replace("title: API Name", f"title: {json.dumps(args.display_name)}")
    spec = spec.replace(
        "description: API description.",
        f"description: {json.dumps(args.description)}"
    )

    # Create the endpoint-free starter spec and register it as pending.
    entry = {
        "display_name": args.display_name,
        "domain": args.domain,
        "owner": args.owner,
        "specification": f"specs/{name}/{name}.yaml",
        "lifecycle": "Draft",
        "approval_status": "Pending",
        "approved_by": "",
        "approval_reference": "",
        "dependencies": [],
        "postman_spec_id": ""
    }

    target_dir.mkdir(parents=True, exist_ok=False)
    try:
        target_file.write_text(spec, encoding="utf-8")
        catalogue["apis"][name] = entry
        CATALOGUE.write_text(
            json.dumps(catalogue, indent=2) + "\n",
            encoding="utf-8"
        )
    except Exception:
        target_file.unlink(missing_ok=True)
        target_dir.rmdir()
        raise

    print(f"Created specification: {target_file.relative_to(ROOT)}")
    print(f"Registered API: {name}")
    print("Lifecycle: Draft")
    print("Approval status: Pending")

    # Run the existing governance validator.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate-governance.py")],
        cwd=ROOT
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
