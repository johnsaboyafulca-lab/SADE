# app/modules/cursos/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import cursos_bp
from app.models import Curso, Inscripcion, Evaluacion,Estudiante
from app.extensions import db
from .forms import CursoForm

@cursos_bp.route('/')
@login_required
def index():
    """Lista de todos los cursos"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Query base
    cursos_query = Curso.query

    # Búsqueda
    search = request.args.get('search', '')
    if search:
        cursos_query = cursos_query.filter(
            db.or_(
                Curso.nombre_curso.ilike(f'%{search}%'),
                Curso.codigo_curso.ilike(f'%{search}%'),
                Curso.semestre.ilike(f'%{search}%')
            )
        )

    cursos = cursos_query.order_by(Curso.semestre.desc(), Curso.nombre_curso).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('cursos/index.html',
                         cursos=cursos,
                         search=search)

@cursos_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear nuevo curso"""
    form = CursoForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si el código de curso ya existe en el mismo semestre
            curso_existente = Curso.query.filter_by(
                codigo_curso=form.codigo_curso.data,
                semestre=form.semestre.data
            ).first()
            
            if curso_existente:
                flash('Ya existe un curso con este código en el mismo semestre', 'danger')
                return render_template('cursos/crear.html', form=form)
            
            # Crear nuevo curso
            nuevo_curso = Curso(
                codigo_curso=form.codigo_curso.data,
                nombre_curso=form.nombre_curso.data,
                creditos=form.creditos.data,
                semestre=form.semestre.data,
                activo=form.activo.data
            )
            
            db.session.add(nuevo_curso)
            db.session.commit()
            
            flash('Curso creado exitosamente', 'success')
            return redirect(url_for('cursos.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear curso: {str(e)}', 'danger')
    
    return render_template('cursos/crear.html', form=form)


@cursos_bp.route('/<int:curso_id>')
@login_required
def detalle(curso_id):
    """Detalle de un curso específico"""
    curso = Curso.query.get_or_404(curso_id)
    
    # Obtener inscripciones del curso
    inscripciones = (
        Inscripcion.query
        .filter_by(curso_id=curso_id)
        .join(Inscripcion.estudiante)               
        .order_by(Estudiante.apellidos)           
        .all()
    )
    
    # Obtener evaluaciones del curso
    evaluaciones = (
        Evaluacion.query
        .filter_by(curso_id=curso_id)
        .order_by(Evaluacion.fecha_creacion)
        .all()
    )
    
    return render_template(
        'cursos/detalle.html',
        curso=curso,
        inscripciones=inscripciones,
        evaluaciones=evaluaciones
    )



@cursos_bp.route('/<int:curso_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(curso_id):
    """Editar curso existente"""
    curso = Curso.query.get_or_404(curso_id)
    form = CursoForm(obj=curso)
    
    if form.validate_on_submit():
        try:
            # Verificar si el código de curso ya existe (excluyendo el actual)
            curso_existente = Curso.query.filter(
                Curso.codigo_curso == form.codigo_curso.data,
                Curso.semestre == form.semestre.data,
                Curso.id != curso_id
            ).first()
            
            if curso_existente:
                flash('Ya existe un curso con este código en el mismo semestre', 'danger')
                return render_template('cursos/editar.html', form=form, curso=curso)
            
            # Actualizar curso
            curso.codigo_curso = form.codigo_curso.data
            curso.nombre_curso = form.nombre_curso.data
            curso.creditos = form.creditos.data
            curso.semestre = form.semestre.data
            curso.activo = form.activo.data
            
            db.session.commit()
            
            flash('Curso actualizado exitosamente', 'success')
            return redirect(url_for('cursos.detalle', curso_id=curso.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar curso: {str(e)}', 'danger')
    
    return render_template('cursos/editar.html', form=form, curso=curso)

@cursos_bp.route('/<int:curso_id>/eliminar', methods=['POST'])
@login_required
def eliminar(curso_id):
    """Eliminar curso"""
    try:
        curso = Curso.query.get_or_404(curso_id)
        
        # Verificar si tiene registros relacionados
        if curso.inscripciones:
            flash('No se puede eliminar el curso porque tiene inscripciones relacionadas', 'danger')
            return redirect(url_for('cursos.detalle', curso_id=curso_id))
        
        if curso.evaluaciones:
            flash('No se puede eliminar el curso porque tiene evaluaciones relacionadas', 'danger')
            return redirect(url_for('cursos.detalle', curso_id=curso_id))
        
        db.session.delete(curso)
        db.session.commit()
        
        flash('Curso eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar curso: {str(e)}', 'danger')
    
    return redirect(url_for('cursos.index'))