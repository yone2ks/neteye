from markupsafe import Markup

from neteye.lib.utils.format_raw_output import format_raw_output


class TestFormatRawOutput:
    def test_normalizes_line_endings_to_newline(self):
        assert format_raw_output("a\r\nb\nc") == Markup("a\nb\nc")

    def test_preserves_leading_indentation(self):
        text = "interface Ethernet1\n  description uplink\n    ip address 10.0.0.1/24"
        assert format_raw_output(text) == Markup(text)

    def test_escapes_html(self):
        result = format_raw_output('description <script>alert("x")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_returns_markup_so_template_does_not_double_escape(self):
        assert isinstance(format_raw_output("a\nb"), Markup)

    def test_empty_string(self):
        assert format_raw_output("") == Markup("")
