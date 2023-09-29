from sqlalchemy_continuum import transaction_class, version_class
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship


from neteye.base.models import Base
from neteye.arp_entry.models import ArpEntry
from neteye.cable.models import Cable
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.serial.models import Serial

node_version = version_class(Node)
node_transaction = transaction_class(Node)
interface_version = version_class(Interface)
interface_transaction = transaction_class(Interface)
serial_version = version_class(Serial)
serial_transaction = transaction_class(Serial)
cable_version = version_class(Cable)
cable_transaction = transaction_class(Cable)
arp_entry_version = version_class(ArpEntry)
arp_entry_transaction = transaction_class(ArpEntry)

OPERATION_TYPE = {0: "INSERT", 1: "UPDATE", 2: "DELETE"}


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
