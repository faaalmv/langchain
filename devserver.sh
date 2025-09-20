#!/bin/sh
source .venv/bin/activate
# Corregido: Se eliminó la variable $PORT no definida y se reestructuró el comando
# para usar el modo de depuración correctamente. La aplicación se ejecutará en el puerto 8080.
python -m flask --app app run --port 8080 --debug
