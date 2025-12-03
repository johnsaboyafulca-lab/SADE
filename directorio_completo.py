import os

# Definir la ruta raíz de la estructura de archivos proporcionada
root_path = r'./venv/Lib/site-packages'

# Función para recorrer y generar la estructura del árbol
def generate_file_tree(start_path, indent=""):
    tree = ""
    # Listar archivos y carpetas en el directorio
    try:
        for item in os.listdir(start_path):
            item_path = os.path.join(start_path, item)
            if os.path.isdir(item_path):
                tree += f"{indent}{item}/\n"  # Directorios
                tree += generate_file_tree(item_path, indent + "    ")  # Recursión para subdirectorios
            else:
                tree += f"{indent}{item}\n"  # Archivos
    except PermissionError:
        tree += f"{indent}Permission Denied\n"
    return tree

# Generar y mostrar el árbol de archivos
file_tree = generate_file_tree(root_path)
print(file_tree)
