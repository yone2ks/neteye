from neteye.extensions import db
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from datetime import datetime


class Base(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return "<id={id} created_at={created_at} updated_at={updated_at}".format(
            id=self.id, created_at=self.created_at, updated_at=self.updated_at
        )
