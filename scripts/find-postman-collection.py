
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE_URL = "https://api.postman.com"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def get_generated_collections(spec_id, api_key):
    """Fetch all collections generated from a Postman specification."""
    collections = []
    cursor = None

    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor

        url = (
            f"{API_BASE_URL}/specs/{spec_id}/generations/collection?"
            f"{urlencode(params)}"
        )

        request = Request(
            url,
            headers={
                "X-Api-Key": api_key,
                "Accept": "application/json",
                "User-Agent": "api-governance-demo/1.0",
            },
        )

        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            fail(
                f"Postman API returned HTTP {exc.code}: {details}"
            )
        except (URLError, TimeoutError) as exc:
            fail(f"Could not retrieve Postman collections: {exc}")
        except json.JSONDecodeError:
            fail("Postman returned an invalid JSON response.")

        page_collections = payload.get("collections")
        if not isinstance(page_collections, list):
            fail(
                "Postman API response did not contain a valid "
                "'collections' list. Cannot safely determine whether "
                "a collection exists."
            )

        collections.extend(page_collections)
        cursor = payload.get("meta", {}).get("nextCursor")

        if not cursor:
            break

    return collections


def select_collection(collections, api_name, spec_id):
    """Select a collection only when the result is unambiguous."""
    matching = [
        item
        for item in collections
        if item.get("name") == api_name
    ]

    if not matching:
        if collections:
            available = "\n".join(
                f"  - {item.get('name', '<unnamed>')} "
                f"(ID: {item.get('id', '<missing>')})"
                for item in collections
            )
            fail(
                f"No collection named '{api_name}' was found for "
                f"specification {spec_id}. Collections returned:\n"
                f"{available}"
            )

        # Empty list: no generated collections were returned.
        # The workflow may create the initial collection.
        return ""

    if len(matching) > 1:
        details = "\n".join(
            f"  - ID: {item.get('id', '<missing>')}; "
            f"state: {item.get('state', '<unknown>')}; "
            f"updatedAt: {item.get('updatedAt', '<unknown>')}"
            for item in matching
        )
        fail(
            f"Found {len(matching)} collections named '{api_name}' "
            f"for specification {spec_id}. No collection was selected.\n"
            f"{details}\n"
            "Resolve the duplicates in Postman, then rerun the workflow."
        )

    collection_id = matching[0].get("id")
    if not collection_id:
        fail("The matching collection has no ID in the API response.")

    print(
        f"Selected collection '{api_name}' (ID: {collection_id}).",
        file=sys.stderr,
    )
    return collection_id


def main():
    if len(sys.argv) != 3:
        fail(
            "Usage: python scripts/find-postman-collection.py "
            "SPEC_ID API_NAME"
        )

    spec_id, api_name = sys.argv[1:3]
    api_key = os.environ.get("POSTMAN_API_KEY")

    if not api_key:
        fail("POSTMAN_API_KEY environment variable is not set.")

    collections = get_generated_collections(spec_id, api_key)
    collection_id = select_collection(
        collections,
        api_name,
        spec_id,
    )
    print(collection_id)


if __name__ == "__main__":
    main()