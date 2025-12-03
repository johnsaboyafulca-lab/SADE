# app/modules/asistencias/forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from datetime import datetime

class AsistenciaForm(FlaskForm):
    inscripcion_id = SelectField('Inscripción', coerce=int, validators=[DataRequired()])
    fecha = DateField('Fecha de Clase', validators=[DataRequired()], default=datetime.utcnow)
    presente = BooleanField('Presente', default=True)
    justificado = BooleanField('Justificado', default=False)
    observaciones = StringField('Observaciones', 
                               validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar Asistencia')
    
    def __init__(self, *args, **kwargs):
        super(AsistenciaForm, self).__init__(*args, **kwargs)
        # Importar modelos dentro del método para evitar importaciones circulares
        from app.models import Inscripcion, Estudiante, Curso
        
        # Cargar inscripciones activas
        self.inscripcion_id.choices = [
            (ins.id, f"{ins.estudiante.codigo_estudiante} - {ins.estudiante.nombres} {ins.estudiante.apellidos} - {ins.curso.nombre_curso}")
            for ins in Inscripcion.query.join(Estudiante).join(Curso).filter(
                Inscripcion.estado == 'ACTIVO',
                Estudiante.activo == True,
                Curso.activo == True
            ).order_by(Curso.nombre_curso, Estudiante.apellidos).all()
        ]

class AsistenciaMasivaForm(FlaskForm):
    curso_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    fecha = DateField('Fecha de Clase', validators=[DataRequired()], default=datetime.utcnow)
    submit = SubmitField('Generar Formulario Masivo')
    
    def __init__(self, *args, **kwargs):
        super(AsistenciaMasivaForm, self).__init__(*args, **kwargs)
        # Importar modelos dentro del método
        from app.models import Curso
        
        # Cargar cursos activos
        self.curso_id.choices = [
            (curso.id, f"{curso.codigo_curso} - {curso.nombre_curso} ({curso.semestre})")
            for curso in Curso.query.filter_by(activo=True).order_by('semestre', 'nombre_curso').all()
        ]