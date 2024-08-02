"******Python script to generate backups of cisco equipment******"
import time
import os
from datetime import datetime
import pandas as pd
import paramiko
import socket

# Leer el archivo Excel
df = pd.read_excel('C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\LLD_BPAC_AMERAFIN.xlsx',
                   sheet_name="YOBEL")

# Nombre de la carpeta donde se guardarán los archivos
OUTPUT_FOLDER = 'C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\BackUps\\BK_YOBEL'

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Crear la carpeta si no existe
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Nombrar y abrir el archivo de salida de equipos inaccesibles
nAccess = os.path.join(OUTPUT_FOLDER, "Dispositivos_inaccesibles.txt")
with open(nAccess, 'w', encoding="utf-8") as errors_file:

    # Extracción de datos de equipo
    for index, row in df.iterrows():
        client = row['PUNTO']
        hostname = row['IP CPE']
        username = row['USUARIO']
        password = row['CONTRASEÑA']
        PORT = 22
        enable_password = row['CONTRASEÑA']

        # Crear un cliente SSH
        ssh_client = paramiko.SSHClient()

        # Añadir la clave del servidor a la lista de hosts conocidos automáticamente
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Conectar al equipo
            ssh_client.connect(hostname, PORT, username, password)

            # Abrir una sesión SSH
            ssh_shell = ssh_client.invoke_shell()
            time.sleep(1)

            # Limpiar el buffer de bienvenida
            if ssh_shell.recv_ready():
                ssh_shell.recv(65535)

            # Enviar el comando 'enable'
            ssh_shell.send('enable\n')
            time.sleep(1)

            # Enviar la contraseña enable
            ssh_shell.send(f'{enable_password}\n')
            time.sleep(1)

            # Enviar el comando 'show running-config'
            ssh_shell.send('show running-config\n')
            ssh_shell.send('                     ')
            time.sleep(5)

            # Recibir la salida del comando hasta que no haya más datos
            OUTPUT = ""
            while True:
                if ssh_shell.recv_ready():
                    OUTPUT += ssh_shell.recv(65535).decode('utf-8')
                else:
                    break

            # Nombrar el archivo de salida basado en el hostname
            filename = os.path.join(OUTPUT_FOLDER, f"{client}_config_{date}.txt")

            # Escribir la salida en el archivo
            with open(filename, 'w', encoding="utf-8") as file:
                file.write(OUTPUT)

            print(f"\nBack up para {client}({hostname}) \nRuta al archivo: {filename}\n")
        except (TimeoutError, TypeError, paramiko.ssh_exception.SSHException,
                paramiko.ssh_exception.NoValidConnectionsError, socket.gaierror) as e:
            error_message = f"\nNo se pudo conectar a {client}({hostname}) : {str(e)}\n"
            errors_file.write(error_message)
            print(error_message)
        finally:
            # Asegurarse de que la conexión se cierra incluso si ocurre un error
            ssh_client.close()
            