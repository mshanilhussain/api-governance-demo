#!/usr/bin/env python3

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else ROOT / "governance" / "catalogue.json"
)

VALID_LIFECYCLES = {
    "Draft", "Review", "Approved", "Published", "Deprecated"
}

REQUIRED_FIELDS = [
    "display_name",
    "domain",
    "owner",
    "specification",
    "lifecycle",
    "dependencies",
]


def main():
    errors = []

    try:
        data = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: Cannot read governance catalogue: {exc}")
        return 1

    apis = data.get("apis")

    if not isinstance(apis, dict) or not apis:
        print("FAIL: Catalogue must contain at least one API.")
        return 1

    for name, api in apis.items():
        if not isinstance(api, dict):
            errors.append(f"{name}: API entry must be an object.")
            continue

        for field in REQUIRED_FIELDS:
            if field not in api or api[field] in ("", None):
                errors.append(f"{name}: Missing required field '{field}'.")

        lifecycle = api.get("lifecycle")

        if lifecycle and lifecycle not in VALID_LIFECYCLES:
            errors.append(f"{name}: Invalid lifecycle '{lifecycle}'.")

        spec = api.get("specification")
        if spec:
            spec_path = (ROOT / spec).resolve()

            if not spec_path.is_relative_to(ROOT.resolve()):
                errors.append(f"{name}: Specification path escapes repository.")
            elif not spec_path.is_file():
                errors.append(f"{name}: Specification not found: {spec}")

        dependencies = api.get("dependencies", [])
        if not isinstance(dependencies, list):
            errors.append(f"{name}: Dependencies must be a list.")
        else:
            for dependency in dependencies:
                if dependency not in apis:
                    errors.append(
                        f"{name}: Unknown dependency '{dependency}'."
                    )

        if lifecycle == "Published":
            if api.get("approval_status") != "Approved":
                errors.append(
                    f"{name}: Publication blocked; approval_status must be Approved."
                )

            if not api.get("approved_by"):
                errors.append(
                    f"{name}: Publication blocked; approved_by is required."
                )

            if not api.get("approval_reference"):
                errors.append(
                    f"{name}: Publication blocked; approval_reference is required."
                )

    if errors:
        print("GOVERNANCE VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GOVERNANCE VALIDATION PASSED")
    print(f"Validated {len(apis)} API(s).")

    for name, api in apis.items():
        print(f"- {name}: {api['lifecycle']} | Owner: {api['owner']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
