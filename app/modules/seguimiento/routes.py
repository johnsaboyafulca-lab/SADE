# app/modules/seguimiento/routes.py - VERSIÓN DEFINITIVAMENTE CORREGIDA
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import seguimiento_bp
from app.services.riesgo_calculator_v2 import CalculatorRiesgoIntrasemestral
from app.models import Estudiante, SeguimientoRiesgo
from app.extensions import db
from app.modules.admin.routes import cargar_configuracion  # IMPORTAR CONFIGURACIÓN

@seguimiento_bp.route('/')
@login_required
def index():
    """Panel de control del módulo de seguimiento"""
    return render_template('seguimiento/index.html')

@seguimiento_bp.route('/calcular-riesgo', methods=['POST'])
@login_required
def calcular_riesgo():
    """Ejecutar cálculo de riesgo para todos los estudiantes"""
    try:
        # CORRECCIÓN: Usar semestre por defecto 2025-1 en lugar de 2025-2
        semestre = request.form.get('semestre', '2025-1')
        
        # CORRECCIÓN: Cargar configuración del sistema
        config = cargar_configuracion()
        
        # CORRECCIÓN: Pasar configuración al calculador
        calculador = CalculatorRiesgoIntrasemestral(config)
        
        estudiantes = Estudiante.query.filter_by(activo=True).all()
        estudiantes_procesados = 0
        
        for estudiante in estudiantes:
            try:
                # CORRECCIÓN: Pasar db correctamente
                resultado = calculador.calcular_riesgo_estudiante(estudiante.id, semestre, db)
                
                # Guardar en base de datos
                seguimiento = SeguimientoRiesgo.query.filter_by(
                    estudiante_id=estudiante.id, 
                    semestre=semestre
                ).first()
                
                if seguimiento:
                    seguimiento.categoria_riesgo = resultado['categoria']
                    seguimiento.puntaje_riesgo = resultado['puntaje_riesgo']
                    seguimiento.factores_riesgo = resultado['factores']
                else:
                    seguimiento = SeguimientoRiesgo(
                        estudiante_id=estudiante.id,
                        semestre=semestre,
                        categoria_riesgo=resultado['categoria'],
                        puntaje_riesgo=resultado['puntaje_riesgo'],
                        factores_riesgo=resultado['factores']
                    )
                    db.session.add(seguimiento)
                
                estudiantes_procesados += 1
                
            except Exception as e:
                print(f"Error procesando estudiante {estudiante.id}: {e}")
                continue
        
        db.session.commit()
        
        flash(f'✅ Cálculo de riesgo completado! {estudiantes_procesados} estudiantes evaluados.', 'success')
        return redirect(url_for('seguimiento.resultados'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error ejecutando cálculo: {str(e)}', 'danger')
        return redirect(url_for('seguimiento.index'))

@seguimiento_bp.route('/resultados')
@login_required
def resultados():
    """Mostrar resultados del cálculo de riesgo"""
    # Estadísticas de riesgo
    stats_query = db.session.query(
        SeguimientoRiesgo.categoria_riesgo,
        db.func.count(SeguimientoRiesgo.id)
    ).group_by(SeguimientoRiesgo.categoria_riesgo).all()
    
    estadisticas = {categoria: cantidad for categoria, cantidad in stats_query}
    
    # Últimos cálculos
    ultimos_seguimientos = SeguimientoRiesgo.query.order_by(
        SeguimientoRiesgo.fecha_evaluacion.desc()
    ).limit(10).all()
    
    return render_template('seguimiento/resultados.html',
                         estadisticas=estadisticas,
                         ultimos_seguimientos=ultimos_seguimientos)

@seguimiento_bp.route('/api/calcular-estudiante/<int:estudiante_id>')
@login_required
def calcular_estudiante(estudiante_id):
    """API para calcular riesgo de un estudiante específico"""
    try:
        # CORRECCIÓN: Semestre por defecto 2025-1
        semestre = request.args.get('semestre', '2025-1')
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        
        # CORRECCIÓN: Cargar configuración
        config = cargar_configuracion()
        calculador = CalculatorRiesgoIntrasemestral(config)
        
        resultado = calculador.calcular_riesgo_estudiante(estudiante_id, semestre, db)
        
        return jsonify({
            'estudiante': {
                'id': estudiante.id,
                'codigo': estudiante.codigo_estudiante,
                'nombre': f"{estudiante.nombres} {estudiante.apellidos}"
            },
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500