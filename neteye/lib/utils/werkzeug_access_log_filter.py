import logging
import re


class WerkzeugAccessLogFilter(logging.Filter):
    """Strip werkzeug's built-in timestamp from access log messages.

    werkzeug embeds its own timestamp in every access log line:

        127.0.0.1 - - [10/May/2026 19:29:22] "GET /node/ HTTP/1.1" 200 -

    When logging.basicConfig (or any handler) already prepends a timestamp,
    this results in the time appearing twice on every line.  This filter
    removes the redundant werkzeug timestamp so the output becomes:

        127.0.0.1 - - "GET /node/ HTTP/1.1" 200 -

    Why not suppress werkzeug logs entirely?
    Access logs are useful for debugging request flow. The goal is to keep
    them readable, not to lose them.

    Why a Filter rather than a custom Formatter?
    werkzeug uses its own internal logger and does not expose a way to
    customise its format without monkey-patching. A logging.Filter applied
    to the 'werkzeug' logger is the least-invasive approach.
    """

    _TIMESTAMP_RE = re.compile(r" \[\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2}\]")

    def filter(self, record: logging.LogRecord) -> bool:
        raw_msg = record.getMessage()
        stripped = self._TIMESTAMP_RE.sub("", raw_msg)
        if stripped != raw_msg:
            record.msg = stripped
            record.args = ()
        return True
