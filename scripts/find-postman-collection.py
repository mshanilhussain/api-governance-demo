
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
    """Fetch every collection generated from the specified Postman spec."""
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
            },
        )

        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            fail(
                f"Postman API returned HTTP {exc.code} while listing "
                f"collections for specification {spec_id}. "
                f"Response: {details}"
            )
        except URLError as exc:
            fail(f"Could not connect to the Postman API: {exc.reason}")
        except TimeoutError:
            fail("The Postman API request timed out.")
        except json.JSONDecodeError:
            fail("The Postman API returned an invalid JSON response.")

        collections.extend(payload.get("collections", []))
        cursor = payload.get("meta", {}).get("nextCursor")

        if not cursor:
            break

    return collections


def select_collection(collections, api_name, spec_id):
    """
    Select a collection only when the result is unambiguous.

    Prefer a single in-sync collection when duplicates exist.
    If there is only one name-matched collection, use it even if
    it is currently out of sync.
    """
    if not collections:
        # An empty result means this spec has no generated collections yet.
        return ""

    matching = [
        collection
        for collection in collections
        if collection.get("name") == api_name
    ]

    if not matching:
        available = ", ".join(
            f"{item.get('name', '<unnamed>')} "
            f"(ID: {item.get('id', '<missing>')}, "
            f"state: {item.get('state', '<unknown>')})"
            for item in collections
        )

        fail(
            f"No generated collection named '{api_name}' was found for "
            f"specification {spec_id}. Existing generated collections: "
            f"{available}. No collection was selected or created."
        )

    in_sync = [
        collection
        for collection in matching
        if collection.get("state") == "in-sync"
    ]

    if len(in_sync) == 1:
        selected = in_sync[0]
    elif len(matching) == 1:
        selected = matching[0]
    else:
        details = "\n".join(
            f"  - Name: {item.get('name', '<unnamed>')}; "
            f"ID: {item.get('id', '<missing>')}; "
            f"state: {item.get('state', '<unknown>')}; "
            f"updatedAt: {item.get('updatedAt', '<unknown>')}"
            for item in matching
        )

        fail(
            f"Multiple collections named '{api_name}' are associated with "
            f"specification {spec_id}, and there is no unique in-sync "
            f"collection. To avoid updating the wrong collection, "
            f"automatic synchronization has stopped.\n{details}\n"
            f"Resolve the duplicate collections in Postman, then rerun "
            f"the workflow."
        )

    collection_id = selected.get("id")

    if not collection_id:
        fail(
            f"The selected collection for '{api_name}' has no ID in "
            f"the Postman API response."
        )

    print(
        f"Selected collection '{api_name}' "
        f"(ID: {collection_id}, state: "
        f"{selected.get('state', 'unknown')}).",
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
        fail(
            "POSTMAN_API_KEY is not set. Add it as a GitHub Actions "
            "repository secret."
        )

    collections = get_generated_collections(spec_id, api_key)
    collection_id = select_collection(collections, api_name, spec_id)

    # Print only the ID to stdout so GitHub Actions can capture it.
    print(collection_id)


if __name__ == "__main__":
    main()