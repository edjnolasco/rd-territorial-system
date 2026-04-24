from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


DN_BRISAS_PARENT = "10-01-01-01-01-001-00"
DN_BRISAS_CODE = "10-01-01-01-01-001-03"


def test_resolve_distrito_nacional_province():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Distrito Nacional",
            "level": "province",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["input"] == "Distrito Nacional"
    assert payload["normalized_text"] == "distrito nacional"
    assert payload["canonical_name"] == "Distrito Nacional"
    assert payload["entity_id"] == "10-01-00-00-00-000-00"
    assert payload["entity_type"] == "province"
    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["match_strategy"] == "exact_catalog"
    assert payload["rules_version"] == "v1"
    assert payload["entity"]["composite_code"] == "10-01-00-00-00-000-00"


def test_resolve_dn_alias_province():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "DN",
            "level": "province",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["normalized_text"] == "distrito nacional"
    assert payload["canonical_name"] == "Distrito Nacional"
    assert payload["entity_type"] == "province"
    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert "applied alias" in " ".join(payload["trace"]).lower()


def test_resolve_los_peralejos_barrio_paraje():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Los Peralejos",
            "level": "barrio_paraje",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["canonical_name"] == "Los Peralejos"
    assert payload["entity_id"] == "10-01-01-01-01-001-00"
    assert payload["entity_type"] == "barrio_paraje"
    assert payload["matched"] is True
    assert payload["status"] == "matched"


def test_resolve_brisas_del_norte_without_parent_is_ambiguous():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Brisas del Norte",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is False
    assert payload["status"] == "ambiguous"
    assert payload["entity"] is None
    assert len(payload["candidates"]) >= 2

    candidate_codes = {item["composite_code"] for item in payload["candidates"]}
    assert DN_BRISAS_CODE in candidate_codes


def test_resolve_brisas_del_norte_sub_barrio_with_parent():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Brisas del Norte",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": DN_BRISAS_PARENT,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["canonical_name"] == "Brisas del Norte"
    assert payload["entity_id"] == DN_BRISAS_CODE
    assert payload["entity_type"] == "sub_barrio"
    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["entity"]["parent_composite_code"] == DN_BRISAS_PARENT


def test_resolve_not_found_returns_200_with_not_found_payload():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Sector Inventado DN",
            "level": "barrio_paraje",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is False
    assert payload["status"] == "not_found"
    assert payload["canonical_name"] is None
    assert payload["entity"] is None
    assert payload["candidates"] == []


def test_resolve_ambiguous_villa_maria():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Villa María",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is False
    assert payload["status"] == "ambiguous"
    assert payload["entity"] is None
    assert len(payload["candidates"]) >= 2

    candidate_codes = {item["composite_code"] for item in payload["candidates"]}
    assert "10-01-01-01-01-002-07" in candidate_codes
    assert "10-01-01-01-01-056-02" in candidate_codes
    assert "10-01-01-01-01-063-05" in candidate_codes


def test_resolve_villa_maria_disambiguated_by_parent_code():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Villa María",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": "10-01-01-01-01-002-00",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["canonical_name"] == "Villa María"
    assert payload["entity_id"] == "10-01-01-01-01-002-07"
    assert payload["entity"]["parent_composite_code"] == "10-01-01-01-01-002-00"


def test_resolve_strict_not_found_returns_400():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "No Existe DN",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": True,
            "parent_code": None,
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert "detail" in payload


def test_resolve_strict_ambiguous_returns_400():
    response = client.post(
        "/api/v1/resolve",
        json={
            "text": "Villa María",
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": True,
            "parent_code": None,
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert "detail" in payload


def test_batch_resolve_mixed_cases():
    response = client.post(
        "/api/v1/batch-resolve",
        json={
            "items": [
                "Distrito Nacional",
                "Los Peralejos",
                "Brisas del Norte",
                "Sector Inventado DN",
            ],
            "level": None,
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload, list)
    assert len(payload) == 4

    assert payload[0]["matched"] is True
    assert payload[0]["canonical_name"] == "Distrito Nacional"

    assert payload[1]["matched"] is True
    assert payload[1]["canonical_name"] == "Los Peralejos"

    assert payload[2]["matched"] is False
    assert payload[2]["status"] == "ambiguous"

    assert payload[3]["matched"] is False
    assert payload[3]["status"] == "not_found"


def test_batch_resolve_with_level_sub_barrio_without_parent():
    response = client.post(
        "/api/v1/batch-resolve",
        json={
            "items": ["Villa María", "Brisas del Norte"],
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 2
    assert payload[0]["status"] == "ambiguous"
    assert payload[1]["status"] == "ambiguous"


def test_batch_resolve_with_level_sub_barrio_and_parent():
    response = client.post(
        "/api/v1/batch-resolve",
        json={
            "items": ["Brisas del Norte"],
            "level": "sub_barrio",
            "rules_version": "v1",
            "strict": False,
            "parent_code": DN_BRISAS_PARENT,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["status"] == "matched"
    assert payload[0]["canonical_name"] == "Brisas del Norte"
    assert payload[0]["entity_id"] == DN_BRISAS_CODE


def test_explain_distrito_nacional():
    response = client.post(
        "/api/v1/explain",
        json={
            "text": "Distrito Nacional",
            "level": "province",
            "rules_version": "v1",
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["input"] == "Distrito Nacional"
    assert payload["normalized_text"] == "distrito nacional"
    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["match_strategy"] == "exact_catalog"
    assert isinstance(payload["trace"], list)
    assert len(payload["trace"]) >= 1
    assert payload["entity"]["name"] == "Distrito Nacional"


def test_explain_alias_dn():
    response = client.post(
        "/api/v1/explain",
        json={
            "text": "DN",
            "level": "province",
            "rules_version": "v1",
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["entity"]["name"] == "Distrito Nacional"
    assert "alias" in " ".join(payload["trace"]).lower()


def test_explain_ambiguous_villa_maria():
    response = client.post(
        "/api/v1/explain",
        json={
            "text": "Villa María",
            "level": "sub_barrio",
            "rules_version": "v1",
            "parent_code": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is False
    assert payload["status"] == "ambiguous"
    assert payload["entity"] is None
    assert len(payload["candidates"]) >= 2
    assert any("ambiguous" in item.lower() for item in payload["trace"])


def test_explain_parent_code_disambiguates():
    response = client.post(
        "/api/v1/explain",
        json={
            "text": "San Miguel",
            "level": "sub_barrio",
            "rules_version": "v1",
            "parent_code": "10-01-01-01-01-065-00",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["matched"] is True
    assert payload["status"] == "matched"
    assert payload["entity"]["name"] == "San Miguel"
    assert payload["entity"]["composite_code"] == "10-01-01-01-01-065-02"