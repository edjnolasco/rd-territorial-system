from fastapi.testclient import TestClient

from rd_territorial_system.api.main import app

client = TestClient(app)


def test_openapi_schema_available():
    r = client.get("/openapi.json")

    assert r.status_code == 200

    schema = r.json()
    assert schema["openapi"].startswith("3.")
    assert "info" in schema
    assert schema["info"]["title"] == "RD Territorial System API"
    assert "paths" in schema
    assert isinstance(schema["paths"], dict)


def test_openapi_contains_core_api_paths():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    expected_keywords = [
        "health",
        "catalog",
        "resolve",
        "batch",
        "explain",
        "search",
        "entities",
    ]

    all_paths = "\n".join(paths.keys())

    for keyword in expected_keywords:
        assert keyword in all_paths


def test_openapi_paths_are_versioned():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    api_paths = [
        path for path in paths
        if path not in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    ]

    assert api_paths

    for path in api_paths:
        assert path.startswith("/api/v1/")


def test_openapi_operations_have_tags():
    schema = client.get("/openapi.json").json()

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue

            assert "tags" in operation, f"Missing tags in {method} {path}"
            assert isinstance(operation["tags"], list)
            assert operation["tags"]


def test_openapi_operations_have_responses():
    schema = client.get("/openapi.json").json()

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue

            assert "responses" in operation, f"Missing responses in {method} {path}"
            assert isinstance(operation["responses"], dict)
            assert operation["responses"]


def test_openapi_has_component_schemas():
    schema = client.get("/openapi.json").json()

    assert "components" in schema
    assert "schemas" in schema["components"]
    assert isinstance(schema["components"]["schemas"], dict)
    assert schema["components"]["schemas"]


def test_health_endpoint_matches_openapi_contract():
    r = client.get("/api/v1/health")

    assert r.status_code == 200

    data = r.json()
    assert data == {"status": "ok"}


def test_catalog_stats_endpoint_matches_openapi_contract():
    r = client.get("/api/v1/catalog/stats")

    assert r.status_code == 200

    data = r.json()

    required_fields = {
        "catalog_version",
        "generated_at",
        "entity_count",
        "province_count",
        "source_of_truth",
    }

    assert required_fields.issubset(data.keys())
    assert data["entity_count"] == 20773
    assert data["province_count"] == 32
    assert data["source_of_truth"] == "csv"
    
def test_openapi_declares_expected_tags():
    schema = client.get("/openapi.json").json()

    assert "tags" in schema

    declared_tags = {tag["name"] for tag in schema["tags"]}

    expected_tags = {
        "meta",
        "resolve",
        "batch",
        "explain",
        "search",
        "entities",
    }

    assert expected_tags.issubset(declared_tags)