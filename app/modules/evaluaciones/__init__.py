# app/modules/evaluaciones/__init__.py
from flask import Blueprint

evaluaciones_bp = Blueprint('evaluaciones', __name__, url_prefix='/evaluaciones')

from . import routes
from . import forms