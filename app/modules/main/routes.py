# app/modules/main/routes.py
from flask import redirect, url_for
from . import main_bp

@main_bp.route('/')
def index():
    """Ruta raíz principal - redirige al login"""
    return redirect(url_for('auth.login'))