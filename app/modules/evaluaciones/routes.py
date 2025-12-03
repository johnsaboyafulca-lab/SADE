# app/modules/evaluaciones/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import evaluaciones_bp
from app.models import Evaluacion, Curso, Nota, Inscripcion, Estudiante
from app.extensions import db
from .forms import EvaluacionForm, NotaForm
from datetime import datetime

# ===== RUTAS PARA EVALUACIONES =====

@evaluaciones_bp.route('/')
@login_required
def index():
    """Lista de todas las evaluaciones"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Query base con join para curso
    evaluaciones_query = Evaluacion.query.join(Curso)

    # Búsqueda
    search = request.args.get('search', '')
    if search:
        evaluaciones_query = evaluaciones_query.filter(
            db.or_(
                Evaluacion.nombre_evaluacion.ilike(f'%{search}%'),
                Curso.nombre_curso.ilike(f'%{search}%'),
                Curso.codigo_curso.ilike(f'%{search}%')
            )
        )

    # Filtros
    curso_id = request.args.get('curso_id', type=int)
    tipo_evaluacion = request.args.get('tipo_evaluacion', '')
    
    if curso_id:
        evaluaciones_query = evaluaciones_query.filter(Evaluacion.curso_id == curso_id)
    if tipo_evaluacion:
        evaluaciones_query = evaluaciones_query.filter(Evaluacion.tipo_evaluacion == tipo_evaluacion)

    evaluaciones = evaluaciones_query.order_by(
        Curso.semestre.desc(), Curso.nombre_curso, Evaluacion.nombre_evaluacion
    ).paginate(page=page, per_page=per_page, error_out=False)

    # Para los filtros
    cursos = Curso.query.filter_by(activo=True).order_by('semestre', 'nombre_curso').all()
    tipos_evaluacion = [
        'PARCIAL', 'QUIZ', 'TRABAJO', 'PROYECTO', 'LABORATORIO', 'EXAMEN_FINAL', 'OTRO'
    ]

    return render_template('evaluaciones/index.html',
                         evaluaciones=evaluaciones,
                         cursos=cursos,
                         tipos_evaluacion=tipos_evaluacion,
                         search=search,
                         curso_id=curso_id,
                         tipo_evaluacion=tipo_evaluacion)

@evaluaciones_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_evaluacion():
    """Crear nueva evaluación"""
    form = EvaluacionForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la evaluación en el mismo curso
            evaluacion_existente = Evaluacion.query.filter_by(
                nombre_evaluacion=form.nombre_evaluacion.data,
                curso_id=form.curso_id.data
            ).first()
            
            if evaluacion_existente:
                flash('Ya existe una evaluación con este nombre en el mismo curso', 'danger')
                return render_template('evaluaciones/crear_evaluacion.html', form=form)
            
            # Crear nueva evaluación
            nueva_evaluacion = Evaluacion(
                curso_id=form.curso_id.data,
                nombre_evaluacion=form.nombre_evaluacion.data,
                tipo_evaluacion=form.tipo_evaluacion.data,
                peso=form.peso.data,
                fecha_creacion=form.fecha_creacion.data
            )
            
            db.session.add(nueva_evaluacion)
            db.session.commit()
            
            flash('Evaluación creada exitosamente', 'success')
            return redirect(url_for('evaluaciones.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear evaluación: {str(e)}', 'danger')
    
    # Para GET request, establecer fecha actual como default
    if request.method == 'GET':
        form.fecha_creacion.data = datetime.utcnow().date()
        form.peso.data = 100.0  # Valor por defecto
    
    return render_template('evaluaciones/crear_evaluacion.html', form=form)

@evaluaciones_bp.route('/<int:evaluacion_id>')
@login_required
def detalle_evaluacion(evaluacion_id):
    """Detalle de una evaluación específica"""
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    
    # Obtener notas de esta evaluación
    notas = Nota.query.filter_by(
        evaluacion_id=evaluacion_id
    ).join(Inscripcion).join(Estudiante).order_by(Estudiante.apellidos).all()
    
    # Estadísticas
    total_notas = len(notas)
    promedio = db.session.query(db.func.avg(Nota.nota)).filter_by(
        evaluacion_id=evaluacion_id
    ).scalar() or 0
    nota_maxima = db.session.query(db.func.max(Nota.nota)).filter_by(
        evaluacion_id=evaluacion_id
    ).scalar() or 0
    nota_minima = db.session.query(db.func.min(Nota.nota)).filter_by(
        evaluacion_id=evaluacion_id
    ).scalar() or 0

    return render_template('evaluaciones/detalle_evaluacion.html',
                         evaluacion=evaluacion,
                         notas=notas,
                         total_notas=total_notas,
                         promedio=promedio,
                         nota_maxima=nota_maxima,
                         nota_minima=nota_minima)

@evaluaciones_bp.route('/<int:evaluacion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_evaluacion(evaluacion_id):
    """Editar evaluación existente"""
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    form = EvaluacionForm(obj=evaluacion)
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la evaluación (excluyendo la actual)
            evaluacion_existente = Evaluacion.query.filter(
                Evaluacion.nombre_evaluacion == form.nombre_evaluacion.data,
                Evaluacion.curso_id == form.curso_id.data,
                Evaluacion.id != evaluacion_id
            ).first()
            
            if evaluacion_existente:
                flash('Ya existe una evaluación con este nombre en el mismo curso', 'danger')
                return render_template('evaluaciones/editar_evaluacion.html', form=form, evaluacion=evaluacion)
            
            # Actualizar evaluación
            evaluacion.curso_id = form.curso_id.data
            evaluacion.nombre_evaluacion = form.nombre_evaluacion.data
            evaluacion.tipo_evaluacion = form.tipo_evaluacion.data
            evaluacion.peso = form.peso.data
            evaluacion.fecha_creacion = form.fecha_creacion.data
            
            db.session.commit()
            
            flash('Evaluación actualizada exitosamente', 'success')
            return redirect(url_for('evaluaciones.detalle_evaluacion', evaluacion_id=evaluacion.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar evaluación: {str(e)}', 'danger')
    
    return render_template('evaluaciones/editar_evaluacion.html', form=form, evaluacion=evaluacion)

@evaluaciones_bp.route('/<int:evaluacion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_evaluacion(evaluacion_id):
    """Eliminar evaluación"""
    try:
        evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
        
        # Verificar si tiene registros relacionados
        if evaluacion.notas:
            flash('No se puede eliminar la evaluación porque tiene notas relacionadas', 'danger')
            return redirect(url_for('evaluaciones.detalle_evaluacion', evaluacion_id=evaluacion_id))
        
        db.session.delete(evaluacion)
        db.session.commit()
        
        flash('Evaluación eliminada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar evaluación: {str(e)}', 'danger')
    
    return redirect(url_for('evaluaciones.index'))

# ===== RUTAS PARA NOTAS =====

@evaluaciones_bp.route('/notas')
@login_required
def notas_index():
    """Lista de todas las notas"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Query base con joins
    notas_query = Nota.query.join(Inscripcion).join(Estudiante).join(Evaluacion).join(Curso)

    # Filtros
    estudiante_id = request.args.get('estudiante_id', type=int)
    curso_id = request.args.get('curso_id', type=int)
    evaluacion_id = request.args.get('evaluacion_id', type=int)
    
    if estudiante_id:
        notas_query = notas_query.filter(Inscripcion.estudiante_id == estudiante_id)
    if curso_id:
        notas_query = notas_query.filter(Inscripcion.curso_id == curso_id)
    if evaluacion_id:
        notas_query = notas_query.filter(Nota.evaluacion_id == evaluacion_id)

    notas = notas_query.order_by(
        Nota.fecha_registro.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    # Para los filtros
    estudiantes = Estudiante.query.filter_by(activo=True).order_by('apellidos').all()
    cursos = Curso.query.filter_by(activo=True).order_by('semestre', 'nombre_curso').all()
    evaluaciones = Evaluacion.query.join(Curso).filter(
        Curso.activo == True
    ).order_by(Curso.nombre_curso, Evaluacion.nombre_evaluacion).all()

    return render_template('evaluaciones/notas_index.html',
                         notas=notas,
                         estudiantes=estudiantes,
                         cursos=cursos,
                         evaluaciones=evaluaciones,
                         estudiante_id=estudiante_id,
                         curso_id=curso_id,
                         evaluacion_id=evaluacion_id)

@evaluaciones_bp.route('/notas/crear', methods=['GET', 'POST'])
@login_required
def crear_nota():
    """Crear nueva nota"""
    form = NotaForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la nota para esta inscripción y evaluación
            nota_existente = Nota.query.filter_by(
                inscripcion_id=form.inscripcion_id.data,
                evaluacion_id=form.evaluacion_id.data
            ).first()
            
            if nota_existente:
                flash('Ya existe una nota para este estudiante en esta evaluación', 'danger')
                return render_template('evaluaciones/crear_nota.html', form=form)
            
            # Crear nueva nota
            nueva_nota = Nota(
                inscripcion_id=form.inscripcion_id.data,
                evaluacion_id=form.evaluacion_id.data,
                nota=form.nota.data,
                fecha_registro=form.fecha_registro.data,
                observaciones=form.observaciones.data or None
            )
            
            db.session.add(nueva_nota)
            db.session.commit()
            
            flash('Nota creada exitosamente', 'success')
            return redirect(url_for('evaluaciones.notas_index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear nota: {str(e)}', 'danger')
    
    # Para GET request, establecer fecha actual como default
    if request.method == 'GET':
        form.fecha_registro.data = datetime.utcnow().date()
    
    return render_template('evaluaciones/crear_nota.html', form=form)

@evaluaciones_bp.route('/notas/<int:nota_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_nota(nota_id):
    """Editar nota existente"""
    nota = Nota.query.get_or_404(nota_id)
    form = NotaForm(obj=nota)
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la nota (excluyendo la actual)
            nota_existente = Nota.query.filter(
                Nota.inscripcion_id == form.inscripcion_id.data,
                Nota.evaluacion_id == form.evaluacion_id.data,
                Nota.id != nota_id
            ).first()
            
            if nota_existente:
                flash('Ya existe una nota para este estudiante en esta evaluación', 'danger')
                return render_template('evaluaciones/editar_nota.html', form=form, nota=nota)
            
            # Actualizar nota
            nota.inscripcion_id = form.inscripcion_id.data
            nota.evaluacion_id = form.evaluacion_id.data
            nota.nota = form.nota.data
            nota.fecha_registro = form.fecha_registro.data
            nota.observaciones = form.observaciones.data or None
            
            db.session.commit()
            
            flash('Nota actualizada exitosamente', 'success')
            return redirect(url_for('evaluaciones.notas_index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar nota: {str(e)}', 'danger')
    
    return render_template('evaluaciones/editar_nota.html', form=form, nota=nota)

@evaluaciones_bp.route('/notas/<int:nota_id>/eliminar', methods=['POST'])
@login_required
def eliminar_nota(nota_id):
    """Eliminar nota"""
    try:
        nota = Nota.query.get_or_404(nota_id)
        
        db.session.delete(nota)
        db.session.commit()
        
        flash('Nota eliminada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar nota: {str(e)}', 'danger')
    
    return redirect(url_for('evaluaciones.notas_index'))