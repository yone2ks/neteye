from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
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
    src_ip_address = SelectField("Source IP Address:", choices=[])
    count = IntegerField("Count:")
    data_size = IntegerField("Data Size:")
    timeout = IntegerField("Timeout:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
