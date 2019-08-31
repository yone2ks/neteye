from neteye.base.models import Base
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint

class Interface(Base):
    __tablename__ = 'interfaces'
    __table_args__ = (
        UniqueConstraint('node_id', 'name', name='unique_interface'),
    )

    node_id = Column(Integer, ForeignKey('nodes.id'))
    name = Column(String)
    description = Column(String)
    ip_address = Column(String)
    mask = Column(String)
    speed = Column(String)
    duplex = Column(String)
    status = Column(String)

    def __repr__(self):
        return "<Interface id={id} node_id={node_id} name={name}".format(id=self.id, node_id=self.node_id, name=self.name)

    def exists(node_id, name):
        return Interface.query.filter_by(node_id=node_id).filter_by(name=IntfAbbrevConverter('cisco_ios').to_long(name)).scalar() != None

