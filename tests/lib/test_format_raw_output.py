from markupsafe import Markup

from neteye.lib.utils.format_raw_output import format_raw_output


class TestFormatRawOutput:
    def test_converts_newlines_to_br(self):
        assert format_raw_output("a\r\nb\nc") == Markup("a<br />b<br />c")

    def test_escapes_html(self):
        result = format_raw_output('description <script>alert("x")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_returns_markup_so_template_does_not_double_escape(self):
        assert isinstance(format_raw_output("a\nb"), Markup)

    def test_empty_string(self):
        assert format_raw_output("") == Markup("")
