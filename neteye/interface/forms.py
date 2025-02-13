from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, InputRequired, IPAddress

from neteye.node.models import Node


def get_nodes():
    return Node.query.all()


class InterfaceForm(FlaskForm):
    node_id = QuerySelectField(
        "Node:", validators=[InputRequired()], query_factory=get_nodes, get_label="hostname"
    )
    name = StringField("Name:", validators=[InputRequired()])
    description = StringField("Description:")
    ip_address = StringField("IP Address:", validators=[IPAddress()])
    mask = StringField("Mask:", validators=[IPAddress()])
    mac_address = StringField("MAC Address:")
    speed = StringField("Speed:")
    duplex = StringField("Duplex:")
    mtu = StringField("MTU:")
    status = StringField("Status:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
