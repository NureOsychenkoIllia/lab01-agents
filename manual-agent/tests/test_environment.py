from agent.environment import NOT_FOUND, check_property, lookup_http_method


def test_existing_method():
    assert lookup_http_method("get").startswith("get:")


def test_name_is_normalized():
    assert lookup_http_method(" PUT ").startswith("put:")
    assert lookup_http_method("Patch").startswith("patch:")


def test_unknown_method():
    result = lookup_http_method("trace")
    assert result.startswith(NOT_FOUND)
    assert "trace" in result


def test_safe_property_known_and_unknown_method():
    assert check_property("head", "safe").startswith("head: safe=yes")
    assert check_property("post", "SAFE").startswith("post: safe=no")
    assert check_property("connect", "safe").startswith(NOT_FOUND)


def test_idempotent_property():
    assert check_property("put", "idempotent").startswith("put: idempotent=yes")
    assert check_property("patch", "idempotent").startswith("patch: idempotent=no")


def test_unknown_property():
    assert check_property("get", "cacheable").startswith(NOT_FOUND)
