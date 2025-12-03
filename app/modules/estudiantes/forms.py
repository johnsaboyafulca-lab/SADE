# app/modules/estudiantes/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional
from wtforms.widgets import TextArea

class EstudianteForm(FlaskForm):
    codigo_estudiante = StringField('Código de Estudiante', 
                                   validators=[DataRequired(), Length(max=20)])
    nombres = StringField('Nombres', 
                         validators=[DataRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', 
                           validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), Length(max=150)])
    telefono = StringField('Teléfono', 
                          validators=[Optional(), Length(max=15)])
    fecha_inscripcion = DateField('Fecha de Inscripción', 
                                 validators=[DataRequired()])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Estudiante')