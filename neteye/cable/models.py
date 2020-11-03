from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy_utils import UUIDType

from neteye.base.models import Base


class Cable(Base):
    __tablename__ = "cables"

    src_interface_id = Column(UUIDType(binary=False), ForeignKey("interfaces.id"))
    dst_interface_id = Column(UUIDType(binary=False), ForeignKey("interfaces.id"))
    description = Column(String)
    cable_type = Column(String)
    link_speed = Column(String)
