from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)

from neteye.base.models import Base


class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    target_table = Column(String, nullable=False)
    target_item = Column(String, nullable=False)
    action = Column(String, nullable=False)
