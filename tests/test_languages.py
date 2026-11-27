from app.languages import SUPPORTED_LANGUAGES

def test_eleven_languages_are_configured():
    assert len(SUPPORTED_LANGUAGES) == 11
    assert SUPPORTED_LANGUAGES["en"] == "English"
    assert SUPPORTED_LANGUAGES["pl"] == "Polish"
