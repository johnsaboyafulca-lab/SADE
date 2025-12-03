import os
from flask import Flask
from app.extensions import db, migrate, login_manager
from config import config_by_name

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuración
    config_name = config_name or os.getenv("FLASK_CONFIG", "development")
    app.config.from_object(config_by_name[config_name])

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    # IMPORTAR MODELOS DESPUÉS de inicializar db - ESTO ES CLAVE
    with app.app_context():
        # Importar todos los modelos para que SQLAlchemy los registre
        from app.models import (
            Usuario, Estudiante, Curso, Inscripcion, 
            Asistencia, Evaluacion, Nota, 
            SeguimientoRiesgo, Intervencion, Ciclo, Reporte
        )
    
    # Configurar user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # ============================================================================
    # REGISTRAR BLUEPRINTS - AQUÍ VAN TODOS LOS MÓDULOS
    # ============================================================================
    
    # 1. Auth (Autenticación)
    from app.modules.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.modules.main import main_bp
    app.register_blueprint(main_bp)
    
    # 2. Dashboard (Panel principal)
    from app.modules.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    # 3. Estudiantes (Gestión de estudiantes)
    from app.modules.estudiantes import estudiantes_bp
    app.register_blueprint(estudiantes_bp)
    
    # 4. Seguimiento (Cálculos de riesgo)
    from app.modules.seguimiento import seguimiento_bp
    app.register_blueprint(seguimiento_bp)
    
    # 5. Importación
    from app.modules.importacion import importacion_bp
    app.register_blueprint(importacion_bp)
    
    # 6. Administración
    from app.modules.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # 7. Reportes (Generación de reportes)
    from app.modules.reportes import reportes_bp
    app.register_blueprint(reportes_bp)
    
    # 8. Cursos
    from app.modules.cursos import cursos_bp
    app.register_blueprint(cursos_bp)
    
    # 9. Inscripciones
    from app.modules.inscripciones import inscripciones_bp
    app.register_blueprint(inscripciones_bp)
    
    # 10. Evaluaciones
    from app.modules.evaluaciones import evaluaciones_bp
    app.register_blueprint(evaluaciones_bp)
    
    # 11. Asistencias
    from app.modules.asistencias import asistencias_bp
    app.register_blueprint(asistencias_bp)
    
  
  
    
    return app