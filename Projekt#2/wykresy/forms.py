
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])


class GraphForm(FlaskForm):
    marka = SelectField('Marka')
    rocznik_min = SelectField('Rocznik min')
    rocznik_max = SelectField('Rocznik max')
