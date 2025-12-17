import bleach

# Базовий whitelist під Quill
ALLOWED_TAGS = [
    "p", "br",
    "strong", "b", "em", "i", "u",
    "blockquote",
    "ul", "ol", "li",
    "a",
    "h2",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

def sanitize_html(html: str) -> str:
    """
    Clean user HTML input to prevent XSS.
    Keeps formatting but strips scripts, styles, events, etc.
    """
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    # Автоматично робимо лінки безпечними
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
    )

    return cleaned
