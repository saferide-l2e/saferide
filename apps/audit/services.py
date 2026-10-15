"""Audit recording service (BE-12, DB-07)."""

from .models import AuditEvent

# Sensitive keys that must never appear raw in audit metadata
_REDACTED_KEYS = {
    "password",
    "raw_code",
    "code",
    "token",
    "secret",
    "licence",
    "license",
    "licence_number",
    "license_number",
    "id_scan",
    "complaint_narrative",
    "narrative",
    "phone",
    "address",
}


def _redact(metadata):
    if not metadata:
        return {}
    clean = {}
    for key, value in metadata.items():
        if key.lower() in _REDACTED_KEYS:
            clean[key] = "[REDACTED]"
        else:
            clean[key] = value
    return clean


def record(actor, action, obj=None, metadata=None):
    """Write an audit event. Safe to call inside a transaction with the change."""
    object_type = ""
    object_id = ""
    if obj is not None:
        object_type = obj._meta.label if hasattr(obj, "_meta") else type(obj).__name__
        object_id = str(getattr(obj, "pk", ""))
    if actor is not None and not getattr(actor, "is_authenticated", True):
        actor = None
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=_redact(metadata),
    )


def record_audit_event(actor, action, object_type, object_id, raw_metadata=None):
    """Utility helper matching DB-07 requirements."""
    if actor is not None and not getattr(actor, "is_authenticated", True):
        actor = None
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        metadata=_redact(raw_metadata),
    )
