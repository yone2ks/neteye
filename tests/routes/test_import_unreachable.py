from unittest.mock import patch

from flask import url_for


def test_import_from_ip_unreachable_redirects_instead_of_500(app, auth_client):
    with patch("neteye.node.routes.try_connect_node", return_value=False):
        resp = auth_client.post("/node/import_node_from_ip/192.0.2.1")
    assert resp.status_code == 302
    with app.test_request_context():
        expected = url_for("node.index")
    assert resp.headers["Location"].endswith(expected)
