# app/modules/admin/routes.py
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import admin_bp
from app.models import Usuario
from app.extensions import db
import json
import os
import re
from datetime import datetime

# OBTENER SEMESTRE ACTUAL DINÁMICAMENTE
def obtener_semestre_actual():
    """Calcula el semestre actual basado en la fecha"""
    ahora = datetime.now()
    año = ahora.year
    mes = ahora.month
    
    # Lógica para determinar el semestre:
    # Enero-Junio: Semestre 1 (2025-1)
    # Julio-Diciembre: Semestre 2 (2025-2)
    semestre = 1 if 1 <= mes <= 6 else 2
    return f"{año}-{semestre}"

# Configuración por defecto del sistema - CON SEMESTRE DINÁMICO
CONFIG_DEFAULT = {
    'umbral_amarillo': 0.4,
    'umbral_rojo': 0.7,
    'peso_rendimiento': 0.4,
    'peso_asistencia': 0.3,
    'peso_distribucion': 0.3,
    'semestre_actual': obtener_semestre_actual(),  # ¡DINÁMICO!
    'nota_minima_aprobatoria': 12.0,
    'porcentaje_asistencia_minimo': 70.0
}

def guardar_configuracion(config):
    """Guardar configuración en archivo"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_sistema.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("✅ Configuración guardada exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False

def cargar_configuracion():
    """Cargar configuración desde archivo o usar valores por defecto"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_sistema.json')
        print(f"📁 Buscando configuración en: {config_path}")
        
        if os.path.exists(config_path):
            print("✅ Archivo de configuración encontrado")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_cargada = json.load(f)
            
            print(f"🔍 Configuración cargada: {list(config_cargada.keys())}")
            
            # FORZAR MIGRACIÓN SI FALTAN CAMPOS NUEVOS
            necesita_migracion = (
                'peso_distribucion' not in config_cargada or 
                'peso_progreso' in config_cargada or 
                'peso_historial' in config_cargada
            )
            
            if necesita_migracion:
                print("🔄 Migrando configuración a nueva estructura...")
                
                # Crear configuración nueva basada en DEFAULT
                config_migrada = CONFIG_DEFAULT.copy()
                
                # Migrar valores personalizados si existen
                if 'umbral_amarillo' in config_cargada:
                    config_migrada['umbral_amarillo'] = config_cargada['umbral_amarillo']
                if 'umbral_rojo' in config_cargada:
                    config_migrada['umbral_rojo'] = config_cargada['umbral_rojo']
                if 'semestre_actual' in config_cargada:
                    config_migrada['semestre_actual'] = config_cargada['semestre_actual']
                if 'nota_minima_aprobatoria' in config_cargada:
                    config_migrada['nota_minima_aprobatoria'] = config_cargada['nota_minima_aprobatoria']
                if 'porcentaje_asistencia_minimo' in config_cargada:
                    config_migrada['porcentaje_asistencia_minimo'] = config_cargada['porcentaje_asistencia_minimo']
                
                # Guardar configuración migrada
                guardar_configuracion(config_migrada)
                print("✅ Migración completada")
                return config_migrada
            
            print("✅ Usando configuración actual")
            return config_cargada
        else:
            print("📝 No existe archivo de configuración, usando valores por defecto")
            # Crear archivo con valores por defecto
            guardar_configuracion(CONFIG_DEFAULT)
            return CONFIG_DEFAULT
            
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
    
    # Si hay error, usar valores por defecto
    print("🔄 Usando configuración por defecto")
    return CONFIG_DEFAULT

@admin_bp.route('/')
@login_required
def index():
    """Panel de administración principal"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard.index'))
    
    config = cargar_configuracion()
    print(f"🎯 Configuración final: {config}")
    print(f"📅 Semestre actual: {config['semestre_actual']}")
    
    stats = {
        'total_usuarios': Usuario.query.count(),
        'usuarios_activos': Usuario.query.filter_by(activo=True).count(),
        'administradores': Usuario.query.filter_by(rol='administrador').count()
    }
    
    return render_template('admin/index.html', config=config, stats=stats)

@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    """Configuración del sistema"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard.index'))
    
    config = cargar_configuracion()
    
    if request.method == 'POST':
        try:
            # CONFIGURACIÓN ACTUALIZADA - Solo 3 factores
            nueva_config = {
                'umbral_amarillo': float(request.form.get('umbral_amarillo', 0.4)),
                'umbral_rojo': float(request.form.get('umbral_rojo', 0.7)),
                'peso_rendimiento': float(request.form.get('peso_rendimiento', 0.4)),
                'peso_asistencia': float(request.form.get('peso_asistencia', 0.3)),
                'peso_distribucion': float(request.form.get('peso_distribucion', 0.3)),
                'semestre_actual': request.form.get('semestre_actual', obtener_semestre_actual()),
                'nota_minima_aprobatoria': float(request.form.get('nota_minima_aprobatoria', 12.0)),
                'porcentaje_asistencia_minimo': float(request.form.get('porcentaje_asistencia_minimo', 70.0))
            }
            
            # VALIDACIÓN ACTUALIZADA - Solo 3 factores
            total_pesos = (nueva_config['peso_rendimiento'] + 
                          nueva_config['peso_asistencia'] + 
                          nueva_config['peso_distribucion'])
            
            if abs(total_pesos - 1.0) > 0.01:
                flash('Los pesos de los factores deben sumar exactamente 1.0', 'danger')
            else:
                guardar_configuracion(nueva_config)
                flash('Configuración actualizada exitosamente', 'success')
                
        except ValueError as e:
            flash('Error en los valores ingresados. Verifique que sean números válidos.', 'danger')
        except Exception as e:
            flash(f'Error al guardar la configuración: {str(e)}', 'danger')
        
        return redirect(url_for('admin.configuracion'))
    
    return render_template('admin/configuracion.html', config=config)

@admin_bp.route('/cambiar-semestre', methods=['POST'])
@login_required
def cambiar_semestre():
    """Cambiar solo el semestre actual"""
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        nuevo_semestre = request.form.get('semestre')
        
        if not nuevo_semestre:
            flash('El semestre no puede estar vacío', 'danger')
            return redirect(url_for('admin.configuracion'))
        
        # Validar formato de semestre (YYYY-N)
        if not re.match(r'^\d{4}-[12]$', nuevo_semestre):
            flash('Formato de semestre inválido. Use: AÑO-SEMESTRE (ej: 2025-1, 2025-2)', 'danger')
            return redirect(url_for('admin.configuracion'))
        
        # Cargar configuración actual
        config = cargar_configuracion()
        
        # Actualizar solo el semestre
        config['semestre_actual'] = nuevo_semestre
        
        # Guardar configuración actualizada
        guardar_configuracion(config)
        
        flash(f'Semestre cambiado exitosamente a {nuevo_semestre}', 'success')
        
    except Exception as e:
        flash(f'Error al cambiar semestre: {str(e)}', 'danger')
    
    return redirect(url_for('admin.configuracion'))

@admin_bp.route('/usuarios')
@login_required
def usuarios():
    """Gestión de usuarios del sistema"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/crear', methods=['POST'])
@login_required
def crear_usuario():
    """Crear nuevo usuario"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para esta acción', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        rol = request.form.get('rol', 'docente')
        
        # Validaciones
        if not all([username, email, password, confirm_password]):
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('admin.usuarios'))
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('admin.usuarios'))
            
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return redirect(url_for('admin.usuarios'))
            
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('admin.usuarios'))
        
        # Crear usuario
        nuevo_usuario = Usuario(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            rol=rol,
            activo=True
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario creado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:usuario_id>/toggle', methods=['POST'])
@login_required
def toggle_usuario(usuario_id):
    """Activar/desactivar usuario"""
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # No permitir desactivarse a sí mismo
        if usuario.id == current_user.id:
            return jsonify({'error': 'No puede cambiar su propio estado'}), 400
            
        usuario.activo = not usuario.activo
        db.session.commit()
        
        return jsonify({
            'success': True,
            'nuevo_estado': 'Activo' if usuario.activo else 'Inactivo',
            'message': f'Usuario {"activado" if usuario.activo else "desactivado"} exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/usuarios/<int:usuario_id>/cambiar-rol', methods=['POST'])
@login_required
def cambiar_rol_usuario(usuario_id):
    """Cambiar rol de usuario"""
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        nuevo_rol = data.get('rol')
        
        if nuevo_rol not in ['administrador', 'coordinador', 'docente']:
            return jsonify({'error': 'Rol inválido'}), 400
            
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # No permitir cambiar el propio rol
        if usuario.id == current_user.id:
            return jsonify({'error': 'No puede cambiar su propio rol'}), 400
            
        usuario.rol = nuevo_rol
        db.session.commit()
        
        return jsonify({
            'success': True,
            'nuevo_rol': nuevo_rol,
            'message': f'Rol cambiado a {nuevo_rol} exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    """Eliminar usuario"""
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # No permitir eliminarse a sí mismo
        if usuario.id == current_user.id:
            return jsonify({'error': 'No puede eliminarse a sí mismo'}), 400
            
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/backup')
@login_required
def backup():
    """Panel de backup y restauración"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return render_template('admin/backup.html')

@admin_bp.route('/logs')
@login_required
def logs():
    """Visualización de logs del sistema"""
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard.index'))
    
    logs_sistema = [
        {'fecha': '2024-10-02 10:30:00', 'nivel': 'INFO', 'mensaje': 'Sistema iniciado correctamente'},
        {'fecha': '2024-10-02 10:35:00', 'nivel': 'INFO', 'mensaje': 'Cálculo de riesgo ejecutado para 5 estudiantes'},
        {'fecha': '2024-10-02 11:00:00', 'nivel': 'WARNING', 'mensaje': 'Estudiante 2024EST001 detectado en alerta roja'},
    ]
    
    return render_template('admin/logs.html', logs=logs_sistema)