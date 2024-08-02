"******Python script to generate backups of forti equipment******"
import os
from datetime import datetime
import time
import paramiko

# Obtener la fecha actual en formato YYYY-MM-DD
date = datetime.now().strftime('%Y-%m-%d')

# Carpeta base donde se guardafrán los archivos de salida

BASE_OUTPUT_FOLDER = 'BackUps Forti'
# Extracción de datos de equipo
client = {
        "ip": "190.12.62.187",
        "hostname": "FW_HOTEL_SAIL_PLAZA",
        "username": "admin",
        "password": "FW_sail$$2020",
        "PORT": 22
}
# Crear un cliente SSH
ssh_client = paramiko.SSHClient()

# Añadir la clave del servidor a la lista de hosts conocidos automáticamente
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Conectar al equipo
    ssh_client.connect(client["ip"], client["PORT"], client["username"], client["password"])

    # Abrir una sesión SSH
    ssh_shell = ssh_client.invoke_shell()
    time.sleep(1)

    # Limpiar el buffer de bienvenida
    if ssh_shell.recv_ready():
        ssh_shell.recv(65535)

        # Enviar el comando 'show running-config'
        ssh_shell.send('show\n')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        ssh_shell.send('                                                                 ')
        time.sleep(10)

        # Recibir la salida del comando hasta que no haya más datos
        OUTPUT = ""
        while True:
            if ssh_shell.recv_ready():
                OUTPUT += ssh_shell.recv(65535).decode('utf-8')
            else:
                break

        # Nombrar el archivo de salida basado en el hostname
        filename = os.path.join(BASE_OUTPUT_FOLDER, f"{client['hostname']}_config_{date}.txt")

        # Escribir la salida en el archivo
        with open(filename, 'w', encoding="utf-8") as file:
            file.write(OUTPUT)

        print(f"Back up para {client['hostname']}) \nRuta al archivo: {filename}")
except (TimeoutError, TypeError, paramiko.ssh_exception.SSHException,
                paramiko.ssh_exception.NoValidConnectionsError) as e:
    error_message = f"No se pudo conectar a {client['hostname']}) : {str(e)}\n"
    print(error_message)
finally:
    # Asegurarse de que la conexión se cierra incluso si ocurre un error
    ssh_client.close()
            