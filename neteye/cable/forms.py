from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Required
from neteye.extensions import db
from neteye.node.models import Node
from neteye.interface.models import Interface


def get_nodes():
    return Node.query.all()


class CableForm(FlaskForm):
    src_node = QuerySelectField(
        "Src Node:",
        validators=[Required()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    dst_node = QuerySelectField(
        "Dst Node:",
        validators=[Required()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    src_interface = SelectField(choices=[])
    dst_interface = SelectField(choices=[])
    description = StringField("description:")
    cable_type = SelectField(
        choices=[("twisted_pair", "Twisted-Pair"), ("optical_fiber", "Optical-Fiber")]
    )
    link_speed = SelectField(
        choices=[
            ("1g", "1Gbps"),
            ("10g", "10Gbps"),
            ("40g", "40Gbps"),
            ("100g", "100Gbps"),
        ]
    )
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
