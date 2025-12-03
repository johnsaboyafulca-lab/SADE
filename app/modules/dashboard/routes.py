# app/modules/dashboard/routes.py
from flask import render_template, jsonify
from flask_login import login_required, current_user
from . import dashboard_bp
from app.models import Estudiante, SeguimientoRiesgo, Curso, Inscripcion
from app.extensions import db

@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    """Panel principal del dashboard"""
    # Estadísticas básicas (las mejoraremos después)
    total_estudiantes = Estudiante.query.filter_by(activo=True).count()
    total_cursos = Curso.query.filter_by(activo=True).count()
    
    # Estudiantes en riesgo (usaremos datos de prueba por ahora)
    estudiantes_riesgo = SeguimientoRiesgo.query.filter(
        SeguimientoRiesgo.categoria_riesgo != 'SIN_RIESGO'
    ).count()
    
    return render_template('dashboard/index.html',
                         total_estudiantes=total_estudiantes,
                         total_cursos=total_cursos,
                         estudiantes_riesgo=estudiantes_riesgo,
                         usuario_actual=current_user)

@dashboard_bp.route('/estadisticas')
@login_required
def estadisticas():
    """Endpoint para estadísticas en JSON (para gráficos)"""
    try:
        # Conteo por categoría de riesgo
        categorias_riesgo = db.session.query(
            SeguimientoRiesgo.categoria_riesgo,
            db.func.count(SeguimientoRiesgo.id)
        ).group_by(SeguimientoRiesgo.categoria_riesgo).all()
        
        estadisticas = {
            'categorias_riesgo': {
                categoria: cantidad for categoria, cantidad in categorias_riesgo
            },
            'total_estudiantes': Estudiante.query.filter_by(activo=True).count(),
            'total_cursos_activos': Curso.query.filter_by(activo=True).count()
        }
        
        return jsonify(estadisticas)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500