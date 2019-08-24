from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Required

class NodeForm(FlaskForm):
    hostname = StringField('hostname:', validators=[Required()])
    description = StringField('description:')
    ip_address = StringField('ip address:', validators=[Required()])
    username = StringField('username:', validators=[Required()])
    password = StringField('password:', validators=[Required()])
    enable = StringField('enable:', validators=[Required()])
    device_type = StringField('enable:')
    submit = SubmitField('Add Node')
    reset = SubmitField('Reset')
