import logging
import re


class WerkzeugAccessLogFilter(logging.Filter):
    """Clean up werkzeug access log messages.

    Applies two transformations:

    1. Remove redundant werkzeug timestamp.
       werkzeug embeds its own timestamp in every access log line:

           127.0.0.1 - - [10/May/2026 19:29:22] "GET /node/ HTTP/1.1" 200 -

       When logging.basicConfig (or any handler) already prepends a timestamp,
       this results in the time appearing twice on every line.  This filter
       removes the redundant werkzeug timestamp so the output becomes:

           127.0.0.1 - - "GET /node/ HTTP/1.1" 200 -

    2. Suppress 304 Not Modified responses.
       304 responses indicate browser cache hits on static files (CSS, JS,
       images). They carry no diagnostic value in normal operation and add
       noise that buries meaningful application requests.

    Why not suppress werkzeug logs entirely?
    Access logs are useful for debugging request flow. The goal is to keep
    them readable, not to lose them.

    Why a Filter rather than a custom Formatter?
    werkzeug uses its own internal logger and does not expose a way to
    customise its format without monkey-patching. A logging.Filter applied
    to the 'werkzeug' logger is the least-invasive approach.
    """

    _WERKZEUG_TIMESTAMP_RE = re.compile(r" \[\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2}\]")
    _HTTP_304_RE = re.compile(r'" 304 ')

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()

        # Suppress 304 Not Modified — static file cache hits, no diagnostic value.
        if self._HTTP_304_RE.search(msg):
            return False

        # Remove the redundant werkzeug timestamp if present.
        msg_without_timestamp = self._WERKZEUG_TIMESTAMP_RE.sub("", msg)
        if msg_without_timestamp != msg:
            record.msg = msg_without_timestamp
            record.args = ()

        return True
