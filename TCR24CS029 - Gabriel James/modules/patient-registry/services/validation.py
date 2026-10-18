"""Typed input validation shared by the capability services.

Every violation raises BadInput with a message naming the input, so the gateway and the UI show
the same reason the service rejected the call.
"""

from services.errors import BadInput


def require_string(payload, name):
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise BadInput('input "%s" must be a non empty string' % name)
    return value.strip()


def optional_string(payload, name, default=None):
    value = payload.get(name)
    if value is None:
        return default
    if not isinstance(value, str):
        raise BadInput('input "%s" must be a string' % name)
    return value.strip()


def require_enum(payload, name, allowed):
    value = require_string(payload, name)
    if value not in allowed:
        raise BadInput('input "%s" must be one of %s' % (name, ", ".join(sorted(allowed))))
    return value


def optional_enum(payload, name, allowed, default):
    value = payload.get(name)
    if value is None:
        return default
    if not isinstance(value, str) or value not in allowed:
        raise BadInput('input "%s" must be one of %s' % (name, ", ".join(sorted(allowed))))
    return value


def optional_int(payload, name, default=None):
    value = payload.get(name)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise BadInput('input "%s" must be an integer' % name)
    return value
