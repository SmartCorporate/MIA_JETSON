import paramiko

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("wget -qO test.mp3 https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3 && mpv --no-video test.mp3")
print("MPV Output:")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
