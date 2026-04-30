import paramiko

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'
remote_path = '/home/mia/MIA_JETSON'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=host, username=user, password=password, timeout=10)

sftp = ssh.open_sftp()
sftp.put('scripts/test_voices.py', f'{remote_path}/scripts/test_voices.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command(f"cd {remote_path} && python3 scripts/test_voices.py")
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
