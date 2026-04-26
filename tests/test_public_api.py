from rd_territorial_system import batch_resolve, resolve


def test_public_resolve_api():
    result = resolve("SDE")

    assert isinstance(result, dict)
    assert result["status"] in {"matched", "ambiguous", "not_found", "invalid_input"}
    assert "catalog_version" in result


def test_public_batch_resolve_api():
    results = batch_resolve(["SDE", "Villa Mella"])

    assert isinstance(results, list)
    assert len(results) == 2

    for result in results:
        assert result["status"] in {
            "matched",
            "ambiguous",
            "not_found",
            "invalid_input",
        }
        assert "catalog_version" in result