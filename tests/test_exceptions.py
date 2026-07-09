from __future__ import annotations

import pytest

from seojuice._exceptions import (
    APIError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    SEOJuiceError,
    ServerError,
    raise_for_response,
)


# ---------------------------------------------------------------------------
# Inheritance hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_api_error_inherits_from_seojuice_error(self):
        assert issubclass(APIError, SEOJuiceError)

    def test_auth_error_inherits_from_api_error(self):
        assert issubclass(AuthError, APIError)

    def test_forbidden_error_inherits_from_api_error(self):
        assert issubclass(ForbiddenError, APIError)

    def test_not_found_error_inherits_from_api_error(self):
        assert issubclass(NotFoundError, APIError)

    def test_rate_limit_error_inherits_from_api_error(self):
        assert issubclass(RateLimitError, APIError)

    def test_server_error_inherits_from_api_error(self):
        assert issubclass(ServerError, APIError)

    def test_all_specific_errors_are_catchable_as_seojuice_error(self):
        for cls in (
            AuthError,
            ForbiddenError,
            NotFoundError,
            RateLimitError,
            ServerError,
        ):
            assert issubclass(cls, SEOJuiceError)

    def test_api_connection_error_inherits_from_seojuice_error(self):
        from seojuice._exceptions import APIConnectionError

        assert issubclass(APIConnectionError, SEOJuiceError)

    def test_api_timeout_error_inherits_from_api_connection_error(self):
        from seojuice._exceptions import APIConnectionError, APITimeoutError

        assert issubclass(APITimeoutError, APIConnectionError)
        assert issubclass(APITimeoutError, SEOJuiceError)


# ---------------------------------------------------------------------------
# APIError attributes
# ---------------------------------------------------------------------------


class TestAPIErrorAttributes:
    def test_stores_status_code(self):
        err = APIError(400, "bad_request", "Invalid input")
        assert err.status_code == 400

    def test_stores_error_code(self):
        err = APIError(422, "validation_error", "Field required")
        assert err.error_code == "validation_error"

    def test_stores_message(self):
        err = APIError(400, "bad_request", "Missing field 'url'")
        assert err.message == "Missing field 'url'"

    def test_str_representation(self):
        err = APIError(400, "bad_request", "Invalid input")
        assert str(err) == "[400] bad_request: Invalid input"


# ---------------------------------------------------------------------------
# raise_for_response
# ---------------------------------------------------------------------------


class TestRaiseForResponse:
    @pytest.mark.parametrize("status", [200, 201, 204, 301, 302, 399])
    def test_does_nothing_for_status_below_400(self, status: int):
        raise_for_response(status, {"error": "ignored", "message": "ignored"})

    def test_raises_auth_error_for_401(self):
        with pytest.raises(AuthError) as exc_info:
            raise_for_response(401, {"error": "unauthorized", "message": "Bad token"})
        assert exc_info.value.status_code == 401
        assert exc_info.value.error_code == "unauthorized"
        assert exc_info.value.message == "Bad token"

    def test_raises_forbidden_error_for_403(self):
        with pytest.raises(ForbiddenError) as exc_info:
            raise_for_response(403, {"error": "forbidden", "message": "Not allowed"})
        assert exc_info.value.status_code == 403

    def test_raises_not_found_error_for_404(self):
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_response(
                404, {"error": "not_found", "message": "No such resource"}
            )
        assert exc_info.value.status_code == 404

    def test_raises_rate_limit_error_for_429(self):
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_response(429, {"error": "rate_limited", "message": "Slow down"})
        assert exc_info.value.status_code == 429

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_raises_server_error_for_5xx(self, status: int):
        with pytest.raises(ServerError) as exc_info:
            raise_for_response(status, {"error": "server_error", "message": "Oops"})
        assert exc_info.value.status_code == status

    @pytest.mark.parametrize("status", [400, 422, 409, 410, 415])
    def test_raises_api_error_for_other_4xx(self, status: int):
        with pytest.raises(APIError) as exc_info:
            raise_for_response(status, {"error": "bad_request", "message": "Nope"})
        assert exc_info.value.status_code == status
        # Ensure it is NOT one of the specific subclasses
        assert type(exc_info.value) is APIError

    def test_uses_defaults_when_body_keys_missing(self):
        with pytest.raises(APIError) as exc_info:
            raise_for_response(400, {})
        assert exc_info.value.error_code == "unknown_error"
        assert exc_info.value.message == "An unexpected error occurred"

    def test_handles_non_dict_body_gracefully_via_caller(self):
        """The function expects a dict; callers pass {} for non-dict bodies."""
        with pytest.raises(APIError):
            raise_for_response(500, {})
