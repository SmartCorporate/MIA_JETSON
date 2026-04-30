import paramiko

host = '10.0.0.9'
user = 'mia'
password = 'MIA_JETSON'

asoundrc_content = """pcm.!default {
    type plug
    slave.pcm "hw:0,0"
}

ctl.!default {
    type hw
    card 0
}
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=host, username=user, password=password, timeout=10)

sftp = ssh.open_sftp()
with sftp.file('/home/mia/.asoundrc', 'w') as f:
    f.write(asoundrc_content)
sftp.close()

# Let's test the audio by playing a sample beep
stdin, stdout, stderr = ssh.exec_command("speaker-test -t sine -f 440 -c 2 -l 1")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
