import sqlite3

from neteye.extensions import settings
from neteye.node.models import Node
from neteye.history.models import node_version


class TestNodeCredentialEncryption:
    def test_password_round_trips_through_orm(self, db):
        node = Node(
            hostname="enc-test-router",
            ip_address="192.168.50.1",
            port=22,
            device_type="cisco_ios",
            username="secretuser",
            password="supersecretpw",
        )
        db.session.add(node)
        db.session.commit()
        node_id = node.id

        db.session.expire_all()
        reloaded = Node.get(node_id)
        assert reloaded.password == "supersecretpw"

        db.session.delete(reloaded)
        db.session.commit()

    def test_password_not_stored_in_plaintext_in_sqlite_file(self, db):
        node = Node(
            hostname="enc-test-router-2",
            ip_address="192.168.50.2",
            port=22,
            device_type="cisco_ios",
            username="plaintextcheckuser",
            password="findme-plaintext-marker",
        )
        db.session.add(node)
        db.session.commit()
        db.session.expire_all()

        db_path = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
        raw_conn = sqlite3.connect(db_path)
        try:
            cursor = raw_conn.execute(
                "SELECT password FROM nodes WHERE hostname = ?", ("enc-test-router-2",)
            )
            raw_value = cursor.fetchone()[0]
        finally:
            raw_conn.close()

        assert "findme-plaintext-marker" not in raw_value
        assert raw_value != "findme-plaintext-marker"

        node = Node.query.filter_by(hostname="enc-test-router-2").first()
        db.session.delete(node)
        db.session.commit()

    def test_node_version_history_stores_and_returns_decrypted_password(self, db):
        node = Node(
            hostname="enc-test-router-3",
            ip_address="192.168.50.3",
            port=22,
            device_type="cisco_ios",
            username="histuser",
            password="histpassword1",
        )
        db.session.add(node)
        db.session.commit()

        node.password = "histpassword2"
        db.session.commit()

        versions = (
            db.session.query(node_version)
            .filter(node_version.id == node.id)
            .order_by(node_version.transaction_id.asc())
            .all()
        )
        assert len(versions) >= 2
        passwords = [v.password for v in versions]
        assert "histpassword1" in passwords
        assert "histpassword2" in passwords

        db.session.delete(node)
        db.session.commit()
