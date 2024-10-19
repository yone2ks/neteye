from flask_security import RoleMixin, UserMixin, SQLAlchemySessionUserDatastore
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.extensions import db


class RolesUsers(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column("user_id", Integer, ForeignKey("user.id"))
    role_id = Column("role_id", Integer, ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    fs_uniquifier = Column(String(255), unique=True, nullable=False)
    confirmed_at = Column(DateTime())
    roles = relationship(
        "Role", secondary="roles_users", backref=backref("users", lazy="dynamic")
    )

user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
