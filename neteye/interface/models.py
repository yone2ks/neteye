from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter


class Interface(Base):
    __tablename__ = "interfaces"
    __table_args__ = (UniqueConstraint("node_id", "name", name="unique_interface"),)

    ATTRIBUTES = {"name", "description", "ip_address", "mask", "mac_address", "speed", "duplex", "mtu", "status", "node_id"}
    KEY = "name"

    node_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    node = relationship("Node")
    name = Column(String, nullable=False)
    description = Column(String, default="")
    ip_address = Column(String)
    mask = Column(String)
    mac_address = Column(String)
    speed = Column(String)
    duplex = Column(String)
    mtu = Column(String)
    status = Column(String)

    def __repr__(self):
        return "<Interface id={id} node_id={node_id} name={name}".format(
            id=self.id, node_id=self.node_id, name=self.name
        )

    def exists(node_id, name):
        return (
            Interface.query.filter_by(node_id=node_id)
            .filter_by(name=IntfAbbrevConverter("cisco_ios").normalization(name))
            .scalar()
            != None
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ip_address': self.ip_address,
            'mask': self.mask,
            'mac_address': self.mac_address,
            'speed': self.speed,
            'duplex': self.duplex,
            'mtu': self.mtu,
            'status': self.status,
            'node_id': self.node_id,
        }
