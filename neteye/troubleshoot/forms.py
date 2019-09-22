from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Required
from neteye.node.models import Node

def get_nodes():
    return Node.query.all()

class PingForm(FlaskForm):
    dst_ip_address = QuerySelectField('Node:', validators=[Required()], query_factory=get_nodes, get_label='hostname')
    src_node = QuerySelectField('Node:', validators=[Required()], query_factory=get_nodes, get_label='hostname')
    # src_ip_address =
    # count =
    # date_size =
    # timeout = 
