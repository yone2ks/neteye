import logging
import re
from urllib.parse import parse_qs


class DataTablesLogFilter(logging.Filter):
    """Collapse DataTables server-side query strings in werkzeug access logs.

    DataTables sends verbose column configuration on every request. This filter
    replaces those query strings with a compact human-readable summary:

        Before:
            "GET /node/data?draw=1&columns[0][data]=0&columns[0][name]=
             &columns[0][searchable]=true&...&order[0][column]=1
             &order[0][dir]=asc&start=0&length=100&search[value]=
             &search[regex]=false HTTP/1.1" 200 -

        After (no search):
            "GET /node/data [start=0 length=100 sort=col1:asc] HTTP/1.1" 200 -

        After (global search):
            "GET /node/data [start=0 length=100 sort=col1:asc search=cisco] HTTP/1.1" 200 -

        After (per-column search):
            "GET /node/data [start=0 length=100 sort=col1:asc col3=192.168] HTTP/1.1" 200 -

    Non-DataTables URLs (no 'draw' parameter) are left unchanged.
    """

    _URL_RE = re.compile(
        r'("(?:GET|POST|PUT|DELETE|PATCH) )(/[^?"\s]+)\?([^"\s]+)( HTTP/[\d.]+")'
    )
    _COL_SEARCH_RE = re.compile(r"columns\[(\d+)\]\[search\]\[value\]")

    def filter(self, record: logging.LogRecord) -> bool:
        # getMessage() merges record.msg and record.args into the final string.
        # str(record.msg) alone would return the unformatted template (e.g. '"%s %s %s" %s -').
        raw_msg = record.getMessage()
        url_match = self._URL_RE.search(raw_msg)
        if not url_match:
            return True

        query_string = url_match.group(3)
        params = parse_qs(query_string, keep_blank_values=True)

        # Only reformat DataTables requests (identified by the 'draw' parameter).
        if "draw" not in params:
            return True

        summary_parts = []

        # Pagination: start row and page length as separate keys (matching DataTables param names)
        start_row = params.get("start", ["0"])[0]
        rows_per_page = params.get("length", ["?"])[0]
        summary_parts.append(f"start={start_row}")
        summary_parts.append(f"length={rows_per_page}")

        # Sort: order[0][column] + order[0][dir] → sort=colN:direction
        sort_column = params.get("order[0][column]", [None])[0]
        sort_direction = params.get("order[0][dir]", ["?"])[0]
        if sort_column is not None:
            summary_parts.append(f"sort=col{sort_column}:{sort_direction}")

        # Global search (across all columns)
        global_search_term = params.get("search[value]", [""])[0]
        if global_search_term:
            summary_parts.append(f"search={global_search_term}")

        # Per-column search (only columns with a non-empty search value)
        for query_param_name, query_param_values in params.items():
            column_search_match = self._COL_SEARCH_RE.fullmatch(query_param_name)
            if column_search_match and query_param_values[0]:
                summary_parts.append(f"col{column_search_match.group(1)}={query_param_values[0]}")

        summary = "[" + " ".join(summary_parts) + "]"
        filtered_msg = (
            raw_msg[: url_match.start(1)]
            + url_match.group(1)
            + url_match.group(2)
            + " "
            + summary
            + url_match.group(4)
            + raw_msg[url_match.end(4):]
        )
        record.msg = filtered_msg
        record.args = ()
        return True
