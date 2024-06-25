from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base


class Serial(Base):
    __tablename__ = "serials"

    serial_number = Column(String, nullable=False)
    product_id = Column(String)
    description = Column(String, default="")
    node_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    node = relationship("Node")

    def __repr__(self):
        return "serial_id={id} serial_number={serial_number} product_id={product_id} node_id={node_id}".format(
            id=self.id,
            serial_number=self.serial_number,
            product_id=self.product_id,
            node_id=self.node_id,
        )

    def exists(serial_number):
        return Serial.query.filter_by(serial_number=serial_number).scalar() != None
