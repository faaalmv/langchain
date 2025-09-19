# Importar las funciones 'request' y 'jsonify' de Flask
from flask import Flask, render_template, request, jsonify

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Definir la ruta principal (la raíz del sitio)
@app.route('/')
def index():
    """
    Esta función se ejecuta cuando alguien visita la página principal.
    Renderiza y devuelve el archivo 'index.html' de la carpeta 'templates'.
    """
    return render_template('index.html')

# Definir la ruta para la API de investigación
@app.route('/api/investigate', methods=['POST'])
def investigate():
    """
    Este endpoint se activa cuando recibe una petición POST.
    Por ahora, solo confirma la recepción.
    """
    # Devolvemos una respuesta simple en formato JSON
    return jsonify({"status": "recibido"})

# Esto permite ejecutar la aplicación directamente con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True)