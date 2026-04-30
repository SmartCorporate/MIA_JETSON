import paramiko

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("amixer -c 0")
print("Amixer output for Card 0:")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
