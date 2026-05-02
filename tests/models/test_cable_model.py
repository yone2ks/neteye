import pytest
from sqlalchemy.exc import IntegrityError
from neteye.cable.models import Cable
from neteye.interface.models import Interface
from neteye.node.models import Node


@pytest.fixture
def two_nodes(db):
    n1 = Node(hostname="node1", ip_address="10.0.0.1", port=22, device_type="cisco_ios", username="u", password="p")
    n2 = Node(hostname="node2", ip_address="10.0.0.2", port=22, device_type="cisco_ios", username="u", password="p")
    db.session.add_all([n1, n2])
    db.session.commit()
    yield n1, n2
    db.session.delete(n1)
    db.session.delete(n2)
    db.session.commit()


@pytest.fixture
def two_interfaces(db, two_nodes):
    n1, n2 = two_nodes
    i1 = Interface(node_id=n1.id, name="Gi0/0")
    i2 = Interface(node_id=n2.id, name="Gi0/0")
    db.session.add_all([i1, i2])
    db.session.commit()
    yield i1, i2
    db.session.delete(i1)
    db.session.delete(i2)
    db.session.commit()


class TestCableUniqueConstraint:
    def test_create_cable(self, db, two_interfaces):
        i1, i2 = two_interfaces
        sorted_ids = "-".join(sorted([i1.id, i2.id]))
        cable = Cable(
            a_interface_id=i1.id,
            b_interface_id=i2.id,
            sorted_interface_ids=sorted_ids,
        )
        db.session.add(cable)
        db.session.commit()
        assert Cable.get(cable.id) is not None
        db.session.delete(cable)
        db.session.commit()

    def test_duplicate_cable_raises_integrity_error(self, db, two_interfaces):
        i1, i2 = two_interfaces
        sorted_ids = "-".join(sorted([i1.id, i2.id]))
        c1 = Cable(a_interface_id=i1.id, b_interface_id=i2.id, sorted_interface_ids=sorted_ids)
        db.session.add(c1)
        db.session.commit()

        c2 = Cable(a_interface_id=i1.id, b_interface_id=i2.id, sorted_interface_ids=sorted_ids)
        db.session.add(c2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        db.session.delete(c1)
        db.session.commit()
