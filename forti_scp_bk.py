import paramiko
from scp import SCPClient

def create_ssh_client(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)
    return ssh

def generate_backup_fortigate(ssh, backup_file):
    try:
        # Ejecutar el comando para generar el respaldo
        stdin, stdout, stderr = ssh.exec_command(f'execute backup config flash {backup_file}')
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        print("Backup generado exitosamente en el Fortigate.")
    except Exception as e:
        print(f"Error al generar el backup: {e}")

def transfer_backup_fortigate_scp(ssh, remote_file, local_file):
    try:
        # Crear un cliente SCP
        with SCPClient(ssh.get_transport()) as scp:
            # Descargar el archivo de respaldo desde el Fortigate
            scp.get(remote_file, local_file)
        print(f"Backup transferido exitosamente a {local_file}")
    except Exception as e:
        print(f"Error al transferir el backup: {e}")

def backup_fortigate(hostname, port, username, password, backup_file, local_file):
    ssh = None
    try:
        # Crear una conexión SSH
        ssh = create_ssh_client(hostname, port, username, password)
        
        # Generar el respaldo en el Fortigate
        generate_backup_fortigate(ssh, backup_file)
        
        # Transferir el respaldo a la máquina local usando SCP
        remote_file = f'/flash/{backup_file}'
        transfer_backup_fortigate_scp(ssh, remote_file, local_file)
    except Exception as e:
        print(f"Error en el proceso de backup: {e}")
    finally:
        if ssh:
            # Cerrar la conexión SSH
            ssh.close()

# Configuración del dispositivo Fortigate
hostname = '190.12.62.187'  # Dirección IP del Fortigate
port = 22                 # Puerto SSH (por defecto es 22)
username = 'admin'        # Usuario SSH
password = 'FW_sail$$2020'     # Contraseña SSH
backup_file = 'backup.conf'  # Nombre del archivo de respaldo en el Fortigate
local_file = 'FW_HOTEL_SAIL_PLAZA_backup.conf'  # Archivo local donde se guardará el respaldo

# Realizar el backup
backup_fortigate(hostname, port, username, password, backup_file, local_file)