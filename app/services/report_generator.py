import os
import json
from datetime import datetime
from flask import render_template
from app.models import Estudiante, SeguimientoRiesgo, Curso, Inscripcion, Nota, Asistencia
from app.extensions import db

class ReportGenerator:
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(__file__), '../static/reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generar_reporte_riesgo_individual(self, estudiante_id, semestre=None):
        """Genera reporte individual de riesgo para un estudiante"""
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        
        if not semestre:
            from app.modules.admin.routes import obtener_semestre_actual
            semestre = obtener_semestre_actual()
        
        # Obtener seguimiento de riesgo más reciente
        seguimiento = SeguimientoRiesgo.query.filter_by(
            estudiante_id=estudiante_id,
            semestre=semestre
        ).order_by(SeguimientoRiesgo.fecha_evaluacion.desc()).first()
        
        # Obtener cursos del semestre
        cursos = Curso.query.join(Inscripcion).filter(
            Inscripcion.estudiante_id == estudiante_id,
            Curso.semestre == semestre
        ).all()
        
        # Obtener notas y asistencias
        datos_cursos = []
        for curso in cursos:
            # Promedio de notas del curso
            promedio_query = db.session.query(db.func.avg(Nota.nota)).join(
                Inscripcion
            ).filter(
                Inscripcion.estudiante_id == estudiante_id,
                Inscripcion.curso_id == curso.id
            ).scalar()
            
            # Asistencia del curso
            asistencia_query = db.session.query(
                db.func.count(Asistencia.id),
                db.func.sum(db.cast(Asistencia.presente, db.Integer))
            ).join(Inscripcion).filter(
                Inscripcion.estudiante_id == estudiante_id,
                Inscripcion.curso_id == curso.id
            ).first()
            
            total_clases = asistencia_query[0] or 0
            asistencias = asistencia_query[1] or 0
            porcentaje_asistencia = (asistencias / total_clases * 100) if total_clases > 0 else 0
            
            datos_cursos.append({
                'curso': curso,
                'promedio': round(promedio_query, 2) if promedio_query else 'Sin notas',
                'asistencia': round(porcentaje_asistencia, 1),
                'total_clases': total_clases
            })
        
        # Renderizar template HTML
        html_content = render_template(
            'reportes/individual_riesgo.html',
            estudiante=estudiante,
            seguimiento=seguimiento,
            cursos=datos_cursos,
            semestre=semestre,
            fecha_generacion=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        return {
            'html': html_content,
            'estudiante': estudiante,
            'seguimiento': seguimiento,
            'datos_cursos': datos_cursos
        }
    
    def generar_reporte_riesgo_general(self, semestre=None, categoria_filtro=None):
        """Genera reporte general de riesgo para todos los estudiantes"""
        if not semestre:
            from app.modules.admin.routes import obtener_semestre_actual
            semestre = obtener_semestre_actual()
        
        # Obtener estudiantes en riesgo
        query = db.session.query(Estudiante, SeguimientoRiesgo).join(
            SeguimientoRiesgo, Estudiante.id == SeguimientoRiesgo.estudiante_id
        ).filter(
            SeguimientoRiesgo.semestre == semestre,
            Estudiante.activo == True
        )
        
        if categoria_filtro and categoria_filtro != 'TODOS':
            query = query.filter(SeguimientoRiesgo.categoria_riesgo == categoria_filtro)
        
        estudiantes_riesgo = query.order_by(
            SeguimientoRiesgo.puntaje_riesgo.desc()
        ).all()
        
        # Estadísticas
        total_estudiantes = Estudiante.query.filter_by(activo=True).count()
        total_riesgo = len(estudiantes_riesgo)
        
        # Conteo por categoría
        categorias_count = db.session.query(
            SeguimientoRiesgo.categoria_riesgo,
            db.func.count(SeguimientoRiesgo.id)
        ).filter(
            SeguimientoRiesgo.semestre == semestre
        ).group_by(SeguimientoRiesgo.categoria_riesgo).all()
        
        estadisticas = {
            'total_estudiantes': total_estudiantes,
            'total_riesgo': total_riesgo,
            'porcentaje_riesgo': (total_riesgo / total_estudiantes * 100) if total_estudiantes > 0 else 0,
            'categorias': dict(categorias_count)
        }
        
        html_content = render_template(
            'reportes/general_riesgo.html',
            estudiantes_riesgo=estudiantes_riesgo,
            estadisticas=estadisticas,
            semestre=semestre,
            categoria_filtro=categoria_filtro,
            fecha_generacion=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        return {
            'html': html_content,
            'estadisticas': estadisticas,
            'estudiantes_riesgo': estudiantes_riesgo
        }