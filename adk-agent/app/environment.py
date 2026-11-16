"""Середовище агента: перевірені факти про методи HTTP.

Детермінований код без LLM. Джерела фактів:
- RFC 9110 «HTTP Semantics» (IETF, 2022): розд. 9.2.1 — безпечні методи,
  розд. 9.2.2 — ідемпотентні методи, розд. 9.3.1 GET, 9.3.2 HEAD, 9.3.3 POST,
  9.3.4 PUT, 9.3.5 DELETE, 9.3.7 OPTIONS;
- RFC 5789 «PATCH Method for HTTP» (IETF, 2010): розд. 1–2 — PATCH не є безпечним,
  а ідемпотентність залежить від документу змін.

Метод TRACE (RFC 9110, розд. 9.3.8) навмисно відсутній у середовищі: він використовується
як запит типу D — про об'єкт, якого в середовищі немає.
"""

HTTP_METHODS: dict[str, str] = {
    "get": (
        "GET запитує передачу поточного подання цільового ресурсу; тіло запиту не має "
        "визначеної семантики. Метод безпечний і ідемпотентний: повторний виклик не змінює "
        "стан ресурсу (RFC 9110, розд. 9.3.1)."
    ),
    "head": (
        "HEAD ідентичний GET, але сервер не надсилає тіло відповіді — лише статус і "
        "заголовки, тому метод застосовують для перевірки наявності та метаданих ресурсу. "
        "Безпечний і ідемпотентний (RFC 9110, розд. 9.3.2)."
    ),
    "post": (
        "POST передає подання цільовому ресурсу для обробки за його власною семантикою; "
        "типово створює підпорядкований ресурс і відповідає 201 із заголовком Location. "
        "Не безпечний і не ідемпотентний: два однакові запити можуть створити два ресурси "
        "(RFC 9110, розд. 9.3.3)."
    ),
    "put": (
        "PUT замінює стан цільового ресурсу поданням із запиту; якщо ресурсу немає, він може "
        "бути створений. Ідемпотентний, але не безпечний: повторна передача того самого "
        "подання залишає ресурс у тому самому стані (RFC 9110, розд. 9.3.4)."
    ),
    "patch": (
        "PATCH застосовує до цільового ресурсу часткову зміну, описану в тілі запиту. "
        "Не безпечний і не гарантовано ідемпотентний: результат повторного застосування "
        "залежить від документу змін, наприклад application/merge-patch+json (RFC 5789, розд. 1–2)."
    ),
    "delete": (
        "DELETE видаляє асоціацію між цільовим ресурсом і його поточним станом. "
        "Ідемпотентний, але не безпечний: повторне видалення залишає ресурс у тому самому "
        "стані (RFC 9110, розд. 9.3.5)."
    ),
    "options": (
        "OPTIONS запитує інформацію про комунікаційні опції цільового ресурсу, зокрема "
        "перелік підтримуваних методів у заголовку Allow. Безпечний і ідемпотентний "
        "(RFC 9110, розд. 9.3.7)."
    ),
}

SAFE_METHODS = frozenset({"get", "head", "options"})
"""Безпечні методи лише читають ресурс (RFC 9110, розд. 9.2.1)."""

IDEMPOTENT_METHODS = frozenset({"get", "head", "options", "put", "delete"})
"""Повторний однаковий запит дає той самий ефект (RFC 9110, розд. 9.2.2)."""

NOT_FOUND = "NOT_FOUND"

PROPERTY_FACTS: dict[str, str] = {
    "safe": "safe method is read-only (RFC 9110, 9.2.1)",
    "idempotent": "repeating the same request has the same effect (RFC 9110, 9.2.2)",
}


def normalize_name(name: str) -> str:
    """Зводить «GET», « Get » і «get_method» до ключа «get»."""
    key = name.strip().lower().replace(" ", "-").replace("_", "-")
    return key.removesuffix("-method")


def lookup_http_method(name: str) -> str:
    """Return verified information about one HTTP method.

    Use it when the user asks about a specific HTTP method such as GET, POST, PUT,
    PATCH, DELETE, HEAD or OPTIONS.

    Args:
        name: identifier of the method, for example "get" or "PATCH".

    Returns:
        "<id>: <description>" or a line starting with NOT_FOUND.
    """
    key = normalize_name(name)
    if key not in HTTP_METHODS:
        return f"{NOT_FOUND}: no verified information about '{name}'."
    return f"{key}: {HTTP_METHODS[key]}"


def check_property(method: str, property: str) -> str:
    """Return whether an HTTP method is safe or idempotent.

    Use it when the user asks a yes/no question about safety or idempotence of one or
    several methods.

    Args:
        method: identifier of the method, for example "put" or "PATCH".
        property: property name, exactly "safe" or "idempotent".

    Returns:
        "<id>: <property>=yes; <fact>" or a line starting with NOT_FOUND.
    """
    key = normalize_name(method)
    prop = property.strip().lower()
    if key not in HTTP_METHODS:
        return f"{NOT_FOUND}: no verified information about '{method}'."
    if prop not in PROPERTY_FACTS:
        return f"{NOT_FOUND}: unknown property '{property}', expected one of {sorted(PROPERTY_FACTS)}."
    source = SAFE_METHODS if prop == "safe" else IDEMPOTENT_METHODS
    answer = "yes" if key in source else "no"
    return f"{key}: {prop}={answer}; {PROPERTY_FACTS[prop]}"


def list_http_methods() -> str:
    """Return identifiers of all HTTP methods known to the environment."""
    return ", ".join(sorted(HTTP_METHODS))
