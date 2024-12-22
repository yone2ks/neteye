from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, InputRequired
from neteye.extensions import db
from neteye.node.models import Node
from neteye.interface.models import Interface


def get_nodes():
    return Node.query.all()


class CableForm(FlaskForm):
    a_node = QuerySelectField(
        "Node-A:",
        validators=[InputRequired()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    b_node = QuerySelectField(
        "Node-B:",
        validators=[InputRequired()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    a_interface = SelectField(validators=[InputRequired()], choices=[])
    b_interface = SelectField(validators=[InputRequired()], choices=[])
    description = StringField("description:")
    cable_type = SelectField(
        choices=[("twisted_pair", "Twisted-Pair"), ("optical_fiber", "Optical-Fiber")]
    )
    link_speed = SelectField(
        choices=[
            ("1g", "1Gbps"),
            ("10g", "10Gbps"),
            ("25g", "25Gbps"),
            ("40g", "40Gbps"),
            ("100g", "100Gbps"),
        ]
    )
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
