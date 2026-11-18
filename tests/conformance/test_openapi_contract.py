"""OpenAPI contract tests: document validity, published operations, Schemathesis.

Schemathesis runs only safe (GET) operations against the in-memory backend with a
member token, so it needs no Docker and cannot modify real data.
"""

import pytest
import schemathesis
from openapi_spec_validator import validate
from starlette.testclient import TestClient

from app.main import app
from tests.conftest import TEST_ADMIN_TOKEN, TEST_MEMBER_TOKEN
from schemathesis.specs.openapi.checks import allow_header_conformance  # may not be needed

# (path, method) -> (expected success status, expected error statuses)
EXPECTED_OPERATIONS = {
    ("/books", "get"): ("200", {"401"}),
    ("/books", "post"): ("201", {"401", "403", "404", "409", "422"}),
    ("/books/{book_id}", "get"): ("200", {"401", "404", "422"}),
    ("/books/{book_id}", "put"): ("200", {"401", "403", "404", "409", "422"}),
    ("/books/{book_id}", "delete"): ("204", {"401", "403", "404", "422"}),
    ("/members", "get"): ("200", {"401"}),
    ("/members", "post"): ("201", {"401", "403", "409", "422"}),
    ("/members/{member_id}", "get"): ("200", {"401", "404", "422"}),
    ("/members/{member_id}", "put"): ("200", {"401", "403", "404", "409", "422"}),
    ("/members/{member_id}", "delete"): ("204", {"401", "403", "404", "409", "422"}),
    ("/members/{member_id}/books", "get"): ("200", {"401", "404", "422"}),
}


@pytest.fixture(scope="module")
def openapi_schema() -> dict:
    return app.openapi()


def test_generated_openapi_document_is_valid(openapi_schema):
    # Raises if the document violates the OpenAPI specification.
    validate(openapi_schema)


def test_served_openapi_json_matches_generated_document(memory_client, openapi_schema):
    response = memory_client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == openapi_schema


@pytest.mark.parametrize(("path", "method"), list(EXPECTED_OPERATIONS))
def test_operation_publishes_expected_statuses(openapi_schema, path, method):
    success, errors = EXPECTED_OPERATIONS[(path, method)]
    responses = set(openapi_schema["paths"][path][method]["responses"])
    assert success in responses
    assert errors <= responses


@pytest.mark.parametrize(
    ("path", "method"),
    [("/books", "post"), ("/books/{book_id}", "put"),
     ("/members", "post"), ("/members/{member_id}", "put")],
)
def test_write_operations_publish_json_request_schema(openapi_schema, path, method):
    body = openapi_schema["paths"][path][method]["requestBody"]
    assert "$ref" in body["content"]["application/json"]["schema"]


@pytest.mark.parametrize(
    ("path", "model"),
    [("/books", "BookResponse"), ("/members", "MemberResponse")],
)
def test_collection_get_publishes_array_of_response_schema(openapi_schema, path, model):
    schema = openapi_schema["paths"][path]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert schema["type"] == "array"
    assert schema["items"]["$ref"].endswith(f"/{model}")


def test_request_schemas_forbid_unknown_fields(openapi_schema):
    schemas = openapi_schema["components"]["schemas"]
    for name in ("BookRequest", "MemberRequest"):
        assert schemas[name].get("additionalProperties") is False


def test_no_documented_path_is_missing_from_expected_operations(openapi_schema):
    documented = {
        (path, method)
        for path, item in openapi_schema["paths"].items()
        if path.startswith(("/books", "/members"))
        for method in item
    }
    assert documented == set(EXPECTED_OPERATIONS)


# --- Schemathesis: generated requests against safe operations ----------------

@pytest.fixture(scope="module", autouse=True)
def running_memory_app():
    """Run the app lifespan (in-memory backend) so services and settings exist.

    Schemathesis calls the ASGI app directly and does not run startup itself.
    """
    patch = pytest.MonkeyPatch()
    patch.setenv("STORAGE_BACKEND", "memory")
    patch.setenv("DEMO_MEMBER_TOKEN", TEST_MEMBER_TOKEN)
    patch.setenv("DEMO_ADMIN_TOKEN", TEST_ADMIN_TOKEN)
    patch.delenv("DATABASE_URL", raising=False)
    with TestClient(app):
        yield
    patch.undo()


# Only GET operations are generated: they cannot change stored data.
schema = schemathesis.openapi.from_asgi("/openapi.json", app).include(method="GET")


@schema.parametrize()
def test_safe_operations_conform_to_openapi_contract(case):
    # "Allow" header probing (ST205) fails because Starlette reports only one
    # method per path when several share it; that is framework behavior, not a
    # response-contract problem.
    case.call_and_validate(
        headers={"Authorization": f"Bearer {TEST_MEMBER_TOKEN}"},
        excluded_checks=[schemathesis.checks.allow_header_conformance],
    )