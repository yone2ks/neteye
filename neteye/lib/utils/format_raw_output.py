from markupsafe import Markup, escape

LINE_BREAK = Markup("<br />")


def format_raw_output(text: str) -> Markup:
    """Convert raw device output into HTML that is safe to render.

    Device output can contain attacker-controlled text (e.g. an interface
    description such as "<script>..."), so each line is HTML-escaped before
    newlines are turned into <br /> tags.
    """
    return LINE_BREAK.join(escape(line) for line in text.splitlines())
