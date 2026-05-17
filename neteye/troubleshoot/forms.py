from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from wtforms_sqlalchemy.fields import QuerySelectField

from neteye.extensions import settings
from neteye.node.models import Node


def get_nodes():
    return Node.query.all()


# Ping form defaults
PING_DEFAULT_COUNT     = 5
PING_DEFAULT_DATA_SIZE = 100
PING_DEFAULT_TIMEOUT   = 2


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
        default=PING_DEFAULT_COUNT,
    )
    data_size = IntegerField(
        "Data Size:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.PING_MAX_DATA_SIZE)],
        default=PING_DEFAULT_DATA_SIZE,
    )
    timeout = IntegerField(
        "Timeout:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.PING_MAX_TIMEOUT)],
        default=PING_DEFAULT_TIMEOUT,
    )
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")


# Traceroute form defaults
TRACEROUTE_MAX_PROBE       = 10
TRACEROUTE_DEFAULT_MAX_TTL = 30
TRACEROUTE_DEFAULT_PROBE   = 3
TRACEROUTE_DEFAULT_TIMEOUT = 3


class TracerouteForm(FlaskForm):
    dst_ip_address = StringField("Destination IP Address:", validators=[DataRequired()])
    src_node = QuerySelectField(
        "Source Node:",
        validators=[DataRequired()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    src_ip_address = SelectField("Source IP Address:", choices=[], validators=[Optional()])
    vrf = StringField("VRF:", validators=[Optional()])
    max_ttl = IntegerField(
        "Max TTL:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.TRACEROUTE_MAX_TTL)],
        default=TRACEROUTE_DEFAULT_MAX_TTL,
    )
    probe = IntegerField(
        "Probe:",
        validators=[DataRequired(), NumberRange(min=1, max=TRACEROUTE_MAX_PROBE)],
        default=TRACEROUTE_DEFAULT_PROBE,
    )
    timeout = IntegerField(
        "Timeout:",
        validators=[DataRequired(), NumberRange(min=1, max=settings.TRACEROUTE_MAX_TIMEOUT)],
        default=TRACEROUTE_DEFAULT_TIMEOUT,
    )
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
