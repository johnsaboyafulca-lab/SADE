# app/modules/inscripciones/__init__.py
from flask import Blueprint

inscripciones_bp = Blueprint('inscripciones', __name__, url_prefix='/inscripciones')

from . import routes
from . import forms