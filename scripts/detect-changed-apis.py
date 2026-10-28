
import json
import re
import subprocess
import sys
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main():
    if len(sys.argv) != 3:
        fail(
            "Usage: python scripts/detect-changed-apis.py BASE_SHA HEAD_SHA"
        )

    base_sha, head_sha = sys.argv[1:3]

    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMRT",
            base_sha,
            head_sha,
            "--",
            "specs/",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    changed_files = sorted(
        {
            path
            for path in result.stdout.splitlines()
            if re.fullmatch(
                r"specs/[^/]+/[^/]+\.(yaml|yml)",
                path,
            )
        }
    )

    mapping_path = Path(".postman/api-mappings.yaml")

    if not mapping_path.is_file():
        fail(f"Postman mapping file not found: {mapping_path}")

    mapping_text = mapping_path.read_text(encoding="utf-8")

    mappings = {}
    current_api = None

    for line in mapping_text.splitlines():
        api_match = re.fullmatch(
            r"  ([A-Za-z0-9_.~-]+):",
            line,
        )

        spec_match = re.fullmatch(
            r"""    spec_id:\s*["']?([A-Za-z0-9-]+)["']?""",
            line,
        )

        if api_match:
            current_api = api_match.group(1)
        elif spec_match and current_api:
            mappings[current_api] = spec_match.group(1)
            current_api = None

    matrix = []

    for api_file in changed_files:
        api_name = api_file.split("/")[1]

        if api_name not in mappings:
            fail(
                f"No Postman Spec ID mapping for API '{api_name}'. "
                "Add its mapping to .postman/api-mappings.yaml "
                "before merging."
            )

        matrix.append(
            {
                "api_file": api_file,
                "api_name": api_name,
                "spec_id": mappings[api_name],
                "skip": False,
            }
        )

    if not matrix:
        matrix = [
            {
                "api_file": "",
                "api_name": "",
                "spec_id": "",
                "skip": True,
            }
        ]

    print(json.dumps({"include": matrix}))


if __name__ == "__main__":
    main()