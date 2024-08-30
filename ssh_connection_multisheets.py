import time
import os
from datetime import datetime
import pandas as pd
import paramiko
import ftplib

# Función para asegurar que los directorios FTP existen
def ensure_ftp_directories(ftp_server, ftp_username, ftp_password, directories):
    try:
        with ftplib.FTP(ftp_server) as ftp:  # Establece la sesión con el servidor FTP
            ftp.login(user=ftp_username, passwd=ftp_password)  # Envío de credenciales al servidor
            print(f"Conectado al servidor FTP: {ftp_server}\n")

            for directory in directories:
                try:
                    # Intentar cambiar al directorio para verificar si existe
                    ftp.cwd(directory)
                    print(f"El directorio '{directory}' ya existe en el servidor FTP.\n")
                except ftplib.error_perm:
                    # Si el directorio no existe, se crea
                    try:
                        # Se crea el directorio y se navega a su interior
                        parent_dir = os.path.dirname(directory)
                        if parent_dir:
                            ftp.cwd(parent_dir)
                        ftp.mkd(directory)
                        print(f"Directorio '{directory}' creado en el servidor FTP.\n")
                        ftp.cwd(directory)
                    except Exception as e:
                        print(f"Error al crear el directorio '{directory}' en el servidor FTP: {e}\n")
    except ftplib.all_errors as e:
        print(f"Error al conectar al servidor FTP: {e}\n")

# Función para subir archivos al servidor FTP
def upload_files_to_ftp(local_folder, ftp_server, ftp_username, ftp_password, ftp_folder):
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login(user=ftp_username, passwd=ftp_password)
            print(f"Conectado al servidor FTP: {ftp_server}")

            # Cambiar al directorio FTP deseado
            ftp.cwd(ftp_folder)

            # Subir archivos desde la carpeta local
            for filename in os.listdir(local_folder):
                local_file_path = os.path.join(local_folder, filename)
                with open(local_file_path, 'rb') as file:
                    ftp.storbinary(f'STOR {filename}', file)
                print(f"Archivo {filename} subido a {ftp_folder} en el servidor FTP.\n")
    except ftplib.all_errors as e:
        print(f"Error al subir archivos al servidor FTP: {e}\n")
# Leer el archivo Excel
EXCEL_FILE = 'LLD_CS.xlsx'
df = pd.ExcelFile(EXCEL_FILE)

# Obtener las hojas del Excel
sheet_names = df.sheet_names

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Carpeta base donde se guardarán los archivos de salida
BASE_OUTPUT_FOLDER = 'FTP/BackUps'

# Información del servidor FTP
ftp_server = '190.110.195.146'
ftp_username = 'forti_mng'
ftp_password = 'FW_BK$$2024'

ensure_ftp_directories(ftp_server, ftp_username, ftp_password, ['FTP', 'BackUps'])
# Iterar sobre cada hoja del Excel
for sheet_name in sheet_names:
    # Crear la carpeta correspondiente a la hoja si no existe
    output_folder = os.path.join(BASE_OUTPUT_FOLDER, f"{sheet_name}_{date}")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Leer los datos de la hoja específica
    df_sheet = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)

    # Nombrar y abrir el archivo de salida de equipos inaccesibles para la hoja
    nAccess = os.path.join(output_folder, f"{sheet_name}_Dispositivos_inaccesibles.txt")
    with open(nAccess, 'w', encoding="utf-8") as errors_file:

        # Iterar sobre los datos de cada fila
        for index, row in df_sheet.iterrows():
            client = str(int(row['CÓDIGO'])) + "_" + str(int(row['PLAN'])) + "_" + row['NOMBRE']
            hostname = row['IP WAN CPE / 30']
            username = row['USUARIO CPE']
            password = row['CONTRASEÑA CPE']
            PORT = 22
            enable_password = row['CONTRASEÑA CPE']

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
                filename = os.path.join(output_folder, f"{client}_config_{date}.txt")

                # Escribir la salida en el archivo
                with open(filename, 'w', encoding="utf-8") as file:
                    file.write(OUTPUT)

                print(f"Back up para {client}({hostname}) \nRuta al archivo: {filename}\n")
            except (TimeoutError, TypeError, ValueError, paramiko.ssh_exception.SSHException,
                    paramiko.ssh_exception.NoValidConnectionsError) as e:
                error_message = f"No se pudo conectar a {client}({hostname}) : {str(e)}\n"
                errors_file.write(error_message)
                print(error_message)
            finally:
                # Asegurarse de que la conexión se cierra incluso si ocurre un error
                ssh_client.close()

# Validar y crear directorios en el servidor FTP para cada hoja
for sheet_name in sheet_names:
    ftp_folder = f"/home/forti_mng/FTP/BackUps/BK_{sheet_name}_{date}"
    ensure_ftp_directories(ftp_server, ftp_username, ftp_password, [ftp_folder])

    # Subir los archivos de la carpeta local correspondiente al FTP
    local_folder = os.path.join(BASE_OUTPUT_FOLDER, f"{sheet_name}_{date}")
    upload_files_to_ftp(local_folder, ftp_server, ftp_username, ftp_password, ftp_folder)
