import pandas as pd
from netmiko import ConnectHandler
from datetime import datetime
import paramiko
import socket

# Leer archivo de Excel que contiene detalles de inicio de sesión de los routers
df = pd.read_excel('detalles_router.xlsx')

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Crear un archivo de texto para registrar dispositivos no accesibles
log_filename = f'dispositivos_no_accesibles_{date}.txt'
log_file = open(log_filename, 'w',encoding="utf-8")

# Rutina a través de cada fila del archivo de Excel y conectarse a los routers uno por uno
for i, row in df.iterrows():
    device = {
        'device_type': 'cisco_ios',
        'ip': row['IP'],
        'username': row['username'],
        'password': row['password'],
        'secret': row['enable_password']
    }
    print(device)

    try:
        # Conectarse al router
        with ConnectHandler(**device) as conn:
            conn.enable()
            # Obtener la configuración en ejecución
            output = conn.send_command('show running-config')
            # Guardar la configuración en un archivo de texto
            filename = f'{row["hostname"]}_config_{date}.txt'
            with open(filename, 'w',encoding="utf-8") as f:
                f.write(output)
            print(f"Configuración de {row['Hostname']} guardada en {filename}")
    except (socket.timeout, paramiko.ssh_exception.SSHException) as e:
        error_message = f"No se pudo conectar a {row['IP']} ({row['Hostname']}): {str(e)}"
        print(error_message)
        # Registrar dispositivos no accesibles en el archivo de registro
        log_file.write(error_message + '\n')

# Cerrar el archivo de registro
log_file.close()

print("Proceso de extracción de configuraciones completado.")