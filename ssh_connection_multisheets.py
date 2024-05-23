"******Python script to generate backups of cisco equipment multisheets******"
import time
import os
from datetime import datetime
import pandas as pd
import paramiko

# Leer el archivo Excel
EXCEL_FILE = 'C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\LLD_CS.xlsx'
df = pd.ExcelFile(EXCEL_FILE)

# Obtener las hojas del Excel
sheet_names = df.sheet_names

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Carpeta base donde se guardarán los archivos de salida
BASE_OUTPUT_FOLDER = 'C:\\Users\\ernesto.andrade\\Desktop\\Prueba\\BackUps'

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
                