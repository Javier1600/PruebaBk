import paramiko

command = "sh version"

# Update the next three lines with your
# server's information

host = "192.168.134.194"
username = "@1783211CORPcue"
password = "Gesti00n.&.PN3T"

client = paramiko.client.SSHClient()

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(host, username=username, password=password)

client.exec_command("enable")

client.exec_command(password)

_stdin, _stdout,_stderr = client.exec_command(command)

print(_stdout.read().decode())

client.close()
