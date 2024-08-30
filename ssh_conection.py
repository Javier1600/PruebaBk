import time
import os
from datetime import datetime
import pandas as pd
import paramiko
import socket
import ftplib

# Función para asegurar que los directorios FTP existen
def ensure_ftp_directories(ftp_server, ftp_username, ftp_password, directories):
    try:
        with ftplib.FTP(ftp_server) as ftp:  # Establece la sesión con el servidor FTP
            ftp.login(user=ftp_username, passwd=ftp_password)  # Envío de credenciales al servidor
            print(f"Conectado al servidor FTP: {ftp_server}")

            for directory in directories:
                try:
                    # Intentar cambiar al directorio para verificar si existe
                    ftp.cwd(directory)
                    print(f"El directorio '{directory}' ya existe en el servidor FTP.")
                except ftplib.error_perm:
                    # Si el directorio no existe, se crea
                    try:
                        ftp.mkd(directory)
                        print(f"Directorio '{directory}' creado en el servidor FTP.")
                        ftp.cwd(directory)
                    except Exception as e:
                        print(f"Error al crear el directorio '{directory}' en el servidor FTP: {e}")
    except ftplib.all_errors as e:
        print(f"Error al conectar al servidor FTP: {e}")

# Subir los archivos al servidor FTP directamente a la ruta especificada
def upload_files_to_ftp(local_folder, ftp_server, ftp_username, ftp_password, ftp_folder):
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login(user=ftp_username, passwd=ftp_password)
            print(f"Conectado al servidor FTP: {ftp_server}")

            # Subir archivos desde la carpeta local
            for filename in os.listdir(local_folder):
                local_file_path = os.path.join(local_folder, filename)
                with open(local_file_path, 'rb') as file:
                    remote_path = f"{ftp_folder}/{filename}"
                    ftp.storbinary(f'STOR {remote_path}', file)
                print(f"Archivo {filename} subido a {remote_path} en el servidor FTP.")
    except ftplib.all_errors as e:
        print(f"Error al subir archivos al servidor FTP: {e}")

# Leer el archivo Excel
df = pd.read_excel('C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\LLD_BPAC_AMERAFIN.xlsx', sheet_name="SIMED")

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Carpeta base local y FTP donde se guardarán los archivos
local_folder = f'C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\FTP\\BackUps\\BK_SIMED_{date}'
ftp_folder = f'/home/forti_mng/FTP/BackUps/BK_SIMED_{date}'

# Crear la carpeta local si no existe
if not os.path.exists(local_folder):
    os.makedirs(local_folder)

# Nombrar y abrir el archivo de salida de equipos inaccesibles
nAccess = os.path.join(local_folder, "Dispositivos_inaccesibles.txt")
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
            filename = os.path.join(local_folder, f"{client}_config_{date}.txt")

            # Escribir la salida en el archivo
            with open(filename, 'w', encoding="utf-8") as file:
                file.write(OUTPUT)

            print(f"\nBack up para {client}({hostname}) \nRuta al archivo: {filename}\n")
        except (TimeoutError, TypeError, paramiko.ssh_exception.SSHException,
                paramiko.ssh_exception.NoValidConnectionsError, socket.gaierror, Exception) as e:
            error_message = f"\nNo se pudo conectar a {client}({hostname}) : {str(e)}\n"
            errors_file.write(error_message)
            print(error_message)
        finally:
            # Asegurarse de que la conexión se cierra incluso si ocurre un error
            ssh_client.close()

# Validar y crear directorios en el servidor FTP
ftp_server = '190.110.195.146'  # Cambia esto por la dirección de tu servidor FTP
ftp_username = 'forti_mng'       # Cambia esto por tu nombre de usuario FTP
ftp_password = 'FW_BK$$2024'     # Cambia esto por tu contraseña FTP
ensure_ftp_directories(ftp_server, ftp_username, ftp_password, ['FTP', 'BackUps',f'BK_SIMED_{date}'])

# Llamar a la función para subir los archivos
upload_files_to_ftp(local_folder, ftp_server, ftp_username, ftp_password, ftp_folder)
