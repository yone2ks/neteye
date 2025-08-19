import logging
import traceback
from flask import flash
from markupsafe import Markup, escape

logger = logging.getLogger(__name__)

def report_exception(err: Exception, context: str, *, include_trace: bool = False, max_len: int = 2000, level: str = "danger") -> None:
    """
    Log full exception (with stack trace) and flash a detailed error message.

    Args:
        err: The caught exception instance.
        context: Short context message (what operation failed).
        include_trace: If True, append traceback text to the flash message (may be long).
        max_len: Max characters of the flash message to avoid UI overflow.
        level: Flash category (Bootstrap alert level), default 'danger'.
    """
    # Always log full stack trace for debugging
    logger.exception(f"{context}: {type(err).__name__}: {err}")

    # Build detailed message for flashing to the UI (admin audience)
    detail = f"{type(err).__name__}: {err}"
    if include_trace:
        tb = traceback.format_exc()
        detail = f"{detail}\n{tb}"

    # Build raw message text
    raw_msg = f"{context}: {detail}"

    # Trim very long messages to keep the UI stable
    if len(raw_msg) > max_len:
        raw_msg = raw_msg[: max_len - 3] + "..."

    # Normalize newlines and escape to prevent XSS, then convert to <br /> and mark safe.
    normalized = raw_msg.replace("\r\n", "\n")
    escaped = escape(normalized)
    html_msg = Markup(str(escaped).replace("\n", "<br />"))

    flash(html_msg, level)
