import pytest

from neteye.cable.models import Cable
from neteye.extensions import db as _db
from neteye.interface.models import Interface
from neteye.node.models import Node


@pytest.fixture
def orphan_cable(app):
    """A cable whose B-end interface was deleted (as an import deletes a renamed interface)."""
    with app.app_context():
        nodes = [
            Node(hostname=f"cable-missing-{i}", ip_address=f"192.168.95.{i}", port=22,
                 device_type="cisco_ios", username="admin", password="pass")
            for i in (1, 2)
        ]
        _db.session.add_all(nodes)
        _db.session.commit()
        a_interface = Interface(node_id=nodes[0].id, name="GigabitEthernet0/1")
        b_interface = Interface(node_id=nodes[1].id, name="GigabitEthernet0/2")
        _db.session.add_all([a_interface, b_interface])
        _db.session.commit()
        cable = Cable(
            a_interface_id=a_interface.id,
            b_interface_id=b_interface.id,
            sorted_interface_ids="-".join(sorted([a_interface.id, b_interface.id])),
        )
        _db.session.add(cable)
        _db.session.commit()
        _db.session.delete(b_interface)
        _db.session.commit()
        ids = {"cable": cable.id, "a_interface": a_interface.id, "nodes": [n.id for n in nodes]}
    yield ids
    with app.app_context():
        for model, object_ids in ((Cable, [ids["cable"]]), (Interface, [ids["a_interface"]]), (Node, ids["nodes"])):
            for object_id in object_ids:
                row = _db.session.get(model, object_id)
                if row:
                    _db.session.delete(row)
        _db.session.commit()


def test_cable_list_shows_a_cable_whose_interface_was_deleted(auth_client, orphan_cable):
    response = auth_client.get("/cable/data?draw=1&start=0&length=100")

    rows = {row["0"]: row for row in response.get_json()["data"]}
    row = rows[orphan_cable["cable"]]
    assert row["1"] == "cable-missing-1"
    assert row["2"] == "GigabitEthernet0/1"
    assert row["3"] is None
    assert row["4"] is None


def test_cable_edit_page_opens_when_an_interface_was_deleted(auth_client, orphan_cable):
    response = auth_client.get(f"/cable/{orphan_cable['cable']}/edit", follow_redirects=True)

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "no longer exists" in page
    assert f'var aNodeId = "{orphan_cable["nodes"][0]}"' in page
    assert 'var bNodeId = ""' in page


def test_cable_update_requires_existing_interfaces(app, auth_client, orphan_cable):
    response = auth_client.post(
        f"/cable/{orphan_cable['cable']}/update",
        data={"a_interface": orphan_cable["a_interface"], "b_interface": "", "cable_type": "", "link_speed": "", "description": ""},
        follow_redirects=True,
    )

    assert "Select the B-side interface" in response.get_data(as_text=True)
    with app.app_context():
        assert _db.session.get(Cable, orphan_cable["cable"]).b_interface_id != ""


@pytest.mark.parametrize(
    "b_interface,message",
    [("", "Select the B-side interface"), ("missing-id", "is not registered"), ("same", "to itself")],
    ids=["empty", "unknown", "same-interface"],
)
def test_cable_create_rejects_invalid_ends(app, auth_client, orphan_cable, b_interface, message):
    a_interface = orphan_cable["a_interface"]
    response = auth_client.post(
        "/cable/create",
        data={
            "a_interface": a_interface,
            "b_interface": a_interface if b_interface == "same" else b_interface,
            "cable_type": "", "link_speed": "", "description": "",
        },
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert message in page
    # The re-rendered form pre-selects the interface the user chose (the list is loaded by JS).
    assert f'selectedValue: "{a_interface}"' in page
    with app.app_context():
        touching = Cable.query.filter((Cable.a_interface_id == a_interface) | (Cable.b_interface_id == a_interface))
        assert touching.count() == 1  # only the fixture's cable


def test_cable_update_rejects_the_same_interface_on_both_ends(app, auth_client, orphan_cable):
    a_interface = orphan_cable["a_interface"]
    response = auth_client.post(
        f"/cable/{orphan_cable['cable']}/update",
        data={"a_interface": a_interface, "b_interface": a_interface, "cable_type": "", "link_speed": "", "description": ""},
        follow_redirects=True,
    )

    assert "to itself" in response.get_data(as_text=True)
    with app.app_context():
        assert _db.session.get(Cable, orphan_cable["cable"]).b_interface_id != a_interface
