# crear_usuarios.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Usuario
from werkzeug.security import generate_password_hash

def crear_usuarios_iniciales():
    app = create_app()
    
    with app.app_context():
        print("👥 Creando usuarios iniciales...")
        
        # Verificar si ya existen usuarios
        if Usuario.query.first():
            print("⚠️  Ya existen usuarios en la base de datos.")
            respuesta = input("¿Deseas crear usuarios adicionales? (s/n): ")
            if respuesta.lower() != 's':
                print("❌ Operación cancelada.")
                return
        
        # Crear usuario Administrador
        admin = Usuario(
            username="admin",
            email="admin@sades.edu",
            password_hash=generate_password_hash("admin123"),
            rol="administrador",
            activo=True
        )
        
        # Crear usuario Coordinador
        coordinador = Usuario(
            username="coordinador",
            email="coordinador@sades.edu", 
            password_hash=generate_password_hash("coord123"),
            rol="coordinador",
            activo=True
        )
        
        # Crear usuario Docente
        docente = Usuario(
            username="docente",
            email="docente@sades.edu",
            password_hash=generate_password_hash("docente123"),
            rol="docente",
            activo=True
        )
        
        # Agregar a la sesión y guardar
        db.session.add(admin)
        db.session.add(coordinador)
        db.session.add(docente)
        db.session.commit()
        
        print("✅ Usuarios creados exitosamente!")
        print("\n🔑 CREDENCIALES DE ACCESO:")
        print("   👑 ADMINISTRADOR")
        print("      Usuario: admin")
        print("      Contraseña: admin123")
        print("      Email: admin@sades.edu")
        print("      Acceso: Completo a todo el sistema")
        
        print("\n   🛡️  COORDINADOR")
        print("      Usuario: coordinador") 
        print("      Contraseña: coord123")
        print("      Email: coordinador@sades.edu")
        print("      Acceso: Gestión de estudiantes y cursos")
        
        print("\n   📚 DOCENTE")
        print("      Usuario: docente")
        print("      Contraseña: docente123")
        print("      Email: docente@sades.edu")
        print("      Acceso: Registro de notas y asistencias")
        
        print(f"\n📊 Total de usuarios creados: {Usuario.query.count()}")

if __name__ == "__main__":
    crear_usuarios_iniciales()