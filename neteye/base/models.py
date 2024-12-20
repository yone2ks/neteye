import uuid
from datetime import datetime, timezone

from flask_continuum import VersioningMixin
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from neteye.extensions import db


def gen_uuid_str():
    return str(uuid.uuid4())


class Base(db.Model, VersioningMixin):
    __abstract__ = True

    id = Column(String, primary_key=True, default=gen_uuid_str)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at.isoformat()}, updated_at={self.updated_at.isoformat()})>"

    def commit(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise

    def add(self):
        try:
            db.session.add(self)
            self.commit()
        except Exception as e:
            db.session.rollback()
            raise

    def delete(self):
        db.session.delete(self)
        self.commit()

    def rollback(self):
        try:
            db.session.rollback()
        except Exception as e:
            raise
