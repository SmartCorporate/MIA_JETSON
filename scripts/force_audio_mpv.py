import paramiko

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'

mpv_conf_content = """ao=alsa
audio-device=alsa/hw:0,0
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=host, username=user, password=password, timeout=10)

sftp = ssh.open_sftp()
try:
    sftp.mkdir('/home/mia/.config')
except:
    pass
try:
    sftp.mkdir('/home/mia/.config/mpv')
except:
    pass
with sftp.file('/home/mia/.config/mpv/mpv.conf', 'w') as f:
    f.write(mpv_conf_content)
sftp.close()

# Let's also set it globally in /etc/asound.conf just in case the app runs as root
stdin, stdout, stderr = ssh.exec_command("echo 'pcm.!default { type plug slave.pcm \"hw:0,0\" } ctl.!default { type hw card 0 }' | sudo -S tee /etc/asound.conf", get_pty=True)
stdin.write(password + '\n')
stdin.flush()
print("Sudo asound.conf:")
print(stdout.read().decode())

ssh.close()
