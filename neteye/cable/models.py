from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint, Index, case)
from sqlalchemy.orm import relationship

from neteye.base.models import Base
from neteye.extensions import db
from neteye.interface.models import Interface


class CableEndpointError(ValueError):
    """Raised when the ends of a cable are missing, not registered or the same interface."""


class Cable(Base):
    __tablename__ = "cables"

    ATTRIBUTES = {"a_interface_id", "b_interface_id", "description", "cable_type", "link_speed"}
    KEY = "sorted_interface_ids"

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

    @staticmethod
    def validate_endpoints(a_interface_id, b_interface_id):
        """
        Check that both ends of a cable are registered interfaces and are not the same interface.

        Raises:
            CableEndpointError: If an end is empty or not registered, or both ends are the same.
        """
        for side, interface_id in (("A", a_interface_id), ("B", b_interface_id)):
            if not interface_id:
                raise CableEndpointError(f"Select the {side}-side interface.")
            if not isinstance(interface_id, str):
                # session.get would read a list or dict as a composite key instead of rejecting it.
                raise CableEndpointError(f"The {side}-side interface id must be a string.")
            if db.session.get(Interface, interface_id) is None:
                raise CableEndpointError(f"The {side}-side interface {interface_id!r} is not registered.")
        if a_interface_id == b_interface_id:
            raise CableEndpointError("A cable cannot connect an interface to itself.")

    @staticmethod
    def make_sorted_interface_ids(a_interface_id, b_interface_id):
        """Return the key that makes an A/B pair unique regardless of order."""
        return "-".join(sorted([a_interface_id, b_interface_id]))

    def to_dict(self):
        return {
            "id": self.id,
            "a_interface_id": self.a_interface_id,
            "b_interface_id": self.b_interface_id,
            "description": self.description,
            "cable_type": self.cable_type,
            "link_speed": self.link_speed,
            "sorted_interface_ids": self.sorted_interface_ids,
        }