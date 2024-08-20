import paramiko
import ftplib
import time

def create_ssh_client(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, port, username, password)
        print(f"Conexión SSH establecida correctamente con {hostname}.")
    except paramiko.AuthenticationException:
        print(f"Error de autenticación en {hostname}. Verifica tu nombre de usuario y contraseña.")
        return None
    except paramiko.SSHException as sshException:
        print(f"Error al conectar a {hostname}: {sshException}")
        return None
    except Exception as e:
        print(f"Error al conectar a {hostname}: {e}")
        return None
    return ssh

def upload_firmware_via_ftp(ftp_server, ftp_username, ftp_password, ftp_file_path, local_file_path):
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login(user=ftp_username, passwd=ftp_password)
            print(f"Conectado al servidor FTP: {ftp_server}")

            with open(local_file_path, 'rb') as file:
                ftp.storbinary(f'STOR {ftp_file_path}', file)
            print(f"Archivo {local_file_path} subido a {ftp_file_path} en el servidor FTP.")
    except ftplib.all_errors as e:
        print(f"Error al subir el archivo al servidor FTP: {e}")

def upgrade_firmware_via_ftp(ssh, ftp_server, ftp_file_path):
    try:
        # Ejecutar el comando para actualizar el firmware desde FTP
        command = f'execute restore image ftp {ftp_file_path} {ftp_server}'
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
fortigate_ip = '190.12.62.187'  # Dirección IP del Fortigate
port = 22                       # Puerto SSH
username = 'admin'              # Usuario SSH
password = 'FW_sail$$2020'      # Contraseña SSH

# Configuración del servidor FTP
ftp_server = '190.110.195.146'
ftp_username = 'forti_mng'
ftp_password = 'FW_BK$$2024'
ftp_file_path = '/home/forti_mng/Images/fortigate_firmware_image.out'
local_file_path = 'fortigate_firmware_image.out'  # Ruta local del archivo de firmware

# Subir el archivo de firmware al servidor FTP
upload_firmware_via_ftp(ftp_server, ftp_username, ftp_password, ftp_file_path, local_file_path)

# Conectar al Fortigate y ejecutar la actualización de firmware
ssh = create_ssh_client(fortigate_ip, port, username, password)
if ssh:
    upgrade_firmware_via_ftp(ssh, ftp_server, ftp_file_path)
    ssh.close()
