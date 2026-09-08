import pytest
from django.core.cache import cache

from agent import speech
from agent.models import InterviewLog
from agent.speech import SpeechUnavailable

pytestmark = pytest.mark.django_db

AUDIO = b"ID3\x04\x00fake-mp3-bytes"


@pytest.fixture
def configured(settings):
    settings.ELEVENLABS_API_KEY = "test-key"
    settings.ELEVENLABS_VOICE_ID = "test-voice"
    return settings


@pytest.fixture
def log():
    return InterviewLog.objects.create(
        session_id="0f6f9f2a-52a1-4d0e-9d3f-3b6b6f0a1c22",
        question="Do you have a degree?",
        answer="I don't have a bachelor's degree. I built the career from the work.",
        ip_hash="x" * 64,
    )


def url(log_id):
    return f"/api/interview/{log_id}/speech/"


def test_speaks_a_stored_answer(client, configured, log, monkeypatch):
    calls = []

    def fake_synthesize(text):
        calls.append(text)
        return AUDIO

    monkeypatch.setattr("agent.views.synthesize", fake_synthesize)

    response = client.get(url(log.id))

    assert response.status_code == 200
    assert response["Content-Type"] == "audio/mpeg"
    assert response.content == AUDIO
    # It spoke the stored answer, not anything the caller supplied.
    assert calls == [log.answer]


def test_repeat_play_is_served_from_cache(client, configured, log, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "agent.views.synthesize", lambda text: (calls.append(text), AUDIO)[1]
    )

    client.get(url(log.id))
    client.get(url(log.id))

    # Replaying an answer must not bill a second time.
    assert len(calls) == 1


def test_unknown_answer_is_404(client, configured):
    assert client.get(url(999_999)).status_code == 404


def test_returns_503_when_not_configured(client, settings, log):
    settings.ELEVENLABS_API_KEY = ""
    settings.ELEVENLABS_VOICE_ID = ""

    response = client.get(url(log.id))

    assert response.status_code == 503
    assert response.json()["code"] == "speech_unavailable"


def test_returns_503_when_the_vendor_fails(client, configured, log, monkeypatch):
    def explode(text):
        raise SpeechUnavailable("vendor down")

    monkeypatch.setattr("agent.views.synthesize", explode)

    response = client.get(url(log.id))

    assert response.status_code == 503
    assert response.json()["code"] == "speech_unavailable"


def test_throttled_after_sixty_plays(client, configured, log, monkeypatch):
    monkeypatch.setattr("agent.views.synthesize", lambda text: AUDIO)

    for _ in range(60):
        assert client.get(url(log.id)).status_code == 200

    assert client.get(url(log.id)).status_code == 429


def test_interview_response_carries_the_speech_fields(client, fake_claude, configured):
    body = client.post(
        "/api/interview/",
        {"question": "What have you shipped?"},
        content_type="application/json",
    ).json()

    assert body["speech_available"] is True
    assert body["log_id"] == InterviewLog.objects.first().id


def test_speech_is_reported_unavailable_when_unconfigured(client, fake_claude, settings):
    settings.ELEVENLABS_API_KEY = ""
    settings.ELEVENLABS_VOICE_ID = ""

    body = client.post(
        "/api/interview/",
        {"question": "What have you shipped?"},
        content_type="application/json",
    ).json()

    assert body["speech_available"] is False


def test_synthesize_refuses_when_unconfigured(settings):
    settings.ELEVENLABS_API_KEY = ""
    settings.ELEVENLABS_VOICE_ID = ""

    with pytest.raises(SpeechUnavailable):
        speech.synthesize("anything")


def test_synthesize_refuses_an_over_long_answer(configured, settings):
    settings.SPEECH_MAX_CHARS = 10

    with pytest.raises(SpeechUnavailable):
        speech.synthesize("x" * 11)


def test_cache_key_changes_with_the_voice(client, configured, log, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "agent.views.synthesize", lambda text: (calls.append(text), AUDIO)[1]
    )

    client.get(url(log.id))
    cache.clear()
    configured.ELEVENLABS_VOICE_ID = "a-different-voice"
    client.get(url(log.id))

    assert len(calls) == 2
