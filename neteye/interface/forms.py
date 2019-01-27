from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Required

class InterfaceForm(FlaskForm):
    node_id = StringField('node_id:', validators=[Required()])
    name = StringField('name:', validators=[Required()])
    description = StringField('description:')
    ip_address = StringField('ip address:')
    mask = StringField('mask:')
    speed = StringField('speed:')
    duplex = StringField('duplex:')
    status = StringField('status:')

