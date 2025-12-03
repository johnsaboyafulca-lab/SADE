# cambiar_a_rojo.py
import sys
import os

# Agregar el directorio raíz al path para que encuentre los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Estudiante

def cambiar_a_alerta_roja(codigo_estudiante):
    """Cambia un estudiante específico a estado ALERTA ROJA"""
    app = create_app()
    
    with app.app_context():
        print(f"🔴 CAMBIANDO {codigo_estudiante} A ALERTA ROJA...")
        
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
        
        # Datos para ALERTA ROJA
        notas_rojo = [3.0, 4.0, 2.5, 5.0]  # Promedio: 3.625
        porcentaje_asistencia = 0.20  # 20% de asistencia
        
        for inscripcion in estudiante.inscripciones:
            # 1. MODIFICAR NOTAS (muy bajas)
            print(f"   📚 Curso: {inscripcion.curso.nombre_curso}")
            for i, nota_obj in enumerate(inscripcion.notas):
                if i < len(notas_rojo):
                    nota_anterior = nota_obj.nota
                    nota_obj.nota = notas_rojo[i]
                    print(f"      📝 Nota {i+1}: {nota_anterior} → {notas_rojo[i]}")
            
            # 2. MODIFICAR ASISTENCIA (muy baja) - CORRECCIÓN: usar lista directamente
            asistencias = list(inscripcion.asistencias)  # Convertir a lista
            total_clases = len(asistencias)
            
            if total_clases > 0:
                asistencias_a_marcar = int(total_clases * porcentaje_asistencia)
                
                for j, asistencia in enumerate(asistencias):
                    asistencia.presente = (j < asistencias_a_marcar)
                
                print(f"      📅 Asistencia: {asistencias_a_marcar}/{total_clases} clases ({porcentaje_asistencia*100}%)")
        
        db.session.commit()
        
        print(f"\n✅ {estudiante.nombres} cambiado a ALERTA ROJA!")
        print("📊 DATOS APLICADOS:")
        print(f"   • Notas: {notas_rojo} (Promedio: {sum(notas_rojo)/len(notas_rojo):.1f})")
        print(f"   • Asistencia: {porcentaje_asistencia*100}%")
        print(f"   • Cursos: Todos en riesgo")
        print("\n🚀 Ejecuta 'Calcular Riesgo' en el sistema para ver los cambios")

if __name__ == "__main__":
    # CAMBIA ESTE CÓDIGO POR EL DEL ESTUDIANTE QUE QUIERES MODIFICAR
    codigo_estudiante = "2025AMA001"  # ← CAMBIA AQUÍ
    cambiar_a_alerta_roja(codigo_estudiante)