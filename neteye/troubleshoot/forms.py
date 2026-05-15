from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from wtforms_sqlalchemy.fields import QuerySelectField

from neteye.extensions import settings
from neteye.node.models import Node


def get_nodes():
    return Node.query.all()


class PingForm(FlaskForm):
    dst_ip_address = StringField("Destination IP Address:", validators=[DataRequired()])
    src_node = QuerySelectField(
        "Source Node:",
        validators=[DataRequired()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    src_ip_address = SelectField("Source IP Address:", choices=[], validators=[Optional()])
    vrf = StringField("VRF:", validators=[Optional()])
    count = IntegerField(
        "Count:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.PING_MAX_COUNT)],
        default=5,
    )
    data_size = IntegerField(
        "Data Size:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.PING_MAX_DATA_SIZE)],
        default=100,
    )
    timeout = IntegerField(
        "Timeout:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.PING_MAX_TIMEOUT)],
        default=2,
    )
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
