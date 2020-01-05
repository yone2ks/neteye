from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Required
from neteye.node.models import Node


def get_nodes():
    return Node.query.all()


class PingForm(FlaskForm):
    dst_ip_address = StringField("Destination IP Address:", validators=[Required()])
    src_node = QuerySelectField(
        "Source Node:",
        validators=[Required()],
        query_factory=get_nodes,
        get_label="hostname",
    )
    src_ip_address = SelectField("Source IP Address:", choices=[])
    count = IntegerField("Count:")
    data_size = IntegerField("Data Size:")
    timeout = IntegerField("Timeout:")
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
