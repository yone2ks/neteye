from neteye.base.models import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, ForeignKey

class Interface(Base):
    __tablename__ = 'interfaces'

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


