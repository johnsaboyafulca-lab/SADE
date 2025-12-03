# app/modules/cursos/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class CursoForm(FlaskForm):
    codigo_curso = StringField('Código del Curso', 
                              validators=[DataRequired(), Length(max=20)])
    nombre_curso = StringField('Nombre del Curso', 
                              validators=[DataRequired(), Length(max=100)])
    creditos = IntegerField('Créditos', 
                           validators=[DataRequired(), NumberRange(min=1, max=10)],
                           default=3)
    semestre = StringField('Semestre', 
                          validators=[DataRequired(), Length(max=10)])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Curso')