# reportes/routes.py - VERSIÓN COMPLETAMENTE CORREGIDA
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import os
import pdfkit
from datetime import datetime
import tempfile
import platform
from . import reportes_bp
from app.services.report_generator import ReportGenerator
from app.models import Reporte, Estudiante
from app.extensions import db

def get_pdf_config():
    """Configuración portable para pdfkit en diferentes sistemas"""
    try:
        # Detectar sistema operativo
        if platform.system() == "Windows":
            # Rutas comunes en Windows
            possible_paths = [
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
                r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
                'wkhtmltopdf.exe'  # Si está en el PATH
            ]
        else:
            # Linux/Mac
            possible_paths = [
                '/usr/bin/wkhtmltopdf',
                '/usr/local/bin/wkhtmltopdf',
                'wkhtmltopdf'
            ]
        
        # Buscar wkhtmltopdf
        for path in possible_paths:
            if os.path.exists(path):
                return pdfkit.configuration(wkhtmltopdf=path)
        
        # Si no se encuentra, usar None (asume que está en PATH)
        return pdfkit.configuration()
        
    except Exception as e:
        print(f"Advertencia en configuración PDF: {e}")
        return pdfkit.configuration()
    
    
@reportes_bp.route('/')
@login_required
def index():
    """Panel principal de reportes"""
    return render_template('reportes/index.html')


@reportes_bp.route('/individual')
@login_required
def individual():
    """Reporte individual de estudiantes"""
    estudiantes = Estudiante.query.filter_by(activo=True).all()
    return render_template('reportes/individual.html', estudiantes=estudiantes)

@reportes_bp.route('/generar-individual', methods=['POST'])
@login_required
def generar_individual():
    """Generar reporte individual - VERSIÓN CORREGIDA"""
    try:
        estudiante_id = request.form.get('estudiante_id')
        semestre = request.form.get('semestre')
        formato = request.form.get('formato', 'html')
        
        generator = ReportGenerator()
        resultado = generator.generar_reporte_riesgo_individual(estudiante_id, semestre)
        
        # Guardar en base de datos
        reporte = Reporte(
            tipo_reporte='INDIVIDUAL_RIESGO',
            titulo=f'Reporte de Riesgo - {resultado["estudiante"].nombres} {resultado["estudiante"].apellidos}',
            descripcion=f'Reporte individual de riesgo académico para el semestre {semestre}',
            parametros={
                'estudiante_id': estudiante_id,
                'semestre': semestre,
                'formato': formato
            },
            contenido=resultado['html'],
            usuario_id=current_user.id
        )
        db.session.add(reporte)
        db.session.commit()
        
        if formato == 'pdf':
            try:
                config = get_pdf_config()
                
                # Opciones optimizadas para PDF
                options = {
                    'page-size': 'A4',
                    'margin-top': '.5in',
                    'margin-right': '1.0in',
                    'margin-bottom': '1.0in',
                    'margin-left': '1.0in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None,
                    'dpi': 300,
                    'print-media-type': None
                }
                
                # CSS específico para PDF
                css_pdf = """
                <style>
                    body { 
                        font-family: 'Arial', sans-serif; 
                        font-size: 12px; 
                        line-height: 1.4;
                        color: #333;
                        margin: 0;
                        padding: 0;
                    }
                    .container { max-width: 100%; padding: 0; }
                    .header { 
                        text-align: center; 
                        border-bottom: 2px solid #2c3e50; 
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .header h1 { 
                        color: #2c3e50; 
                        margin: 0; 
                        font-size: 18px;
                    }
                    .header .subtitle {
                        color: #7f8c8d;
                        font-size: 14px;
                        margin: 5px 0;
                    }
                    .info-section { margin: 15px 0; }
                    .info-section h3 { 
                        color: #34495e; 
                        border-bottom: 1px solid #bdc3c7;
                        padding-bottom: 5px;
                        font-size: 14px;
                    }
                    .table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 10px 0;
                        font-size: 11px;
                    }
                    .table th {
                        background-color: #34495e;
                        color: white;
                        padding: 8px;
                        text-align: left;
                        border: 1px solid #2c3e50;
                    }
                    .table td {
                        padding: 6px 8px;
                        border: 1px solid #ddd;
                    }
                    .table tr:nth-child(even) {
                        background-color: #f8f9fa;
                    }
                    .alerta-roja { color: #dc3545; font-weight: bold; }
                    .alerta-amarilla { color: #ffc107; font-weight: bold; }
                    .sin-riesgo { color: #28a745; font-weight: bold; }
                    .footer {
                        margin-top: 30px;
                        text-align: center;
                        font-size: 10px;
                        color: #7f8c8d;
                        border-top: 1px solid #bdc3c7;
                        padding-top: 10px;
                    }
                    .no-print { display: none; }
                    .page-break { page-break-after: always; }
                    
                    .firmas-container {
    display: flex;
    justify-content: space-between;
    margin-top: 50px;
    page-break-inside: avoid;
}

.firma {
    text-align: center;
    width: 45%;
}

.firma-linea {
    border-top: 1px solid #000;
    margin: 40px 0 10px 0;
    width: 100%;
}

.firma-texto {
    font-size: 11px;
    margin-top: 5px;
}
                </style>
                """
                
                html_para_pdf = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{reporte.titulo}</title>
                    {css_pdf}
                </head>
                <body>
                    <div class="container">
                        {resultado['html']}
                    </div>
                </body>
                </html>
                """
                
                pdf = pdfkit.from_string(html_para_pdf, False, configuration=config, options=options)
                
                # Guardar PDF
                filename = f"reporte_individual_{estudiante_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                filepath = os.path.join(generator.reports_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(pdf)
                
                reporte.archivo_path = filepath
                db.session.commit()
                
                return send_file(filepath, as_attachment=True, download_name=filename)
                
            except Exception as pdf_error:
                flash(f'Error generando PDF: {str(pdf_error)}. Verifique que wkhtmltopdf esté instalado.', 'danger')
                # Fallback: ofrecer HTML
                return render_template('reportes/vista_previa.html', 
                                     contenido=resultado['html'],
                                     titulo=reporte.titulo,
                                     reporte_id=reporte.id,
                                     fecha_generacion=datetime.now().strftime('%d/%m/%Y a las %H:%M'))
        
        # Retornar HTML para vista previa
        return render_template('reportes/vista_previa.html', 
                             contenido=resultado['html'],
                             titulo=reporte.titulo,
                             reporte_id=reporte.id,
                             fecha_generacion=datetime.now().strftime('%d/%m/%Y a las %H:%M'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error generando reporte: {str(e)}', 'danger')
        return redirect(url_for('reportes.individual'))
    
    
@reportes_bp.route('/general')
@login_required
def general():
    """Reporte general de riesgo"""
    return render_template('reportes/general.html')

# Aplicar las mismas correcciones a generar_general()
@reportes_bp.route('/generar-general', methods=['POST'])
@login_required
def generar_general():
    """Generar reporte general - VERSIÓN CORREGIDA"""
    try:
        semestre = request.form.get('semestre')
        categoria_filtro = request.form.get('categoria_filtro', 'TODOS')
        formato = request.form.get('formato', 'html')
        
        generator = ReportGenerator()
        resultado = generator.generar_reporte_riesgo_general(semestre, categoria_filtro)
        
        # Guardar en base de datos
        reporte = Reporte(
            tipo_reporte='GENERAL_RIESGO',
            titulo=f'Reporte General de Riesgo - {semestre}',
            descripcion=f'Reporte general de riesgo académico. Filtro: {categoria_filtro}',
            parametros={
                'semestre': semestre,
                'categoria_filtro': categoria_filtro,
                'formato': formato
            },
            contenido=resultado['html'],
            usuario_id=current_user.id
        )
        db.session.add(reporte)
        db.session.commit()
        
        if formato == 'pdf':
            try:
                config = get_pdf_config()
                
                options = {
                    'page-size': 'A4',
                    'margin-top': '.5in',
                    'margin-right': '1.0in',
                    'margin-bottom': '1.0in',
                    'margin-left': '1.0in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None,
                    'dpi': 300,
                    'print-media-type': None
                }
                
                pdf = pdfkit.from_string(resultado['html'], False, configuration=config, options=options)
                
                filename = f"reporte_general_{semestre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                filepath = os.path.join(generator.reports_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(pdf)
                
                reporte.archivo_path = filepath
                db.session.commit()
                
                return send_file(filepath, as_attachment=True, download_name=filename)
                
            except Exception as pdf_error:
                flash(f'Error generando PDF: {str(pdf_error)}', 'danger')
                return render_template('reportes/vista_previa.html', 
                                     contenido=resultado['html'],
                                     titulo=reporte.titulo,
                                     reporte_id=reporte.id)
        
        return render_template('reportes/vista_previa.html', 
                             contenido=resultado['html'],
                             titulo=reporte.titulo,
                             reporte_id=reporte.id)
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error generando reporte: {str(e)}', 'danger')
        return redirect(url_for('reportes.general'))
    
    
    
@reportes_bp.route('/historial')
@login_required
def historial():
    """Historial de reportes generados"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    reportes = Reporte.query.filter_by(usuario_id=current_user.id).order_by(
        Reporte.fecha_generacion.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('reportes/historial.html', reportes=reportes)


@reportes_bp.route('/descargar/<int:reporte_id>')
@login_required
def descargar(reporte_id):
    """Descargar reporte generado anteriormente"""
    reporte = Reporte.query.get_or_404(reporte_id)
    
    if reporte.usuario_id != current_user.id and current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a este reporte', 'danger')
        return redirect(url_for('reportes.historial'))
    
    if reporte.archivo_path and os.path.exists(reporte.archivo_path):
        filename = f"reporte_{reporte.tipo_reporte}_{reporte.id}.pdf"
        return send_file(reporte.archivo_path, as_attachment=True, download_name=filename)
    else:
        flash('El archivo del reporte no está disponible', 'warning')
        return redirect(url_for('reportes.historial'))