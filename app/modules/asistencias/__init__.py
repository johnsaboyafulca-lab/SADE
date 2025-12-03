# app/modules/asistencias/__init__.py
from flask import Blueprint

asistencias_bp = Blueprint('asistencias', __name__, url_prefix='/asistencias')

from . import routes
from . import forms