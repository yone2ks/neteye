from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base


class Cable(Base):
    __tablename__ = "cables"

    a_interface_id = Column(String, ForeignKey("interfaces.id"))
    a_interface = relationship("Interface", foreign_keys=[a_interface_id])
    b_interface_id = Column(String, ForeignKey("interfaces.id"))
    b_interface = relationship("Interface", foreign_keys=[b_interface_id])
    description = Column(String, default="")
    cable_type = Column(String)
    link_speed = Column(String)
