# app/modules/estudiantes/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import estudiantes_bp
from app.models import Estudiante, SeguimientoRiesgo
from .forms import EstudianteForm
from datetime import datetime
from app.extensions import db

@estudiantes_bp.route('/')
@login_required
def index():
    """Lista de todos los estudiantes"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Query base
    estudiantes_query = Estudiante.query.filter_by(activo=True)
    
    # Búsqueda
    search = request.args.get('search', '')
    if search:
        estudiantes_query = estudiantes_query.filter(
            db.or_(
                Estudiante.nombres.ilike(f'%{search}%'),
                Estudiante.apellidos.ilike(f'%{search}%'),
                Estudiante.codigo_estudiante.ilike(f'%{search}%')
            )
        )
    
    estudiantes = estudiantes_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('estudiantes/index.html', 
                         estudiantes=estudiantes,
                         search=search)

@estudiantes_bp.route('/<int:estudiante_id>')
@login_required
def detalle(estudiante_id):
    """Detalle de un estudiante específico"""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    
    # Obtener seguimientos de riesgo del estudiante
    seguimientos = SeguimientoRiesgo.query.filter_by(
        estudiante_id=estudiante_id
    ).order_by(SeguimientoRiesgo.fecha_evaluacion.desc()).all()
    
    return render_template('estudiantes/detalle.html',
                         estudiante=estudiante,
                         seguimientos=seguimientos)

@estudiantes_bp.route('/en-riesgo')
@login_required
def en_riesgo():
    """Lista de estudiantes en riesgo académico"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Estudiantes con seguimiento de riesgo (excluyendo SIN_RIESGO)
    estudiantes_riesgo = db.session.query(Estudiante, SeguimientoRiesgo).join(
        SeguimientoRiesgo, Estudiante.id == SeguimientoRiesgo.estudiante_id
    ).filter(
        SeguimientoRiesgo.categoria_riesgo != 'SIN_RIESGO',
        Estudiante.activo == True
    ).order_by(SeguimientoRiesgo.puntaje_riesgo.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('estudiantes/en_riesgo.html',
                         estudiantes_riesgo=estudiantes_riesgo)
    
    
@estudiantes_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear nuevo estudiante"""
    form = EstudianteForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si el código de estudiante ya existe
            estudiante_existente = Estudiante.query.filter_by(
                codigo_estudiante=form.codigo_estudiante.data
            ).first()
            
            if estudiante_existente:
                flash('El código de estudiante ya existe', 'danger')
                return render_template('estudiantes/crear.html', form=form)
            
            # Verificar si el email ya existe
            email_existente = Estudiante.query.filter_by(
                email=form.email.data
            ).first()
            
            if email_existente:
                flash('El email ya está registrado', 'danger')
                return render_template('estudiantes/crear.html', form=form)
            
            # Crear nuevo estudiante
            nuevo_estudiante = Estudiante(
                codigo_estudiante=form.codigo_estudiante.data,
                nombres=form.nombres.data,
                apellidos=form.apellidos.data,
                email=form.email.data,
                telefono=form.telefono.data or None,
                fecha_inscripcion=form.fecha_inscripcion.data,
                activo=form.activo.data
            )
            
            db.session.add(nuevo_estudiante)
            db.session.commit()
            
            flash('Estudiante creado exitosamente', 'success')
            return redirect(url_for('estudiantes.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear estudiante: {str(e)}', 'danger')
    
    # Para GET request, establecer fecha actual como default
    if request.method == 'GET':
        form.fecha_inscripcion.data = datetime.utcnow().date()
    
    return render_template('estudiantes/crear.html', form=form)

@estudiantes_bp.route('/<int:estudiante_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(estudiante_id):
    """Editar estudiante existente"""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    form = EstudianteForm(obj=estudiante)
    
    if form.validate_on_submit():
        try:
            # Verificar si el código de estudiante ya existe (excluyendo el actual)
            estudiante_existente = Estudiante.query.filter(
                Estudiante.codigo_estudiante == form.codigo_estudiante.data,
                Estudiante.id != estudiante_id
            ).first()
            
            if estudiante_existente:
                flash('El código de estudiante ya existe', 'danger')
                return render_template('estudiantes/editar.html', form=form, estudiante=estudiante)
            
            # Verificar si el email ya existe (excluyendo el actual)
            email_existente = Estudiante.query.filter(
                Estudiante.email == form.email.data,
                Estudiante.id != estudiante_id
            ).first()
            
            if email_existente:
                flash('El email ya está registrado', 'danger')
                return render_template('estudiantes/editar.html', form=form, estudiante=estudiante)
            
            # Actualizar estudiante
            estudiante.codigo_estudiante = form.codigo_estudiante.data
            estudiante.nombres = form.nombres.data
            estudiante.apellidos = form.apellidos.data
            estudiante.email = form.email.data
            estudiante.telefono = form.telefono.data or None
            estudiante.fecha_inscripcion = form.fecha_inscripcion.data
            estudiante.activo = form.activo.data
            
            db.session.commit()
            
            flash('Estudiante actualizado exitosamente', 'success')
            return redirect(url_for('estudiantes.detalle', estudiante_id=estudiante.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar estudiante: {str(e)}', 'danger')
    
    return render_template('estudiantes/editar.html', form=form, estudiante=estudiante)

@estudiantes_bp.route('/<int:estudiante_id>/eliminar', methods=['POST'])
@login_required
def eliminar(estudiante_id):
    """Eliminar estudiante"""
    try:
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        
        # Verificar si tiene registros relacionados
        if estudiante.inscripciones:
            flash('No se puede eliminar el estudiante porque tiene inscripciones relacionadas', 'danger')
            return redirect(url_for('estudiantes.detalle', estudiante_id=estudiante_id))
        
        db.session.delete(estudiante)
        db.session.commit()
        
        flash('Estudiante eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar estudiante: {str(e)}', 'danger')
    
    return redirect(url_for('estudiantes.index'))