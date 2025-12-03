# app/modules/seguimiento/__init__.py
from flask import Blueprint

seguimiento_bp = Blueprint('seguimiento', __name__, url_prefix='/seguimiento')

from . import routes