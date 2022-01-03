from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, IPAddress


class NodeForm(FlaskForm):
    hostname = StringField("Hostname:", validators=[InputRequired()])
    description = StringField("Description:")
    ip_address = StringField("IP Address:", validators=[InputRequired(), IPAddress()])
    port = IntegerField("Port:", default=22, validators=[InputRequired()])
    device_type = StringField("Device Type:", validators=[InputRequired()])
    napalm_driver = StringField("Napalm Driver:")
    scrapli_driver = StringField("Scrapli Driver:")
    model = StringField("Model:")
    os_type = StringField("OS Type:")
    os_version = StringField("OS Version:")
    username = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    enable = PasswordField("Enable:", validators=[InputRequired()])
    submit = SubmitField("Submit")
    reset = SubmitField("Reset")
