# app/modules/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from . import auth_bp
from .forms import LoginForm
from app.models import Usuario

@auth_bp.route('/')
def index():
    """Ruta raíz del blueprint auth - redirige al login"""
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        if usuario and check_password_hash(usuario.password_hash, form.password.data):
            if usuario.activo:
                login_user(usuario)
                flash(f'Bienvenido {usuario.username}!', 'success')
                
                # Redirigir según el rol
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                # TODOS los roles van al dashboard
                return redirect(url_for('dashboard.index'))
            else:
                flash('Cuenta desactivada. Contacte al administrador.', 'danger')
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))