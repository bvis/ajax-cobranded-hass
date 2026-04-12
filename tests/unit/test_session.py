"""Tests for gRPC session management."""

from __future__ import annotations

import hashlib

from custom_components.ajax_cobranded.api.session import AjaxSession


class TestPasswordHashing:
    def test_hash_password(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        result = session._hash_password("mypassword")
        expected = hashlib.sha256(b"mypassword").hexdigest()
        assert result == expected

    def test_hash_password_empty(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        result = session._hash_password("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_password_static(self) -> None:
        result = AjaxSession.hash_password("mypassword")
        expected = hashlib.sha256(b"mypassword").hexdigest()
        assert result == expected

    def test_hash_password_static_matches_instance(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        assert AjaxSession.hash_password("test") == session._hash_password("test")

    def test_set_credentials_hashed(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._email = None
        session._password_hash = None
        expected_hash = hashlib.sha256(b"secret").hexdigest()
        session.set_credentials_hashed("user@example.com", expected_hash)
        assert session._email == "user@example.com"
        assert session._password_hash == expected_hash


class TestTokenConversion:
    def test_bytes_to_hex(self) -> None:
        token_bytes = bytes.fromhex("aabbccdd")
        result = AjaxSession._token_to_hex(token_bytes)
        assert result == "aabbccdd"

    def test_hex_to_bytes(self) -> None:
        result = AjaxSession._token_from_hex("aabbccdd")
        assert result == bytes.fromhex("aabbccdd")


class TestSessionMetadata:
    def test_session_metadata_keys(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "aabbccdd"
        session._user_hex_id = "user123"
        session._device_id = "device-uuid-1"
        session._email = None
        meta = session.get_session_metadata()
        keys = {k for k, v in meta}
        assert "client-session-token" in keys
        assert "a911-user-id" in keys

    def test_device_info_metadata_keys(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._device_id = "device-uuid-1"
        session._app_label = "Ajax Security System"
        meta = session.get_device_info_metadata()
        meta_dict = dict(meta)
        assert meta_dict["client-os"] == "Android"
        assert meta_dict["client-version-major"] == "3.30"
        assert meta_dict["application-label"] == "Ajax Security System"
        assert meta_dict["client-device-type"] == "MOBILE"
        assert meta_dict["client-device-id"] == "device-uuid-1"
        assert meta_dict["client-device-model"] == "Home Assistant"

    def test_device_info_custom_app_label(self) -> None:
        session = AjaxSession(app_label="Protegim")
        session._device_id = "device-uuid-1"
        meta_dict = dict(session.get_device_info_metadata())
        assert meta_dict["application-label"] == "Protegim"

    def test_device_info_has_model(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._device_id = "dev1"
        session._app_label = "Ajax Security System"
        meta = dict(session.get_device_info_metadata())
        assert "client-device-model" in meta
        assert meta["client-device-model"] == "Home Assistant"

    def test_session_metadata_has_user_login(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "tok"
        session._user_hex_id = "uid"
        session._email = "test@example.com"
        session._device_id = "dev1"
        meta = dict(session.get_session_metadata())
        assert meta["client-user-login"] == "test@example.com"
        assert meta["client-user-role"] == "USER"

    def test_combined_metadata(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "aabb"
        session._user_hex_id = "user1"
        session._device_id = "dev1"
        session._app_label = "Ajax Security System"
        session._email = None
        meta = session.get_call_metadata()
        meta_dict = dict(meta)
        assert "client-session-token" in meta_dict
        assert "client-os" in meta_dict
        assert "client-device-model" in meta_dict


class TestAuthState:
    def test_is_authenticated_false_initially(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = None
        session._user_hex_id = None
        assert session.is_authenticated is False

    def test_is_authenticated_true(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "token"
        session._user_hex_id = "user"
        assert session.is_authenticated is True
