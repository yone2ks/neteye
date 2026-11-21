from markupsafe import Markup, escape

LINE_SEPARATOR = Markup("\n")


def format_raw_output(text: str) -> Markup:
    """Convert raw device output into HTML that is safe to render.

    Device output can contain attacker-controlled text (e.g. an interface
    description such as "<script>..."), so each line is HTML-escaped before
    lines are rejoined with plain newlines. Render the result inside <pre> so
    the device's indentation (e.g. nested config blocks) is preserved.
    """
    return LINE_SEPARATOR.join(escape(line) for line in text.splitlines())
