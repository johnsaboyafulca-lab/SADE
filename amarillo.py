# cambiar_a_amarillo.py
import sys
import os

# Agregar el directorio raíz al path para que encuentre los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Estudiante

def cambiar_a_alerta_amarilla(codigo_estudiante):
    """Cambia un estudiante específico a estado ALERTA AMARILLA"""
    app = create_app()
    
    with app.app_context():
        print(f"🟡 CAMBIANDO {codigo_estudiante} A ALERTA AMARILLA...")
        
        # Buscar estudiante
        estudiante = Estudiante.query.filter_by(codigo_estudiante=codigo_estudiante).first()
        
        if not estudiante:
            print(f"❌ Estudiante {codigo_estudiante} no encontrado")
            print("📋 Estudiantes disponibles:")
            estudiantes = Estudiante.query.all()
            for est in estudiantes:
                print(f"   - {est.codigo_estudiante}: {est.nombres} {est.apellidos}")
            return
        
        print(f"👤 Modificando: {estudiante.nombres} {estudiante.apellidos}")
        
        # Datos para ALERTA AMARILLA
        notas_amarillo = [11.0, 10.5, 12.0, 11.5]  # Promedio: 11.25
        porcentaje_asistencia = 0.70  # 70% de asistencia
        
        for inscripcion in estudiante.inscripciones:
            # 1. MODIFICAR NOTAS (en el límite)
            print(f"   📚 Curso: {inscripcion.curso.nombre_curso}")
            for i, nota_obj in enumerate(inscripcion.notas):
                if i < len(notas_amarillo):
                    nota_anterior = nota_obj.nota
                    nota_obj.nota = notas_amarillo[i]
                    print(f"      📝 Nota {i+1}: {nota_anterior} → {notas_amarillo[i]}")
            
            # 2. MODIFICAR ASISTENCIA (regular) - CORRECCIÓN: usar lista directamente
            asistencias = list(inscripcion.asistencias)  # Convertir a lista
            total_clases = len(asistencias)
            
            if total_clases > 0:
                asistencias_a_marcar = int(total_clases * porcentaje_asistencia)
                
                for j, asistencia in enumerate(asistencias):
                    asistencia.presente = (j < asistencias_a_marcar)
                
                print(f"      📅 Asistencia: {asistencias_a_marcar}/{total_clases} clases ({porcentaje_asistencia*100}%)")
        
        db.session.commit()
        
        print(f"\n✅ {estudiante.nombres} cambiado a ALERTA AMARILLA!")
        print("📊 DATOS APLICADOS:")
        print(f"   • Notas: {notas_amarillo} (Promedio: {sum(notas_amarillo)/len(notas_amarillo):.1f})")
        print(f"   • Asistencia: {porcentaje_asistencia*100}%")
        print(f"   • Cursos: Algunos en riesgo")
        print("\n🚀 Ejecuta 'Calcular Riesgo' en el sistema para ver los cambios")

if __name__ == "__main__":
    # CAMBIA ESTE CÓDIGO POR EL DEL ESTUDIANTE QUE QUIERES MODIFICAR
    codigo_estudiante = "2025ROJ001"  # ← CAMBIA AQUÍ
    cambiar_a_alerta_amarilla(codigo_estudiante)