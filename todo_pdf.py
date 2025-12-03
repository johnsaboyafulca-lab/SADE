import os
from fpdf import FPDF

# Configuración de la clase PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Estructura de Proyecto', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, body)

# Función para filtrar caracteres no soportados
def filtrar_caracteres_no_soportados(texto):
    return ''.join([char if ord(char) < 256 else '?' for char in texto])

# Función para verificar si un archivo es de texto
def es_archivo_texto(archivo):
    # Lista de extensiones de archivos que se consideran de texto
    extensiones_texto = ['.py', '.txt', '.md', '.html', '.css', '.js']
    # Filtrar archivos que no sean de texto (por ejemplo, .pyd, .exe, .dll)
    return any(archivo.lower().endswith(ext) for ext in extensiones_texto)

# Función para recorrer los archivos y generar el PDF
def copiar_archivos_y_generar_pdf(ruta_origen, pdf):
    for root, dirs, files in os.walk(ruta_origen):
        # Excluir carpetas __pycache__ y directorios como 'venv'
        dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'venv']
        
        # Excluir archivos README
        files = [f for f in files if f.lower() != 'readme' and not f.lower().startswith('readme.')]

        # Ruta relativa de la carpeta actual
        ruta_relativa = os.path.relpath(root, ruta_origen)
        pdf.chapter_title(ruta_relativa)

        for archivo in files:
            archivo_origen = os.path.join(root, archivo)

            # Verificar si el archivo es de texto antes de intentar leerlo
            if es_archivo_texto(archivo):
                pdf.chapter_title(archivo)
                try:
                    with open(archivo_origen, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    # Filtrar caracteres no soportados
                    contenido = filtrar_caracteres_no_soportados(contenido)
                    pdf.chapter_body(contenido)
                except Exception as e:
                    print(f"Error al leer el archivo {archivo_origen}: {e}")

# Función principal
def generar_pdf_proyecto(ruta_origen, ruta_destino_pdf):
    pdf = PDF()
    pdf.add_page()

    copiar_archivos_y_generar_pdf(ruta_origen, pdf)

    # Asegúrate de que la carpeta de destino exista
    destino_carpeta = os.path.dirname(ruta_destino_pdf)
    if not os.path.exists(destino_carpeta):
        os.makedirs(destino_carpeta)

    # Guardar el archivo PDF generado
    pdf.output(ruta_destino_pdf)
    print(f"PDF generado exitosamente en {ruta_destino_pdf}")

# Uso
ruta_origen = 'C:/Users/Nvidia/Desktop/SITEMA_SEGUIMIENTO_ESTUDIANTIL'  # Ruta de tu proyecto
ruta_destino_pdf = 'C:/Users/Nvidia/Desktop/SITEMA_SEGUIMIENTO_ESTUDIANTIL/copia_proyecto.pdf'  # Ruta para el PDF
generar_pdf_proyecto(ruta_origen, ruta_destino_pdf)
