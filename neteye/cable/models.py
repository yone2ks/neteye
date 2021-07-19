from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base


class Cable(Base):
    __tablename__ = "cables"

    src_interface_id = Column(String, ForeignKey("interfaces.id"))
    src_interface = relationship("Interface", foreign_keys=[src_interface_id])
    dst_interface_id = Column(String, ForeignKey("interfaces.id"))
    dst_interface = relationship("Interface", foreign_keys=[dst_interface_id])
    description = Column(String, default="")
    cable_type = Column(String)
    link_speed = Column(String)
