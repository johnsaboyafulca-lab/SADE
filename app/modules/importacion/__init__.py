# app/modules/importacion/__init__.py
from flask import Blueprint

importacion_bp = Blueprint('importacion', __name__, url_prefix='/importacion')

from . import routes