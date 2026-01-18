import json
import time


def _agent_debug_log(*, hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    payload = {
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": time.time(),
    }
    try:
        with open("/home/bcorfman/dev/arcade_actions/.cursor/debug.log", "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def _debug_log(message: str, *, action: str = "CallbackUntil", level: int = 3) -> None:
    """Log debug message using centralized config with level and filters."""
    from arcadeactions.base import Action as _ActionBase

    if _ActionBase.debug_level >= level and (
        _ActionBase.debug_all or (_ActionBase.debug_include_classes and action in _ActionBase.debug_include_classes)
    ):
        print(f"[AA L{level} {action}] {message}")
