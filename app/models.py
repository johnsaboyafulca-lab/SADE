# app/models.py
from app.extensions import db  # Usar la misma instancia de extensions
from flask_login import UserMixin
from datetime import datetime

# TODOS los modelos usan db desde extensions

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_estudiante = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(15))
    fecha_inscripcion = db.Column(db.Date, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    inscripciones = db.relationship('Inscripcion', backref='estudiante', lazy=True)
    seguimientos = db.relationship('SeguimientoRiesgo', backref='estudiante', lazy=True)
    intervenciones = db.relationship('Intervencion', backref='estudiante', lazy=True)
    
    def __repr__(self):
        return f'<Estudiante {self.codigo_estudiante}: {self.nombres} {self.apellidos}>'

class Ciclo(db.Model):
    __tablename__ = 'ciclos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  # Ej: "Ciclo I 2025", "Ciclo II 2025"
    codigo_ciclo = db.Column(db.String(20), unique=True, nullable=False)  # Ej: "2025-1", "2025-2"
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    cursos = db.relationship('Curso', backref='ciclo', lazy=True)
    
    def __repr__(self):
        return f'<Ciclo {self.codigo_ciclo}: {self.nombre}>'

class Curso(db.Model):
    __tablename__ = 'cursos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_curso = db.Column(db.String(20), unique=True, nullable=False)
    nombre_curso = db.Column(db.String(100), nullable=False)
    creditos = db.Column(db.Integer, default=3)
    semestre = db.Column(db.String(10), nullable=False)
    ciclo_id = db.Column(db.Integer, db.ForeignKey('ciclos.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    inscripciones = db.relationship('Inscripcion', backref='curso', lazy=True)
    evaluaciones = db.relationship('Evaluacion', backref='curso', lazy=True)
    
    def __repr__(self):
        return f'<Curso {self.codigo_curso}: {self.nombre_curso}>'

class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    fecha_inscripcion = db.Column(db.Date, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='ACTIVO')
    
    # Relaciones
    asistencias = db.relationship('Asistencia', backref='inscripcion', lazy=True)
    notas = db.relationship('Nota', backref='inscripcion', lazy=True)
    
    def __repr__(self):
        return f'<Inscripcion Estudiante:{self.estudiante_id} Curso:{self.curso_id}>'

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripciones.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, default=False)
    justificado = db.Column(db.Boolean, default=False)
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Asistencia {self.fecha} - Presente: {self.presente}>'

class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    nombre_evaluacion = db.Column(db.String(100), nullable=False)
    tipo_evaluacion = db.Column(db.String(50))
    peso = db.Column(db.Numeric(5, 2), default=100.0)
    fecha_creacion = db.Column(db.Date, default=datetime.utcnow)
    
    # Relaciones
    notas = db.relationship('Nota', backref='evaluacion', lazy=True)
    
    def __repr__(self):
        return f'<Evaluacion {self.nombre_evaluacion}>'

class Nota(db.Model):
    __tablename__ = 'notas'
    
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripciones.id'), nullable=False)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)
    nota = db.Column(db.Numeric(5, 2))
    fecha_registro = db.Column(db.Date, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Nota {self.nota}>'

class SeguimientoRiesgo(db.Model):
    __tablename__ = 'seguimiento_riesgo'
    
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    semestre = db.Column(db.String(10), nullable=False)
    categoria_riesgo = db.Column(db.String(20), default='SIN_RIESGO')
    puntaje_riesgo = db.Column(db.Numeric(5, 2), default=0.0)
    fecha_evaluacion = db.Column(db.Date, default=datetime.utcnow)
    factores_riesgo = db.Column(db.JSON)
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<SeguimientoRiesgo {self.estudiante_id} - {self.categoria_riesgo}>'

class Intervencion(db.Model):
    __tablename__ = 'intervenciones'
    
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    tipo_intervencion = db.Column(db.String(50))
    descripcion = db.Column(db.Text, nullable=False)
    fecha_intervencion = db.Column(db.Date, default=datetime.utcnow)
    responsable = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='PENDIENTE')
    resultado = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Intervencion {self.tipo_intervencion} - {self.estado}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    rol = db.Column(db.String(20), default='docente')
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

class Reporte(db.Model):
    __tablename__ = 'reportes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_reporte = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    parametros = db.Column(db.JSON)  # Parámetros usados para generar el reporte
    contenido = db.Column(db.Text)   # HTML/JSON del reporte generado
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    archivo_path = db.Column(db.String(500))  # Ruta del archivo PDF generado
    
    # Relación
    usuario = db.relationship('Usuario', backref='reportes')
    
    def __repr__(self):
        return f'<Reporte {self.tipo_reporte} - {self.fecha_generacion}>'