from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, InputRequired

from neteye.node.models import Node


def get_nodes():
    return Node.query.all()

class SerialForm(FlaskForm):
    node_id = QuerySelectField(
        "Node:", validators=[InputRequired()], query_factory=get_nodes, get_label="hostname"
    )
    serial_number = StringField("Serial Number:", validators=[InputRequired()])
    product_id = StringField("Product ID:", validators=[InputRequired()])
    description = StringField("Description:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
