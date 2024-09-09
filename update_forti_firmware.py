import paramiko
import ftplib
import time

def create_ssh_client(ipForti, port, username, password):
    #Definicion del Cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        #Intenta establecer la sesion SSH con el FW
        ssh.connect(ipForti, port, username, password)
        print(f"Conexión SSH establecida correctamente con {ipForti}.")
    except paramiko.AuthenticationException: #Credenciales incorrectas
        print(f"Error de autenticación en {ipForti}. Verifica tu nombre de usuario y contraseña.")
        return None
    except paramiko.SSHException as sshException: #No se logro establecer la sesion SSH
        print(f"Error al conectar a {ipForti}: {sshException}")
        return None
    except Exception as e: #Escepcion generica
        print(f"Error al conectar a {ipForti}: {e}")
        return None
    return ssh

def upload_firmware_via_ftp(ftp_server, ftp_username, ftp_password, ftp_file_path, local_file_path):
    try:
        with ftplib.FTP(ftp_server) as ftp: #Establecimiento de sesion FTP
            ftp.login(user=ftp_username, passwd=ftp_password) #Envio de credenciales al servidor
            print(f"Conectado al servidor FTP: {ftp_server}")
            #Subida de la imagen al servidor FTP
            with open(local_file_path, 'rb') as file:
                ftp.storbinary(f'STOR {ftp_file_path}', file)
            print(f"Archivo {local_file_path} subido a {ftp_file_path} en el servidor FTP.")
    except ftplib.all_errors as e:
        print(f"Error al subir el archivo al servidor FTP: {e}")

def upgrade_firmware_via_ftp(ssh, ftp_server, ftp_file_path):
    try:
        # Ejecutar el comando para actualizar el firmware desde FTP
        command = f'execute restore image ftp {ftp_file_path} {ftp_server}'
        #Recepcion de respuestas del comando
        stdin, stdout, stderr = ssh.exec_command(command)
        time.sleep(1)
        stdin.write('y\n')  # Confirmar la actualización
        stdin.flush()

        while True:
            line = stdout.readline().strip()
            if line:
                print(line)
                if "Do you want to continue? (y/n)" in line:
                    stdin.write('y\n')  # Confirmar nuevamente si es necesario
                    stdin.flush()
            else:
                break

        stdout.channel.recv_exit_status()

        print("Actualización de firmware iniciada. El dispositivo se reiniciará.")
    except Exception as e:
        print(f"Error durante la actualización del firmware: {e}")

# Configuración del Fortigate
fortigate_ip = 'XXX.XXX.XXX.XXX'  # Dirección IP del Fortigate
port = 22                       # Puerto SSH
username = 'user'              # Usuario SSH
password = 'password'      # Contraseña SSH

# Configuración del servidor FTP
ftp_server = 'XXX.XXX.XXX.XXX'
ftp_username = 'user'
ftp_password = 'password'
ftp_file_path = '/home/forti_mng/FTP/Forti_Images/fortigate_firmware_image.out'
local_file_path = 'fortigate_firmware_image.out'  # Ruta local del archivo de firmware

# Subir el archivo de firmware al servidor FTP
upload_firmware_via_ftp(ftp_server, ftp_username, ftp_password, ftp_file_path, local_file_path)

# Conectar al Fortigate y ejecutar la actualización de firmware
ssh = create_ssh_client(fortigate_ip, port, username, password)
if ssh:
    upgrade_firmware_via_ftp(ssh, ftp_server, ftp_file_path)
    ssh.close()
