"""Backend i18n: machine values in, localized strings out, only at the edge.

Routes and services never build UI sentences themselves — they pass a
translation key plus params to t(key, lang, **params). Supported languages:
ar (default) and fr. Any other language falls back to ar.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_I18N_DIR = Path(__file__).resolve().parent
_SUPPORTED_LANGUAGES = ("ar", "fr")
_DEFAULT_LANGUAGE = "ar"


@lru_cache
def load_translations() -> dict[str, dict[str, str]]:
    return {
        lang: json.loads((_I18N_DIR / f"{lang}.json").read_text(encoding="utf-8"))
        for lang in _SUPPORTED_LANGUAGES
    }


def t(key: str, lang: str, **params: Any) -> str:
    translations = load_translations()
    resolved_lang = lang if lang in translations else _DEFAULT_LANGUAGE
    try:
        template = translations[resolved_lang][key]
    except KeyError:
        raise KeyError(f"missing i18n key {key!r} for language {resolved_lang!r}") from None
    return template.format(**params) if params else template
