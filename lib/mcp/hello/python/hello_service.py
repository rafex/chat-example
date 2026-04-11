from __future__ import annotations

from datetime import datetime, timezone


GREETINGS = {
    "en": "Hello",
    "zh": "Ni hao",
    "hi": "Namaste",
    "es": "Hola",
    "fr": "Bonjour",
    "ar": "Marhaban",
    "bn": "Nomoskar",
    "pt": "Ola",
    "ru": "Privet",
    "ur": "Assalam o Alaikum",
}


def get_supported_languages() -> list[str]:
    return sorted(GREETINGS.keys())


def get_supported_language_count() -> int:
    return len(GREETINGS)


def build_hello_payload(name: str | None, lang: str | None, ip: str = "127.0.0.1") -> dict[str, object]:
    normalized_lang = normalize_lang(lang)
    greeting = GREETINGS[normalized_lang]
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC+00:00")

    if name:
        return {
            "message": f"{greeting} {name}!",
            "timestamp": timestamp,
            "ip": ip,
            "lang": normalized_lang,
            "has_name": True,
            "name": name,
        }

    return {
        "message": f"{greeting}!",
        "timestamp": timestamp,
        "ip": ip,
        "lang": normalized_lang,
        "has_name": False,
    }


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    normalized = lang.strip().lower()
    if normalized in GREETINGS:
        return normalized
    return "en"
