# app/modules/estudiantes/__init__.py
from flask import Blueprint

estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

from . import routes
from . import forms  # ← AÑADIR ESTA LÍNEA