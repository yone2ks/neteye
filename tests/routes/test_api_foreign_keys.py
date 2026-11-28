import pytest
from neteye.extensions import db as _db
from neteye.interface.models import Interface
from neteye.node.models import Node


@pytest.fixture
def two_interfaces(app):
    with app.app_context():
        nodes = []
        for i in (1, 2):
            n = Node(hostname=f"fk-test-{i}", ip_address=f"192.168.98.{i}", port=22,
                     device_type="cisco_ios", username="admin", password="pass")
            _db.session.add(n)
            nodes.append(n)
        _db.session.commit()
        ifs = []
        for n in nodes:
            i = Interface(node_id=n.id, name="Ethernet1/1")
            _db.session.add(i)
            ifs.append(i)
        _db.session.commit()
        ids = [i.id for i in ifs], [n.id for n in nodes]
    yield ids
    with app.app_context():
        for nid in ids[1]:
            n = _db.session.get(Node, nid)
            if n:
                _db.session.delete(n)
        _db.session.commit()


def test_create_interface_via_api(auth_client, two_interfaces):
    _, node_ids = two_interfaces
    resp = auth_client.post("/api/interfaces/", json={"node_id": node_ids[0], "name": "Ethernet1/9"})
    assert resp.status_code == 201
    assert resp.get_json()["node_id"] == node_ids[0]


def test_create_cable_via_api_and_reject_duplicate(auth_client, two_interfaces):
    if_ids, _ = two_interfaces
    body = {"a_interface_id": if_ids[0], "b_interface_id": if_ids[1], "cable_type": "cat6"}
    resp = auth_client.post("/api/cables/", json=body)
    assert resp.status_code == 201
    assert resp.get_json()["a_interface_id"] == if_ids[0]
    cable_id = resp.get_json()["id"]
    # same pair in reverse order must not create a second cable
    dup = auth_client.post("/api/cables/", json={**body, "a_interface_id": if_ids[1], "b_interface_id": if_ids[0]})
    assert dup.status_code == 409
    auth_client.delete(f"/api/cables/{cable_id}")


def test_invalid_payload_returns_400_not_500(auth_client):
    resp = auth_client.post("/api/cables/", json={"bogus_field": "x"})
    assert resp.status_code == 400


@pytest.mark.parametrize(
    "ends",
    [
        {},
        {"a_interface_id": "missing-id"},
        {"b_interface_id": "missing-id"},
        {"b_interface_id": "same"},
    ],
    ids=["no-ends", "unknown-a", "unknown-b", "same-interface"],
)
def test_create_cable_via_api_rejects_invalid_ends(auth_client, two_interfaces, ends):
    if_ids, _ = two_interfaces
    body = {"a_interface_id": if_ids[0], "b_interface_id": if_ids[1], "cable_type": "cat6"}
    if ends == {}:
        body = {"cable_type": "cat6"}
    else:
        body.update({key: (if_ids[0] if value == "same" else value) for key, value in ends.items()})

    resp = auth_client.post("/api/cables/", json=body)

    assert resp.status_code == 400
    assert auth_client.get("/api/cables/").get_json() == []


def test_update_cable_via_api_validates_the_resulting_ends(auth_client, two_interfaces):
    if_ids, _ = two_interfaces
    created = auth_client.post("/api/cables/", json={"a_interface_id": if_ids[0], "b_interface_id": if_ids[1]})
    cable_id = created.get_json()["id"]

    # Only the B end is sent; with the current A end it would connect the interface to itself.
    looped = auth_client.put(f"/api/cables/{cable_id}", json={"b_interface_id": if_ids[0]})
    renamed = auth_client.put(f"/api/cables/{cable_id}", json={"description": "uplink"})

    assert looped.status_code == 400
    assert "to itself" in looped.get_json()["message"]
    assert renamed.status_code == 200
    # PUT does not validate types up front, so these reach the endpoint check.
    for bad_end in (None, {"x": 1}, ["a", "b"], [if_ids[1]]):
        response = auth_client.put(f"/api/cables/{cable_id}", json={"b_interface_id": bad_end})
        assert response.status_code == 400, bad_end
    stored = auth_client.get(f"/api/cables/{cable_id}").get_json()
    assert (stored["b_interface_id"], stored["description"]) == (if_ids[1], "uplink")
    auth_client.delete(f"/api/cables/{cable_id}")
