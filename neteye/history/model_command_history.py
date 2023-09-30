from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship


class CommandHistory(Base):
    __tablename__ = "command_histories"

    username = Column(String, nullable=False)
    node_id = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    command = Column(String, nullable=False)
    result = Column(Text)

    def __init__(self, **kwargs):
        super(CommandHistory, self).__init__(**kwargs)

    def __repr__(self):
        return "<CommandHistory id={id} date={date} username={username} node_id={node_id} hostname={hostname} command={command}".format(
            id=self.id, date=self.created_at, username=self.username, node_id=self.node_id, hostname=self.hostname, command=self.command
        )
