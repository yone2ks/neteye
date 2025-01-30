from flask_security import RoleMixin, UserMixin, SQLAlchemySessionUserDatastore, hash_password
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.extensions import db, settings

ADMIN_ROLE = 'admin'
USER_ROLE = 'user'

class RolesUsers(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column("user_id", Integer, ForeignKey("user.id"))
    role_id = Column("role_id", Integer, ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))
    
    def commit(self):
        db.session.commit()
    
    def add(self):
        db.session.add(self)
        self.commit()
    
    def delete(self):
        db.session.delete(self)
        self.commit()


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

    def commit(self):
        db.session.commit()
        
    def add(self):
        db.session.add(self)
        self.commit()
        
    def delete(self):
        db.session.delete(self)
        self.commit()


user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
admin_role = Role(name=ADMIN_ROLE, description='Administrator role')
user_role = Role(name=USER_ROLE, description='User role')

def initialize_roles():
    if not user_datastore.find_role(ADMIN_ROLE):
        admin_role.add() 
    if not user_datastore.find_role(USER_ROLE):
        user_role.add()


def initialize_admin():
    # If the admin user does not exist, create it
    admin_user = User.query.filter_by(email=settings.ADMIN_EMAIL).first()
    if not admin_user:
        admin_user = user_datastore.create_user(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            password=hash_password(settings.ADMIN_PASSWORD),
            active=True,
            roles=[admin_role]
        )
        admin_user.add()
