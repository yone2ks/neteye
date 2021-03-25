from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import backref, relationship
from sqlalchemy_utils import UUIDType

from neteye.base.models import Base
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter


class Interface(Base):
    __tablename__ = "interfaces"
    __table_args__ = (UniqueConstraint("node_id", "name", name="unique_interface"),)

    node_id = Column(UUIDType(binary=False), ForeignKey("nodes.id"))
    node = relationship("Node", back_populates="interfaces")
    name = Column(String)
    description = Column(String)
    ip_address = Column(String)
    mask = Column(String)
    speed = Column(String)
    duplex = Column(String)
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
