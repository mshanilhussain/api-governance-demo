import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING_PATH = ROOT / ".postman" / "api-mappings.yaml"
COLLECTION_LOOKUP = ROOT / "scripts" / "find-postman-collection.py"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_mappings():
    if not MAPPING_PATH.is_file():
        fail(f"Mapping file not found: {MAPPING_PATH}")

    mappings = {}
    current_api = None

    for line in MAPPING_PATH.read_text(encoding="utf-8").splitlines():
        api_match = re.fullmatch(r"  ([A-Za-z0-9_.~-]+):", line)
        spec_match = re.fullmatch(
            r"""    spec_id:\s*["']?([A-Za-z0-9-]+)["']?""",
            line,
        )

        if api_match:
            current_api = api_match.group(1)
        elif spec_match and current_api:
            mappings[current_api] = spec_match.group(1)
            current_api = None

    if not mappings:
        fail("No API mappings were found.")

    return mappings


def find_spec(api_name):
    for suffix in (".yaml", ".yml"):
        candidate = ROOT / "specs" / api_name / f"{api_name}{suffix}"
        if candidate.is_file():
            return candidate.relative_to(ROOT).as_posix()

    fail(f"No specification found for mapped API '{api_name}'.")


def changed_spec_files(base_sha, head_sha):
    result = subprocess.run(
        [
            "git", "diff", "--name-only", "--diff-filter=ACMRT",
            base_sha, head_sha, "--", "specs/",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    return {
        path
        for path in result.stdout.splitlines()
        if re.fullmatch(r"specs/[^/]+/[^/]+\.(yaml|yml)", path)
    }


def collection_exists(spec_id, api_name):
    env = os.environ.copy()

    result = subprocess.run(
        [
            sys.executable,
            str(COLLECTION_LOOKUP),
            spec_id,
            api_name,
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )

    if result.returncode != 0:
        fail(
            f"Collection lookup failed for '{api_name}'. "
            f"Do not create a collection until this is resolved.\n"
            f"{result.stderr.strip()}"
        )

    return bool(result.stdout.strip())


def main():
    if len(sys.argv) not in (3, 4):
        fail(
            "Usage: python scripts/detect-changed-apis.py "
            "BASE_SHA HEAD_SHA [--reconcile-missing]"
        )

    base_sha, head_sha = sys.argv[1:3]
    reconcile_missing = (
        len(sys.argv) == 4 and sys.argv[3] == "--reconcile-missing"
    )

    mappings = load_mappings()
    changed_files = changed_spec_files(base_sha, head_sha)

    changed_apis = {}
    for api_file in sorted(changed_files):
        api_name = api_file.split("/")[1]

        if api_name not in mappings:
            fail(
                f"No Postman spec ID mapping for changed API '{api_name}'. "
                "Add its mapping to .postman/api-mappings.yaml."
            )

        changed_apis[api_name] = api_file

    selected = {}

    # Changed specifications always need processing.
    for api_name, api_file in changed_apis.items():
        selected[api_name] = {
            "api_file": api_file,
            "api_name": api_name,
            "spec_id": mappings[api_name],
            "changed": True,
            "skip": False,
        }

    # On main pushes/manual reconciliation, check all mappings.
    # Add only APIs whose collection is missing.
    if reconcile_missing:
        if not os.environ.get("POSTMAN_API_KEY"):
            fail("POSTMAN_API_KEY is required for collection reconciliation.")

        for api_name, spec_id in mappings.items():
            if api_name in selected:
                continue

            if collection_exists(spec_id, api_name):
                print(
                    f"Existing collection found for unchanged API "
                    f"'{api_name}'; ignoring it.",
                    file=sys.stderr,
                )
                continue

            api_file = find_spec(api_name)
            selected[api_name] = {
                "api_file": api_file,
                "api_name": api_name,
                "spec_id": spec_id,
                "changed": False,
                "skip": False,
            }

            print(
                f"Collection missing for '{api_name}'; "
                "adding it to the processing matrix.",
                file=sys.stderr,
            )

    matrix = list(selected.values())

    if not matrix:
        # GitHub Actions matrix must still contain one entry.
        matrix = [{
            "api_file": "",
            "api_name": "",
            "spec_id": "",
            "changed": False,
            "skip": True,
        }]

    print(json.dumps({"include": matrix}))


if __name__ == "__main__":
    main()