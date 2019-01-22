from neteye.base.models import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime

class Node(Base):
    __tablename__ = 'nodes'

    hostname = Column(String, unique=True, nullable=True)
    description = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    model = Column(String)
    os_type = Column(String)
    os_version = Column(String)
    serial = Column(String)
    username = Column(String)
    password = Column(String)
    enable = Column(String)

    def __repr__(self):
        return "<Node id={id} hostname={hostname} ip_address={ip_address}".format(id=self.id, hostname=self.hostname, ip_address=self.ip_address)
