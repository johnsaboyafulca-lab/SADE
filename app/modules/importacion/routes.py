# app/modules/importacion/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import pandas as pd
import io
from datetime import datetime
from . import importacion_bp
from app.models import Estudiante, Curso, Inscripcion, Evaluacion, Nota, SeguimientoRiesgo
from app.extensions import db

@importacion_bp.route('/')
@login_required
def index():
    """Panel de importación de datos"""
    return render_template('importacion/index.html')

@importacion_bp.route('/importar-estudiantes', methods=['POST'])
@login_required
def importar_estudiantes():
    """Importar estudiantes desde archivo Excel/CSV"""
    try:
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        # Leer archivo
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        # Validar columnas requeridas
        columnas_requeridas = ['codigo_estudiante', 'nombres', 'apellidos', 'email']
        for columna in columnas_requeridas:
            if columna not in df.columns:
                flash(f'Columna requerida faltante: {columna}', 'danger')
                return redirect(url_for('importacion.index'))
        
        estudiantes_importados = 0
        estudiantes_actualizados = 0
        
        for _, fila in df.iterrows():
            # Buscar si el estudiante ya existe
            estudiante = Estudiante.query.filter_by(
                codigo_estudiante=fila['codigo_estudiante']
            ).first()
            
            if estudiante:
                # Actualizar estudiante existente
                estudiante.nombres = fila['nombres']
                estudiante.apellidos = fila['apellidos']
                estudiante.email = fila['email']
                estudiante.telefono = fila.get('telefono', '')
                estudiantes_actualizados += 1
            else:
                # Crear nuevo estudiante
                estudiante = Estudiante(
                    codigo_estudiante=fila['codigo_estudiante'],
                    nombres=fila['nombres'],
                    apellidos=fila['apellidos'],
                    email=fila['email'],
                    telefono=fila.get('telefono', ''),
                    activo=True
                )
                db.session.add(estudiante)
                estudiantes_importados += 1
        
        db.session.commit()
        
        flash(f'✅ Importación exitosa: {estudiantes_importados} nuevos, {estudiantes_actualizados} actualizados', 'success')
        return redirect(url_for('importacion.resultados'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error en importación: {str(e)}', 'danger')
        return redirect(url_for('importacion.index'))

@importacion_bp.route('/importar-cursos', methods=['POST'])
@login_required
def importar_cursos():
    """Importar cursos desde archivo Excel/CSV"""
    try:
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        # Leer archivo
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        # Validar columnas requeridas
        columnas_requeridas = ['codigo_curso', 'nombre_curso', 'semestre']
        for columna in columnas_requeridas:
            if columna not in df.columns:
                flash(f'Columna requerida faltante: {columna}', 'danger')
                return redirect(url_for('importacion.index'))
        
        cursos_importados = 0
        cursos_actualizados = 0
        
        for _, fila in df.iterrows():
            # Buscar si el curso ya existe
            curso = Curso.query.filter_by(
                codigo_curso=fila['codigo_curso'],
                semestre=fila['semestre']
            ).first()
            
            if curso:
                # Actualizar curso existente
                curso.nombre_curso = fila['nombre_curso']
                curso.creditos = fila.get('creditos', 3)
                cursos_actualizados += 1
            else:
                # Crear nuevo curso
                curso = Curso(
                    codigo_curso=fila['codigo_curso'],
                    nombre_curso=fila['nombre_curso'],
                    creditos=fila.get('creditos', 3),
                    semestre=fila['semestre'],
                    activo=True
                )
                db.session.add(curso)
                cursos_importados += 1
        
        db.session.commit()
        
        flash(f'✅ Cursos importados: {cursos_importados} nuevos, {cursos_actualizados} actualizados', 'success')
        return redirect(url_for('importacion.resultados'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error en importación: {str(e)}', 'danger')
        return redirect(url_for('importacion.index'))

@importacion_bp.route('/importar-notas', methods=['POST'])
@login_required
def importar_notas():
    """Importar notas desde archivo Excel/CSV"""
    try:
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('importacion.index'))
        
        # Leer archivo
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        # Validar columnas requeridas
        columnas_requeridas = ['codigo_estudiante', 'codigo_curso', 'nombre_evaluacion', 'nota']
        for columna in columnas_requeridas:
            if columna not in df.columns:
                flash(f'Columna requerida faltante: {columna}', 'danger')
                return redirect(url_for('importacion.index'))
        
        notas_importadas = 0
        
        for _, fila in df.iterrows():
            # Buscar estudiante y curso
            estudiante = Estudiante.query.filter_by(
                codigo_estudiante=fila['codigo_estudiante']
            ).first()
            
            curso = Curso.query.filter_by(
                codigo_curso=fila['codigo_curso']
            ).first()
            
            if not estudiante or not curso:
                continue  # Saltar si no encuentra estudiante o curso
            
            # Buscar o crear inscripción
            inscripcion = Inscripcion.query.filter_by(
                estudiante_id=estudiante.id,
                curso_id=curso.id
            ).first()
            
            if not inscripcion:
                inscripcion = Inscripcion(
                    estudiante_id=estudiante.id,
                    curso_id=curso.id,
                    estado='ACTIVO'
                )
                db.session.add(inscripcion)
                db.session.flush()  # Para obtener el ID
            
            # Buscar o crear evaluación
            evaluacion = Evaluacion.query.filter_by(
                curso_id=curso.id,
                nombre_evaluacion=fila['nombre_evaluacion']
            ).first()
            
            if not evaluacion:
                evaluacion = Evaluacion(
                    curso_id=curso.id,
                    nombre_evaluacion=fila['nombre_evaluacion'],
                    tipo_evaluacion='PARCIAL',
                    peso=100.0
                )
                db.session.add(evaluacion)
                db.session.flush()
            
            # Buscar o crear nota
            nota = Nota.query.filter_by(
                inscripcion_id=inscripcion.id,
                evaluacion_id=evaluacion.id
            ).first()
            
            if nota:
                # Actualizar nota existente
                nota.nota = float(fila['nota'])
            else:
                # Crear nueva nota
                nota = Nota(
                    inscripcion_id=inscripcion.id,
                    evaluacion_id=evaluacion.id,
                    nota=float(fila['nota']),
                    fecha_registro=pd.to_datetime(fila.get('fecha', datetime.utcnow()))
                )
                db.session.add(nota)
            
            notas_importadas += 1
        
        db.session.commit()
        
        flash(f'✅ Notas importadas: {notas_importadas} registros procesados', 'success')
        return redirect(url_for('importacion.resultados'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error en importación: {str(e)}', 'danger')
        return redirect(url_for('importacion.index'))

@importacion_bp.route('/resultados')
@login_required
def resultados():
    """Mostrar resultados de importaciones"""
    # Obtener estadísticas actuales
    estadisticas = {
        'estudiantes': Estudiante.query.filter_by(activo=True).count(),
        'cursos': Curso.query.filter_by(activo=True).count(),
        'notas': Nota.query.count(),
        'riesgo': SeguimientoRiesgo.query.filter(
            SeguimientoRiesgo.categoria_riesgo != 'SIN_RIESGO'
        ).count()
    }
    
    return render_template('importacion/resultados.html', estadisticas=estadisticas)

@importacion_bp.route('/descargar-plantilla/<tipo>')
@login_required
def descargar_plantilla(tipo):
    """Descargar plantillas para importación"""
    if tipo == 'estudiantes':
        # Crear DataFrame de ejemplo para estudiantes
        df = pd.DataFrame({
            'codigo_estudiante': ['2024EST001', '2024EST002'],
            'nombres': ['Juan Carlos', 'María Elena'],
            'apellidos': ['García López', 'Rodríguez Martínez'],
            'email': ['juan.garcia@ejemplo.com', 'maria.rodriguez@ejemplo.com'],
            'telefono': ['123456789', '987654321']
        })
    elif tipo == 'cursos':
        df = pd.DataFrame({
            'codigo_curso': ['MAT101', 'PROG102'],
            'nombre_curso': ['Matemáticas Básicas', 'Programación Python'],
            'creditos': [4, 3],
            'semestre': ['2024-1', '2024-1']
        })
    elif tipo == 'notas':
        df = pd.DataFrame({
            'codigo_estudiante': ['2024EST001', '2024EST001'],
            'codigo_curso': ['MAT101', 'MAT101'],
            'nombre_evaluacion': ['Parcial 1', 'Parcial 2'],
            'nota': [15.5, 14.0],
            'fecha': ['2024-03-15', '2024-04-20']
        })
    else:
        flash('Tipo de plantilla no válido', 'danger')
        return redirect(url_for('importacion.index'))
    
    # Crear archivo en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Plantilla', index=False)
    output.seek(0)
    
    return send_file(
        output,
        download_name=f'plantilla_{tipo}.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )