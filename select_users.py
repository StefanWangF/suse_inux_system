import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_sudo_user(ssh, username):
    command = f"sudo -lU {username}"
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    return "NOPASSWD: ALL" in output

def execute_script(ip):
    try:
        #/root/.ssh/authorized_keys
        client_ssh = paramiko.SSHClient()
        client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_ssh.connect(hostname=ip, port=22, timeout= 10)
    except Exception as e:    
        print(ip)
    else:
        _, users, _ = client_ssh.exec_command("awk -F: '$3>=1000{print $1}' /etc/passwd")
        users = users.read().decode().split("\n")[:-1]
        for username in users:
            if check_sudo_user(client_ssh, username):
                with open('/stefan/serverName.txt', 'a') as f:
                    f.write(f'{ip}\t\t{username}\t\t sudo\n')
            else:
                with open('/stefan/serverName.txt', 'a') as f:
                    f.write(f'{ip}\t\t{username}\n')


with open("ip_address.txt", "r") as f:
    content_list = f.readlines()

executor = ThreadPoolExecutor(max_workers=20)

tasks = []

for i, content in enumerate(content_list):
    task = executor.submit(execute_script, content.split("\n")[0])
    tasks.append(task)

for future in as_completed(tasks):
    pass

executor.shutdown()

print("全部执行完成")
