from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship
from sqlalchemy_utils import UUIDType

from neteye.base.models import Base


class Serial(Base):
    __tablename__ = "serials"

    serial_number = Column(String)
    product_id = Column(String)
    node_id = Column(UUIDType(binary=False), ForeignKey("nodes.id"))

    def __repr__(self):
        return "serial_id={id} serial_number={serial_number} product_id={product_id} node_id={node_id}".format(
            id=self.id,
            serial_number=self.serial_number,
            product_id=self.product_id,
            node_id=self.node_id,
        )

    def exists(serial_number):
        return Serial.query.filter_by(serial_number=serial_number).scalar() != None
