# app/services/riesgo_calculator_v2.py
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FactorRiesgo:
    nombre: str
    valor: float
    peso: float  
    descripcion: str

class CalculatorRiesgoIntrasemestral:
    """
    NUEVA VERSión - Especializada en evaluación intrasemestral
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.umbral_amarillo = self.config.get('umbral_amarillo', 0.4)
        self.umbral_rojo = self.config.get('umbral_rojo', 0.7)
        
        # Usar pesos de configuración o valores por defecto
        self.peso_rendimiento = self.config.get('peso_rendimiento', 0.4)
        self.peso_asistencia = self.config.get('peso_asistencia', 0.3)
        self.peso_distribucion = self.config.get('peso_distribucion', 0.3)

    def calcular_riesgo_estudiante(self, estudiante_id: int, semestre: str, db) -> Dict:
        """Calcula riesgo usando solo factores del semestre actual"""
        try:
            factores = self._evaluar_factores_intrasemestrales(estudiante_id, semestre, db)
            puntaje_total = self._calcular_puntaje_total(factores)
            categoria = self._determinar_categoria(puntaje_total)
            
            return {
                'puntaje_riesgo': round(puntaje_total, 3),
                'categoria': categoria,
                'factores': [
                    {
                        'nombre': f.nombre,
                        'valor': round(f.valor, 3),
                        'peso': f.peso,
                        'descripcion': f.descripcion,
                        'contribucion': round(f.valor * f.peso, 3)
                    }
                    for f in factores
                ],
                'recomendaciones': self._generar_recomendaciones(factores, categoria)
            }
        except Exception as e:
            logging.error(f"Error calculando riesgo para estudiante {estudiante_id}: {e}")
            return {
                'puntaje_riesgo': 0.0,
                'categoria': 'SIN_RIESGO',
                'factores': [],
                'recomendaciones': ['Error en cálculo - Revisar datos']
            }

    def _evaluar_factores_intrasemestrales(self, estudiante_id: int, semestre: str, db) -> List[FactorRiesgo]:
        """Evalúa ÚNICAMENTE factores del semestre actual"""
        factores = []

        # Factor 1: Rendimiento académico ACTUAL
        factor_notas = self._evaluar_rendimiento_actual(estudiante_id, semestre, db)
        factores.append(factor_notas)

        # Factor 2: Asistencia ACTUAL  
        factor_asistencia = self._evaluar_asistencia_actual(estudiante_id, semestre, db)
        factores.append(factor_asistencia)

        # Factor 3: Distribución de riesgo entre cursos
        factor_distribucion = self._evaluar_distribucion_riesgo(estudiante_id, semestre, db)
        factores.append(factor_distribucion)

        return factores

    def _evaluar_rendimiento_actual(self, estudiante_id: int, semestre: str, db) -> FactorRiesgo:
        """Evalúa rendimiento BASADO EN DATOS ACTUALES del semestre"""
        query = """
        SELECT c.nombre_curso, AVG(n.nota) as promedio_curso, COUNT(n.id) as evaluaciones
        FROM cursos c
        JOIN inscripciones i ON c.id = i.curso_id
        LEFT JOIN notas n ON i.id = n.inscripcion_id
        WHERE i.estudiante_id = %s AND c.semestre = %s
        GROUP BY c.id, c.nombre_curso
        """
        
        try:
            cursos = db.execute(query, (estudiante_id, semestre)).fetchall()
            
            if not cursos:
                return FactorRiesgo("Rendimiento Actual", 0.5, self.peso_rendimiento, 
                                  "Sin cursos inscritos")

            # Calcular métricas
            total_notas = 0
            total_evaluaciones = 0
            cursos_con_datos = 0
            
            for curso in cursos:
                if curso['promedio_curso'] is not None:
                    total_notas += curso['promedio_curso'] * curso['evaluaciones']
                    total_evaluaciones += curso['evaluaciones']
                    cursos_con_datos += 1

            if total_evaluaciones == 0:
                return FactorRiesgo("Rendimiento Actual", 0.3, self.peso_rendimiento,
                                  f"Inscrito en {len(cursos)} cursos pero sin evaluaciones")

            promedio_general = total_notas / total_evaluaciones
            
            # FACTOR ADAPTATIVO: Considerar completitud
            evaluaciones_esperadas = len(cursos) * 3  # Asumiendo 3 eval por curso
            factor_completitud = min(total_evaluaciones / evaluaciones_esperadas, 1.0)
            
            # Escala de riesgo con ajuste por completitud
            if promedio_general >= 14:
                valor_base = 0.1
            elif promedio_general >= 12:
                valor_base = 0.3
            elif promedio_general >= 10:
                valor_base = 0.6
            else:
                valor_base = 0.9
                
            # Ajustar por completitud (si tiene pocas eval, riesgo reducido)
            if factor_completitud < 0.3:  # Menos del 30% de eval esperadas
                valor_ajustado = valor_base * 0.6
            elif factor_completitud < 0.6:
                valor_ajustado = valor_base * 0.8
            else:
                valor_ajustado = valor_base

            descripcion = (f"Promedio: {promedio_general:.1f} | "
                         f"{total_evaluaciones} evaluaciones | "
                         f"Completitud: {factor_completitud:.0%}")
            return FactorRiesgo("Rendimiento Actual", valor_ajustado, self.peso_rendimiento, descripcion)
            
        except Exception as e:
            logging.error(f"Error en evaluación de rendimiento: {e}")
            return FactorRiesgo("Rendimiento Actual", 0.5, self.peso_rendimiento, "Error en cálculo")

    def _evaluar_asistencia_actual(self, estudiante_id: int, semestre: str, db) -> FactorRiesgo:
        """Evalúa asistencia del semestre actual"""
        query = """
        SELECT 
            COUNT(*) as total_clases,
            SUM(CASE WHEN a.presente = TRUE THEN 1 ELSE 0 END) as asistencias,
            SUM(CASE WHEN a.justificado = TRUE THEN 1 ELSE 0 END) as justificadas
        FROM asistencias a
        JOIN inscripciones i ON a.inscripcion_id = i.id
        JOIN cursos c ON i.curso_id = c.id
        WHERE i.estudiante_id = %s AND c.semestre = %s
        """
        
        try:
            result = db.execute(query, (estudiante_id, semestre)).fetchone()
            
            if not result or result['total_clases'] == 0:
                return FactorRiesgo("Asistencia Actual", 0.2, self.peso_asistencia, 
                                  "Sin registros de asistencia")

            total_clases = result['total_clases']
            asistencias = result['asistencias']
            justificadas = result['justificadas']
            
            porcentaje_asistencia = (asistencias / total_clases) * 100
            
            # Calcular asistencia neta (sin justificadas)
            asistencia_neta = (asistencias - justificadas) / total_clases * 100 if total_clases > 0 else 0
            
            # Usar el peor escenario
            porcentaje_efectivo = min(porcentaje_asistencia, asistencia_neta)

            # Escala de riesgo adaptativa
            if porcentaje_efectivo >= 85:
                valor = 0.1
            elif porcentaje_efectivo >= 75:
                valor = 0.3
            elif porcentaje_efectivo >= 65:
                valor = 0.6
            else:
                valor = 0.9

            descripcion = f"Asistencia: {porcentaje_efectivo:.1f}% ({asistencias}/{total_clases} clases)"
            if justificadas > 0:
                descripcion += f" | {justificadas} justificadas"

            return FactorRiesgo("Asistencia Actual", valor, self.peso_asistencia, descripcion)
            
        except Exception as e:
            logging.error(f"Error en evaluación de asistencia: {e}")
            return FactorRiesgo("Asistencia Actual", 0.5, self.peso_asistencia, "Error en cálculo")

    def _evaluar_distribucion_riesgo(self, estudiante_id: int, semestre: str, db) -> FactorRiesgo:
        """Evalúa distribución de riesgo entre cursos"""
        query = """
        SELECT c.nombre_curso, AVG(n.nota) as promedio_curso, COUNT(n.id) as evaluaciones
        FROM cursos c
        JOIN inscripciones i ON c.id = i.curso_id
        LEFT JOIN notas n ON i.id = n.inscripcion_id
        WHERE i.estudiante_id = %s AND c.semestre = %s
        GROUP BY c.id, c.nombre_curso
        """
        
        try:
            cursos = db.execute(query, (estudiante_id, semestre)).fetchall()
            
            if not cursos:
                return FactorRiesgo("Distribución de Riesgo", 0.5, self.peso_distribucion, 
                                  "Sin cursos inscritos")

            cursos_en_riesgo = 0
            total_cursos = len(cursos)
            
            for curso in cursos:
                # Curso en riesgo si:
                if curso['promedio_curso'] is None:
                    cursos_en_riesgo += 0.3  # Riesgo potencial (sin eval)
                elif curso['promedio_curso'] < 12:
                    if curso['evaluaciones'] >= 2:  # Si tiene al menos 2 eval, confirmado
                        cursos_en_riesgo += 1
                    else:  # Pocas eval, riesgo moderado
                        cursos_en_riesgo += 0.7

            proporcion_riesgo = cursos_en_riesgo / total_cursos
            
            # Escala de riesgo por distribución
            if proporcion_riesgo == 0:
                valor = 0.1
            elif proporcion_riesgo <= 0.3:
                valor = 0.3
            elif proporcion_riesgo <= 0.6:
                valor = 0.6
            else:
                valor = 0.9

            descripcion = f"{cursos_en_riesgo:.1f} de {total_cursos} cursos requieren atención"
            return FactorRiesgo("Distribución de Riesgo", valor, self.peso_distribucion, descripcion)
            
        except Exception as e:
            logging.error(f"Error en evaluación de distribución: {e}")
            return FactorRiesgo("Distribución de Riesgo", 0.5, self.peso_distribucion, "Error en cálculo")

    def _calcular_puntaje_total(self, factores: List[FactorRiesgo]) -> float:
        return sum(factor.valor * factor.peso for factor in factores)

    def _determinar_categoria(self, puntaje: float) -> str:
        if puntaje < self.umbral_amarillo:
            return "SIN_RIESGO"
        elif puntaje < self.umbral_rojo:
            return "ALERTA_AMARILLA"
        else:
            return "ALERTA_ROJA"

    def _generar_recomendaciones(self, factores: List[FactorRiesgo], categoria: str) -> List[str]:
        recomendaciones = []
        
        if categoria == "SIN_RIESGO":
            recomendaciones.append("✅ Mantener el buen desempeño académico")
            return recomendaciones

        for factor in factores:
            if factor.valor > 0.5:
                if factor.nombre == "Rendimiento Actual":
                    recomendaciones.append("📚 Reforzamiento académico inmediato")
                    recomendaciones.append("⏰ Revisar técnicas de estudio y planificación")
                    
                elif factor.nombre == "Asistencia Actual":
                    recomendaciones.append("📅 Plan de mejora de asistencia con seguimiento semanal")
                    recomendaciones.append("🏫 Coordinar con bienestar estudiantil")
                    
                elif factor.nombre == "Distribución de Riesgo":
                    recomendaciones.append("🎯 Priorizar atención en cursos críticos")
                    recomendaciones.append("📊 Evaluar carga académica con coordinación")

        if categoria == "ALERTA_AMARILLA":
            recomendaciones.append("🔔 Seguimiento quincenal por coordinación académica")
            recomendaciones.append("🎯 Establecer metas de mejora específicas")
            
        elif categoria == "ALERTA_ROJA":
            recomendaciones.append("🚨 INTERVENCIÓN INMEDIATA - Reunión urgente requerida")
            recomendaciones.append("📞 Notificar a departamento estudiantil y familia")
            recomendaciones.append("⚖️ Evaluar posible ajuste de matrícula")

        return recomendaciones