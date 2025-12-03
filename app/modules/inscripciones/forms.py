# app/modules/inscripciones/forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional,length
from app.models import Estudiante, Curso

class InscripcionForm(FlaskForm):
    estudiante_id = SelectField('Estudiante', coerce=int, validators=[DataRequired()])
    curso_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    fecha_inscripcion = DateField('Fecha de Inscripción', validators=[DataRequired()])
    estado = SelectField('Estado', 
                        choices=[
                            ('ACTIVO', 'Activo'),
                            ('INACTIVO', 'Inactivo'), 
                            ('RETIRADO', 'Retirado'),
                            ('APROBADO', 'Aprobado'),
                            ('REPROBADO', 'Reprobado')
                        ],
                        validators=[DataRequired()])
    submit = SubmitField('Guardar Inscripción')
    
    def __init__(self, *args, **kwargs):
        super(InscripcionForm, self).__init__(*args, **kwargs)
        # Cargar estudiantes activos
        self.estudiante_id.choices = [
            (est.id, f"{est.codigo_estudiante} - {est.nombres} {est.apellidos}")
            for est in Estudiante.query.filter_by(activo=True).order_by('apellidos').all()
        ]
        # Cargar cursos activos
        self.curso_id.choices = [
            (curso.id, f"{curso.codigo_curso} - {curso.nombre_curso} ({curso.semestre})")
            for curso in Curso.query.filter_by(activo=True).order_by('semestre', 'nombre_curso').all()
        ]
        
# ------------------------------------------------------------------
# MATRICULAS MASIVAS    
# app/modules/inscripciones/forms.py - AÑADIR
class MatriculaMasivaForm(FlaskForm):
    semestre = SelectField('Semestre', coerce=str, validators=[DataRequired()])
    grupo_estudiantes = SelectField('Grupo de Estudiantes', 
        choices=[
            ('todos', 'Todos los estudiantes activos'),
            ('nuevos', 'Solo estudiantes nuevos en el semestre')
        ], validators=[DataRequired()])
    fecha_inscripcion = DateField('Fecha de Matrícula', validators=[DataRequired()])
    estado = SelectField('Estado Inicial',
        choices=[
            ('ACTIVO', 'Activo'),
            ('OBSERVADO', 'Observado')
        ], default='ACTIVO')
    submit = SubmitField('Generar Matrícula Masiva')
    
    def __init__(self, *args, **kwargs):
        super(MatriculaMasivaForm, self).__init__(*args, **kwargs)
        # Importar la aplicación para acceder a la BD
        from flask import current_app
        from app.models import Curso
        
        with current_app.app_context():
            try:
                from app.extensions import db
                semestres = db.session.query(Curso.semestre)\
                    .filter(Curso.activo == True)\
                    .distinct()\
                    .order_by(Curso.semestre)\
                    .all()
                
                self.semestre.choices = [(sem[0], f'Semestre {sem[0]}') for sem in semestres]
                
                if not self.semestre.choices:
                    self.semestre.choices = [('', 'No hay cursos activos')]
                    
            except Exception as e:
                print(f"Error cargando semestres: {e}")
                # Fallback a semestres por defecto
                self.semestre.choices = [
                    ('I', 'Semestre I'), ('II', 'Semestre II'), ('III', 'Semestre III'),
                    ('IV', 'Semestre IV'), ('V', 'Semestre V'), ('VI', 'Semestre VI')
                ]