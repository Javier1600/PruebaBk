from datetime import datetime
import ftplib
import paramiko
import openpyxl

def create_ssh_client(ipForti, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipForti, port, username, password)
        print(f"Conexión SSH establecida correctamente con {ipForti}.")
    except paramiko.AuthenticationException:
        print(f"Error de autenticación en {ipForti}. Verifica tu nombre de usuario y contraseña.")
        return None
    except paramiko.SSHException as sshException:
        print(f"Error al conectar a {ipForti}: {sshException}")
        return None
    except Exception as e:
        print(f"Error al conectar a {ipForti}: {e}")
        return None
    return ssh

def generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file):
    try:
        command = f'execute backup config ftp {backup_file} {ftp_server} {ftp_username} {ftp_password}'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        print(f"Backup generado y enviado a FTP: {ftp_server}")
        
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
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login(user=ftp_username, passwd=ftp_password)
            print(f"Conectado al servidor FTP: {ftp_server}")

            with open(local_file, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
            print(f"Archivo {remote_file} descargado como {local_file}")
    except ftplib.all_errors as e:
        print(f"Error al descargar el archivo desde el servidor FTP: {e}")

def get_firmware_version(ssh):
    try:
        command = 'get system status'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:
            print(f"Errores: {errors}")
            
        for line in output.splitlines():
            if "Version:" in line:
                version = line.split("Version:")[1].strip().split(',')[0]
                print(f"Versión del firmware: {version}")
                return version
            
    except Exception as e:
        print(f"Error al obtener la versión del firmware: {e}")
        return None

def get_hostname(ssh):
    try:
        command = 'get system status'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:
            print(f"Errores: {errors}")
        
        for line in output.splitlines():
            if "Hostname:" in line:
                hostname = line.split("Hostname:")[1].strip()
                print(f'Hostname: {hostname}')
                return hostname
            
    except Exception as e:
        print(f"Error al obtener el hostname: {e}")
        return None
    
def backup_fortigate_to_ftp_and_download(plan, client, ipForti, port, username, password, version, ftp_server, ftp_username, ftp_password):
    ssh = None
    local_file = None
    try:
        ssh = create_ssh_client(ipForti, port, username, password)
        
        if ssh:
            version_fw = get_firmware_version(ssh)
            if version_fw != version:
                version = version_fw
            if client == "":
                client = get_hostname(ssh)
        date = datetime.now().strftime('%Y-%m-%d')
        backup_file = f'{client}_{str.replace(version," ","_")}_{date}.conf'
        local_file = f'BackUps Forti/{backup_file}'

        if ssh:
            print(f"Iniciando backup para {client} ({ipForti})...")
            generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file)
            download_backup_from_ftp(ftp_server, ftp_username, ftp_password, backup_file, local_file)
    except Exception as e:
        print(f"Error en el proceso de backup: {e}")
    finally:
        if ssh:
            ssh.close()
        return local_file, version  # Retornar la ruta del archivo local y la versión

def read_firewall_data_from_excel(file_name):
    try:
        workbook = openpyxl.load_workbook(file_name)
        sheet = workbook.active
        firewall_data = []

        for row in sheet.iter_rows(min_row=2):
            plan, client, hostname, username, password, version, updated = [cell.value for cell in row[:7]]
            firewall_data.append({
                'row': row,
                'PLAN': plan,
                "HOSTNAME": client,
                "IP": hostname,
                "PORT": 22,
                "USER": username,
                "PASSWORD": password, 
                "VERSION": version,
                "UPDATED": updated
            })
        return workbook, sheet, firewall_data
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return None, None, []

def main():
    excel_file = 'Forti_firmware_version.xlsx'
    workbook, sheet, firewall_data_list = read_firewall_data_from_excel(excel_file)

    # Valores predeterminados del servidor FTP
    ftp_server = '190.110.195.146'
    ftp_username = 'forti_mng'
    ftp_password = 'FW_BK$$2024'

    for data in firewall_data_list:
        plan = data['PLAN']
        client = data['HOSTNAME']
        ipForti = data['IP']
        port = data['PORT']
        username = data['USER']
        password = data['PASSWORD']
        version = data['VERSION']
        updated = data['UPDATED']

        # Realizar backup y descargarlo
        local_file, version = backup_fortigate_to_ftp_and_download(plan, client, ipForti, port, username, password, version, ftp_server, ftp_username, ftp_password)

        # Actualizar el archivo Excel con la nueva información
        row = data['row']
        row[5].value = version  # Actualizar la versión
        row[6].value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Guardar la fecha y hora del backup

    # Guardar los cambios en el archivo Excel
    workbook.save(excel_file)
    print("Archivo Excel actualizado.")

if __name__ == "__main__":
    main()
