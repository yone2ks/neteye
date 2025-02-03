from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint, Index, case)
from sqlalchemy.orm import relationship

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
    sorted_interface_ids = Column(String, unique=True)

    # Ensure unique pairs of a_interface_id and b_interface_id, regardless of order
    __table_args__ = (
            UniqueConstraint('sorted_interface_ids', name='unique_interface_pair'),
        )
