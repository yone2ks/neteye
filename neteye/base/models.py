import uuid
from datetime import datetime

from flask_continuum import VersioningMixin
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy_utils import UUIDType

from neteye.extensions import db


class Base(db.Model, VersioningMixin):
    __abstract__ = True

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return "<id={id} created_at={created_at} updated_at={updated_at}".format(
            id=self.id, created_at=self.created_at, updated_at=self.updated_at
        )
