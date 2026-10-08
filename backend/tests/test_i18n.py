import json
from pathlib import Path

import pytest

from app.i18n import load_translations, t

I18N_DIR = Path(__file__).resolve().parent.parent / "app" / "i18n"


def test_ar_and_fr_files_exist():
    assert (I18N_DIR / "ar.json").exists()
    assert (I18N_DIR / "fr.json").exists()


def test_ar_and_fr_have_identical_key_sets():
    ar = json.loads((I18N_DIR / "ar.json").read_text(encoding="utf-8"))
    fr = json.loads((I18N_DIR / "fr.json").read_text(encoding="utf-8"))
    missing_in_fr = ar.keys() - fr.keys()
    missing_in_ar = fr.keys() - ar.keys()
    assert not missing_in_fr, f"keys missing in fr.json: {missing_in_fr}"
    assert not missing_in_ar, f"keys missing in ar.json: {missing_in_ar}"


def test_t_returns_arabic_by_default_key():
    load_translations.cache_clear()
    result = t("errors.not_found", "ar")
    translations = load_translations()
    assert result == translations["ar"]["errors.not_found"]


def test_t_substitutes_params():
    result = t("priority.people_affected", "ar", count=42)
    assert "42" in result


def test_t_falls_back_to_arabic_for_unknown_language():
    result = t("errors.not_found", "en")
    translations = load_translations()
    assert result == translations["ar"]["errors.not_found"]


def test_t_raises_on_unknown_key():
    with pytest.raises(KeyError):
        t("this.key.does.not.exist", "ar")
