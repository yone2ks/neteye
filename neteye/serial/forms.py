from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Required

from neteye.node.models import Node


def get_nodes():
    return Node.query.all()

class SerialForm(FlaskForm):
    node_id = QuerySelectField(
        "Node:", validators=[Required()], query_factory=get_nodes, get_label="hostname"
    )
    serial_number = StringField("Serial Number:", validators=[Required()])
    product_id = StringField("Product ID:", validators=[Required()])
    description = StringField("Description:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
