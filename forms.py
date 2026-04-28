from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Length
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Optional
from wtforms import HiddenField
from wtforms.fields import DateTimeLocalField


class SignInForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField("Увійти")

class SignUpForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    email = StringField(validators=[Optional(), Email()])
    fullname = StringField(validators=[Optional()])
    submit = SubmitField("Реєстрація")


class ReservationForm(FlaskForm):
    time = StringField(validators=[DataRequired()])
    table = HiddenField()
    submit = SubmitField("Забронювати")