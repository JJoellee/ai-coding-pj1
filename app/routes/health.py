from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Report basic service liveness.

    Does not check any dependency (there is no database or external
    service to check) — a 200 here only means the process is up and
    handling requests.

    Returns:
        dict: ``{"status": "ok", "timestamp": <current UTC time, ISO 8601>}``.

    Example:
        ``GET /health`` → ``200``.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
