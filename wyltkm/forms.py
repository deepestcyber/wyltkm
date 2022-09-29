from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, RadioField, IntegerField
from wtforms.validators import DataRequired


class ConfigForm(FlaskForm):
    k = RadioField("Kind", choices=[
        ("b", "bottom"),
        ("tb", "top/bottom"),
    ], default="b")
    c = StringField("Content")
    h = StringField("Heading")
    f = RadioField("Format", choices=[
        ("svg", "SVG"),
        ("png", "PNG"),
    ], default="svg")
    w = IntegerField("Width")
    submit = SubmitField("generate")
