from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Required


class NodeForm(FlaskForm):
    hostname = StringField("Hostname:", validators=[Required()])
    description = StringField("Description:")
    ip_address = StringField("IP Address:", validators=[Required()])
    port = IntegerField("Port:", default=22)
    username = StringField("Username:", validators=[Required()])
    device_type = StringField("Device Type:", validators=[Required()])
    password = PasswordField("Password:", validators=[Required()])
    enable = PasswordField("Enable:", validators=[Required()])
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
