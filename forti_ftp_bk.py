"""Python script to generate fortigate backup"""
# pylint: disable=locally-disabled, multiple-statements, fixme, line-too-long
import ftplib
import paramiko

def create_ssh_client(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, port, username, password)
        print("Conexión SSH establecida correctamente.")
    except paramiko.AuthenticationException:
        print("Error de autenticación. Verifica tu nombre de usuario y contraseña.")
        return None
    except paramiko.SSHException as sshException:
        print(f"Error al conectar a {hostname}: {sshException}")
        return None
    except Exception as e:
        print(f"Error al conectar a {hostname}: {e}")
        return None
    return ssh

def generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file):
    try:
        # Ejecutar el comando para generar el respaldo y enviarlo al servidor FTP
        command = f'execute backup config ftp {backup_file} {ftp_server} {ftp_username} {ftp_password}'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        print(f"Backup generado y enviado a FTP: {ftp_server}")
        
        # Leer y mostrar la salida del comando
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if output:
            print(f"Output: {output}")
        if errors:
            print(f"Errors: {errors}")

    except Exception as e:
        print(f"Error al generar el backup: {e}")

def download_backup_from_ftp(ftp_server, ftp_username, ftp_password, remote_file, local_file):
    try:
        # Conectar al servidor FTP
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login(user=ftp_username, passwd=ftp_password)
            print(f"Conectado al servidor FTP: {ftp_server}")

            # Descargar el archivo de respaldo
            with open(local_file, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
            print(f"Archivo {remote_file} descargado como {local_file}")
    except ftplib.all_errors as e:
        print(f"Error al descargar el archivo desde el servidor FTP: {e}")

def backup_fortigate_to_ftp_and_download(hostname, port, username, password, ftp_server, ftp_username, ftp_password, backup_file, local_file):
    ssh = None
    try:
        # Crear una conexión SSH
        ssh = create_ssh_client(hostname, port, username, password)
        
        if ssh:
            # Generar el respaldo y enviarlo al servidor FTP
            generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file)
            
            # Descargar el archivo de respaldo desde el servidor FTP
            download_backup_from_ftp(ftp_server, ftp_username, ftp_password, backup_file, local_file)
    except Exception as e:
        print(f"Error en el proceso de backup: {e}")
    finally:
        if ssh:
            # Cerrar la conexión SSH
            ssh.close()

# Configuración del dispositivo Fortigate y del servidor FTP
hostname = '190.12.62.187'      # Dirección IP del Fortigate
port = 22                     # Puerto SSH (por defecto es 22)
username = 'admin'            # Usuario SSH
password = 'FW_sail$$2020'         # Contraseña SSH

ftp_server = 'ftp.example.com' # Dirección del servidor FTP
ftp_username = 'ftp_user'     # Usuario FTP
ftp_password = 'ftp_pass'     # Contraseña FTP
backup_file = 'backup.conf'   # Nombre del archivo de respaldo en el servidor FTP
local_file = 'fortigate_backup.conf'  # Archivo local donde se guardará el respaldo

# Realizar el backup y descargarlo
backup_fortigate_to_ftp_and_download(hostname, port, username, password, ftp_server, ftp_username, ftp_password, backup_file, local_file)