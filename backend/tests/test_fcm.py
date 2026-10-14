from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.services import fcm


def _settings(**overrides) -> Settings:
    return Settings(
        database_url="postgresql://x",
        jwt_secret="x",
        **overrides,
    )


def test_send_push_is_a_noop_when_firebase_not_configured():
    fcm._firebase_app.cache_clear()
    settings = _settings(fcm_credentials_json="")

    # No firebase_admin call should happen at all — nothing to mock means
    # nothing must be mocked for this to pass without raising.
    fcm.send_push(settings, ["token-1"], "title", "body")


def test_send_push_is_a_noop_with_no_tokens():
    fcm._firebase_app.cache_clear()
    settings = _settings(fcm_credentials_json="")

    fcm.send_push(settings, [], "title", "body")


def test_send_push_calls_firebase_messaging_when_configured():
    fcm._firebase_app.cache_clear()
    fake_credentials_json = '{"type": "service_account", "project_id": "w4f-test"}'
    settings = _settings(fcm_credentials_json=fake_credentials_json)

    with (
        patch.object(fcm.credentials, "Certificate") as mock_certificate,
        patch.object(fcm.firebase_admin, "initialize_app") as mock_init_app,
        patch.object(fcm.messaging, "send_each") as mock_send,
    ):
        mock_init_app.return_value = MagicMock()
        fcm.send_push(settings, ["token-1", "token-2"], "عنوان", "نص الإشعار", {"k": "v"})

    mock_certificate.assert_called_once_with({"type": "service_account", "project_id": "w4f-test"})
    mock_init_app.assert_called_once()
    mock_send.assert_called_once()
    sent_messages = mock_send.call_args.args[0]
    assert [m.token for m in sent_messages] == ["token-1", "token-2"]
    assert all(m.notification.title == "عنوان" for m in sent_messages)
    assert all(m.data == {"k": "v"} for m in sent_messages)


def test_send_push_never_raises_when_firebase_call_fails():
    fcm._firebase_app.cache_clear()
    fake_credentials_json = '{"type": "service_account", "project_id": "w4f-test"}'
    settings = _settings(fcm_credentials_json=fake_credentials_json)

    with (
        patch.object(fcm.credentials, "Certificate"),
        patch.object(fcm.firebase_admin, "initialize_app", return_value=MagicMock()),
        patch.object(fcm.messaging, "send_each", side_effect=RuntimeError("boom")),
    ):
        fcm.send_push(settings, ["token-1"], "title", "body")
