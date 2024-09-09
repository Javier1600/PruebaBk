from datetime import datetime
import ftplib
import paramiko
import openpyxl
import os

def create_ssh_client(ipForti, port, username, password):
    # Definicion del Cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Intenta establecer la sesion SSH con el FW
        ssh.connect(ipForti, port, username, password)
        print(f"Conexión SSH establecida correctamente con {ipForti}.")
    except paramiko.AuthenticationException:  # Credenciales incorrectas
        print(f"Error de autenticación en {ipForti}. Verifica tu nombre de usuario y contraseña.")
        return None
    except paramiko.SSHException as sshException:  # No se logro establecer la sesion SSH
        print(f"Error al conectar a {ipForti}: {sshException}")
        return None
    except Exception as e:  # Excepcion generica
        print(f"Error al conectar a {ipForti}: {e}")
        return None
    return ssh

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

def ensure_local_directories(directories):
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directorio local '{directory}' creado.")
        else:
            print(f"El directorio local '{directory}' ya existe.")

def generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file):
    try:
        file_path = f'FTP/Bk_Forti/{backup_file}'
        # Construccion del comando para generar el BK
        command = f'execute backup config ftp {file_path} {ftp_server} {ftp_username} {ftp_password}'
        # Respuesta del comando
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        print(f"Backup generado y enviado a FTP: {ftp_server}")
        
        # Decodificacion de la salida obtenida y errores obtenidos
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if output:  # Impresion de la salida del comando
            print(f"Output: {output}")
        if errors:  # Impresion de errores si se produjeron
            print(f"Errors: {errors}")

    except Exception as e:  # Atrapa excepciones inesperadas
        print(f"Error al generar el backup: {e}")

def download_backup_from_ftp(ftp_server, ftp_username, ftp_password, remote_file, local_file):
    try:
        with ftplib.FTP(ftp_server) as ftp:  # Establece la sesion con el servidor FTP
            ftp.login(user=ftp_username, passwd=ftp_password)  # Envio de credenciales al servidor
            print(f"Conectado al servidor FTP: {ftp_server}")

            # Descarga del archivo bk del server FTP
            with open(local_file, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
            # Impresion de la ruta de descarga del archivo
            print(f"Archivo {remote_file} descargado como {local_file}")
    except ftplib.all_errors as e:
        # Impresion de errores inesperados
        print(f"Error al descargar el archivo desde el servidor FTP: {e}")

def get_firmware_version(ssh):
    try:
        # Construccion del comando
        command = 'get system status'
        # Envio y ejecucion del comando
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        # Decodificacion de la salida del comando
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:  # Impresion de errores
            print(f"Errores: {errors}")
        
        # Logica de obtencion de la version del firmware
        for line in output.splitlines():
            if "Version:" in line:  # Si la linea contiene la cadena
                version = line.split("Version:")[1].strip().split(',')[0]  # Obtencion del hostname
                print(f"Versión del firmware: {version}")
                return version
            
    except Exception as e:
        print(f"Error al obtener la versión del firmware: {e}")
        return None

def get_hostname(ssh):
    try:
        # Construccion del comando
        command = 'get system status'
        # Envio y ejecucion del comando
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Esperar a que el comando termine
        # Decodificacion de la salida del comando
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:  # Impresion de errores
            print(f"Errores: {errors}")
        # Logica de obtencion de la version del hostname
        for line in output.splitlines():
            if "Hostname:" in line:  # Si la linea contiene la cadena
                hostname = line.split("Hostname:")[1].strip()  # Obtencion del hostname
                print(f'Hostname: {hostname}')
                return hostname
            
    except Exception as e:
        print(f"Error al obtener el hostname: {e}")
        return None
    
def backup_fortigate_to_ftp_and_download(plan, client, ipForti, port, username, password, version, ftp_server, ftp_username, ftp_password):
    ssh = None
    local_file = None
    try:
        # Verificar y crear los directorios locales si es necesario
        ensure_local_directories(['FTP', 'FTP/Bk_Forti'])
        # Verificar y crear los directorios en el servidor FTP si es necesario
        ensure_ftp_directories(ftp_server, ftp_username, ftp_password, ['FTP', 'Bk_Forti'])
        
        # Establecimiendo de la sesion ssh
        ssh = create_ssh_client(ipForti, port, username, password)
        
        if ssh:
            # Obtencion de la version actual del Forti
            version_fw = get_firmware_version(ssh)
            # Validacion si la version actual es diferente a la almacenada en la base
            if version_fw != version:
                # Actualizacion de la version
                version = version_fw
            # Obtencion del hostname si es necesario
            if client == "":
                client = get_hostname(ssh)
        date = datetime.now().strftime('%Y-%m-%d')
        # Definicion de la ruta y nombre de archivo bk generado
        backup_file = f'{client}_{str.replace(version," ","_")}_{date}.conf'
        # Ruta del archivo local
        file_path = f'FTP/Bk_Forti/{backup_file}'

        if ssh:
            print(f"Iniciando backup para {client} ({ipForti})...")
            # Gernacion del archivo de BK
            generate_backup_to_ftp(ssh, ftp_server, ftp_username, ftp_password, backup_file)
            # Descarga del archivo desde el ftp
            download_backup_from_ftp(ftp_server, ftp_username, ftp_password, file_path, file_path)
    except Exception as e:
        print(f"Error en el proceso de backup: {e}")
    finally:
        if ssh:
            ssh.close()
        return local_file, version  # Retornar la ruta del archivo local y la versión

def read_firewall_data_from_excel(file_name):
    try:
        workbook = openpyxl.load_workbook(file_name)  # Lectura de la base de datos
        # Inicializacion de variables para almacenar los datos de los Forti
        sheet = workbook.active
        firewall_data = []

        for row in sheet.iter_rows(min_row=2):  # Inicio de la iteracion
            # Obtencion de los datos de cada forti
            plan, client, hostname, username, password, version, updated = [cell.value for cell in row[:7]]
            # Agregacion de los datos del forti al diccionario
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
        # Retorno variables
        return workbook, sheet, firewall_data
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return None, None, []

def main():
    excel_file = 'Forti_firmware_version.xlsx'
    # Llamo a la funcion read_firewall_data_from_excel para obtener los datos almacenados
    workbook, sheet, firewall_data_list = read_firewall_data_from_excel(excel_file)

    # Valores predeterminados del servidor FTP
    ftp_server = 'XXX.XXX.XXX.XXX'
    ftp_username = 'user'
    ftp_password = 'password'
    # Ciclo for para recorrer todas las entradas en el diccionario
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
