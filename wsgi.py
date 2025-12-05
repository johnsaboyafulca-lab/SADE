# wsgi.py
import sys
import os

# Añade el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Crear la aplicación Flask
app = create_app(config_name="production")

# Esto es necesario para gunicorn
application = app

if __name__ == "__main__":
    # Solo para desarrollo local
    app.run(debug=True)
