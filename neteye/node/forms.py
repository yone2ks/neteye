from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Required

class NodeForm(FlaskForm):
    hostname = StringField('Hostname:', validators=[Required()])
    description = StringField('Description:')
    ip_address = StringField('IP Address:', validators=[Required()])
    username = StringField('Username:', validators=[Required()])
    password = StringField('Password:', validators=[Required()])
    enable = StringField('Enable:', validators=[Required()])
    device_type = StringField('Device Type:')
    submit = SubmitField('Submit')
    reset = SubmitField('Reset')
