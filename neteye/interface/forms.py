from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Required

from neteye.node.models import Node


def get_nodes():
    return Node.query.all()


class InterfaceForm(FlaskForm):
    node_id = QuerySelectField(
        "Node:", validators=[Required()], query_factory=get_nodes, get_label="hostname"
    )
    name = StringField("Name:", validators=[Required()])
    description = StringField("Description:")
    ip_address = StringField("IP Address:")
    mask = StringField("Mask:")
    speed = StringField("Speed:")
    duplex = StringField("Duplex:")
    status = StringField("Status:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
