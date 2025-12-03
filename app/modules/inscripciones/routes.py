# app/modules/inscripciones/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import inscripciones_bp
from app.models import Inscripcion, Estudiante, Curso, Asistencia, Nota, Evaluacion
from app.extensions import db
from .forms import InscripcionForm
from datetime import datetime
from .forms import InscripcionForm, MatriculaMasivaForm 


# PARA MATRICULAR DE UNA SOLA VEZ EN UN CICLO
@inscripciones_bp.route('/matricula-masiva', methods=['GET', 'POST'])
@login_required
def matricula_masiva():
    """Matrícula masiva de estudiantes a todos los cursos de un semestre"""
    
    form = MatriculaMasivaForm()
    
    if form.validate_on_submit():
        try:
            # ✅ CORREGIDO: usar semestre en lugar de ciclo_id
            semestre = form.semestre.data
            grupo = form.grupo_estudiantes.data
            fecha_inscripcion = form.fecha_inscripcion.data
            estado = form.estado.data
            
            # ✅ CORREGIDO: buscar por semestre
            cursos_semestre = Curso.query.filter_by(semestre=semestre, activo=True).all()
            
            if not cursos_semestre:
                flash(f'No hay cursos activos para el semestre {semestre}', 'warning')
                return render_template('inscripciones/matricula_masiva.html', form=form)
            
            # Obtener estudiantes según criterio
            if grupo == 'todos':
                estudiantes = Estudiante.query.filter_by(activo=True).all()
            else:  # 'nuevos'
                # Estudiantes sin inscripciones en el semestre
                estudiantes_subquery = db.session.query(Inscripcion.estudiante_id)\
                    .join(Curso).filter(Curso.semestre == semestre).subquery()
                estudiantes = Estudiante.query.filter(
                    Estudiante.activo == True,
                    ~Estudiante.id.in_(estudiantes_subquery)
                ).all()
            
            if not estudiantes:
                flash('No hay estudiantes que cumplan con el criterio seleccionado', 'warning')
                return render_template('inscripciones/matricula_masiva.html', form=form)
            
            # Procesar matrícula masiva
            matriculas_creadas = 0
            matriculas_actualizadas = 0
            
            for estudiante in estudiantes:
                for curso in cursos_semestre:
                    # Verificar si ya existe la inscripción
                    inscripcion_existente = Inscripcion.query.filter_by(
                        estudiante_id=estudiante.id,
                        curso_id=curso.id
                    ).first()
                    
                    if inscripcion_existente:
                        # Actualizar estado si existe
                        inscripcion_existente.estado = estado
                        inscripcion_existente.fecha_inscripcion = fecha_inscripcion
                        matriculas_actualizadas += 1
                    else:
                        # Crear nueva inscripción
                        nueva_inscripcion = Inscripcion(
                            estudiante_id=estudiante.id,
                            curso_id=curso.id,
                            fecha_inscripcion=fecha_inscripcion,
                            estado=estado
                        )
                        db.session.add(nueva_inscripcion)
                        matriculas_creadas += 1
            
            db.session.commit()
            
            flash(
                f'✅ Matrícula masiva completada: '
                f'{matriculas_creadas} nuevas inscripciones, '
                f'{matriculas_actualizadas} actualizadas. '
                f'({len(estudiantes)} estudiantes × {len(cursos_semestre)} cursos)',
                'success'
            )
            return redirect(url_for('inscripciones.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error en matrícula masiva: {str(e)}', 'danger')
    
    # Para GET request, establecer fecha actual como default
    if request.method == 'GET':
        form.fecha_inscripcion.data = datetime.utcnow().date()
    
    return render_template('inscripciones/matricula_masiva.html', form=form)





@inscripciones_bp.route('/')
@login_required
def index():
    """Lista de todas las inscripciones"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Query base con joins para estudiante y curso
    inscripciones_query = Inscripcion.query.join(Estudiante).join(Curso)

    # Búsqueda
    search = request.args.get('search', '')
    if search:
        inscripciones_query = inscripciones_query.filter(
            db.or_(
                Estudiante.nombres.ilike(f'%{search}%'),
                Estudiante.apellidos.ilike(f'%{search}%'),
                Estudiante.codigo_estudiante.ilike(f'%{search}%'),
                Curso.nombre_curso.ilike(f'%{search}%'),
                Curso.codigo_curso.ilike(f'%{search}%')
            )
        )

    # Filtros
    estudiante_id = request.args.get('estudiante_id', type=int)
    curso_id = request.args.get('curso_id', type=int)
    estado = request.args.get('estado', '')
    
    if estudiante_id:
        inscripciones_query = inscripciones_query.filter(Inscripcion.estudiante_id == estudiante_id)
    if curso_id:
        inscripciones_query = inscripciones_query.filter(Inscripcion.curso_id == curso_id)
    if estado:
        inscripciones_query = inscripciones_query.filter(Inscripcion.estado == estado)

    inscripciones = inscripciones_query.order_by(
        Inscripcion.fecha_inscripcion.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    # Para los filtros
    estudiantes = Estudiante.query.filter_by(activo=True).order_by('apellidos').all()
    cursos = Curso.query.filter_by(activo=True).order_by('semestre', 'nombre_curso').all()

    return render_template('inscripciones/index.html',
                         inscripciones=inscripciones,
                         estudiantes=estudiantes,
                         cursos=cursos,
                         search=search,
                         estudiante_id=estudiante_id,
                         curso_id=curso_id,
                         estado=estado)

@inscripciones_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear nueva inscripción"""
    form = InscripcionForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la inscripción
            inscripcion_existente = Inscripcion.query.filter_by(
                estudiante_id=form.estudiante_id.data,
                curso_id=form.curso_id.data
            ).first()
            
            if inscripcion_existente:
                flash('El estudiante ya está inscrito en este curso', 'danger')
                return render_template('inscripciones/crear.html', form=form)
            
            # Crear nueva inscripción
            nueva_inscripcion = Inscripcion(
                estudiante_id=form.estudiante_id.data,
                curso_id=form.curso_id.data,
                fecha_inscripcion=form.fecha_inscripcion.data,
                estado=form.estado.data
            )
            
            db.session.add(nueva_inscripcion)
            db.session.commit()
            
            flash('Inscripción creada exitosamente', 'success')
            return redirect(url_for('inscripciones.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear inscripción: {str(e)}', 'danger')
    
    # Para GET request, establecer fecha actual como default
    if request.method == 'GET':
        form.fecha_inscripcion.data = datetime.utcnow().date()
        form.estado.data = 'ACTIVO'
    
    return render_template('inscripciones/crear.html', form=form)



@inscripciones_bp.route('/<int:inscripcion_id>')
@login_required
def detalle(inscripcion_id):
    """Detalle de una inscripción específica"""
    inscripcion = Inscripcion.query.get_or_404(inscripcion_id)
    
    # Obtener asistencias
    asistencias = (
        Asistencia.query
        .filter_by(inscripcion_id=inscripcion_id)
        .order_by(Asistencia.fecha.desc())
        .all()
    )
    
    # Obtener notas con join correcto
    notas = (
        Nota.query
        .filter_by(inscripcion_id=inscripcion_id)
        .join(Nota.evaluacion)
        .order_by(Evaluacion.nombre_evaluacion)
        .all()
    )
    
    # Calcular estadísticas
    total_asistencias = len(asistencias)
    asistencias_presente = sum(1 for a in asistencias if a.presente)
    porcentaje_asistencia = (asistencias_presente / total_asistencias * 100) if total_asistencias > 0 else 0
    
    promedio_notas = (
        db.session.query(db.func.avg(Nota.nota))
        .filter_by(inscripcion_id=inscripcion_id)
        .scalar()
        or 0
    )

    return render_template(
        'inscripciones/detalle.html',
        inscripcion=inscripcion,
        asistencias=asistencias,
        notas=notas,
        total_asistencias=total_asistencias,
        asistencias_presente=asistencias_presente,
        porcentaje_asistencia=porcentaje_asistencia,
        promedio_notas=promedio_notas
    )



@inscripciones_bp.route('/<int:inscripcion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(inscripcion_id):
    """Editar inscripción existente"""
    inscripcion = Inscripcion.query.get_or_404(inscripcion_id)
    form = InscripcionForm(obj=inscripcion)
    
    if form.validate_on_submit():
        try:
            # Verificar si ya existe la inscripción (excluyendo la actual)
            inscripcion_existente = Inscripcion.query.filter(
                Inscripcion.estudiante_id == form.estudiante_id.data,
                Inscripcion.curso_id == form.curso_id.data,
                Inscripcion.id != inscripcion_id
            ).first()
            
            if inscripcion_existente:
                flash('El estudiante ya está inscrito en este curso', 'danger')
                return render_template('inscripciones/editar.html', form=form, inscripcion=inscripcion)
            
            # Actualizar inscripción
            inscripcion.estudiante_id = form.estudiante_id.data
            inscripcion.curso_id = form.curso_id.data
            inscripcion.fecha_inscripcion = form.fecha_inscripcion.data
            inscripcion.estado = form.estado.data
            
            db.session.commit()
            
            flash('Inscripción actualizada exitosamente', 'success')
            return redirect(url_for('inscripciones.detalle', inscripcion_id=inscripcion.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar inscripción: {str(e)}', 'danger')
    
    return render_template('inscripciones/editar.html', form=form, inscripcion=inscripcion)

@inscripciones_bp.route('/<int:inscripcion_id>/eliminar', methods=['POST'])
@login_required
def eliminar(inscripcion_id):
    """Eliminar inscripción"""
    try:
        inscripcion = Inscripcion.query.get_or_404(inscripcion_id)
        
        # Verificar si tiene registros relacionados
        if inscripcion.asistencias:
            flash('No se puede eliminar la inscripción porque tiene asistencias relacionadas', 'danger')
            return redirect(url_for('inscripciones.detalle', inscripcion_id=inscripcion_id))
        
        if inscripcion.notas:
            flash('No se puede eliminar la inscripción porque tiene notas relacionadas', 'danger')
            return redirect(url_for('inscripciones.detalle', inscripcion_id=inscripcion_id))
        
        db.session.delete(inscripcion)
        db.session.commit()
        
        flash('Inscripción eliminada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar inscripción: {str(e)}', 'danger')
    
    return redirect(url_for('inscripciones.index'))

