from neteye.base.models import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint

class Cable(Base):
    __tablename__ = 'cables'

    src_interface_id = Column(Integer, ForeignKey('interfaces.id'))
    dst_interface_id = Column(Integer, ForeignKey('interfaces.id'))
    description = Column(String)
    cable_type = Column(String)
    link_speed = Column(String)



