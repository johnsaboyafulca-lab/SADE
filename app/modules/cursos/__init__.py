# app/modules/cursos/__init__.py
from flask import Blueprint

cursos_bp = Blueprint('cursos', __name__, url_prefix='/cursos')

from . import routes
from . import forms  # ← AÑADIR ESTA LÍNEA