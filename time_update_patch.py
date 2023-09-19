import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time
import datetime as dtime
import time as sltime

def execute_script(ip, CICD):
    timestamp = dtime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        client_ssh = paramiko.SSHClient()
        client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_ssh.connect(hostname=ip, port=22, timeout=5)
    except Exception as e:
        file_error_time = dtime.datetime.now().strftime("%Y-%m-%d") 
        filename = f'/stefan/failed_log/ssh_error_{file_error_time}.log'
        with open(filename, 'a') as f:
            f.write(f'{timestamp} - SSH Connect failed {ip}: {str(e)}\n')
    else:
        if "CICD" == CICD:
            _, exports, _ = client_ssh.exec_command("sh /tmp/expox.sh")
            zypper_export = exports.read().decode()
        file_time = dtime.datetime.now().strftime("%Y-%m-%d")
        #search source
        _, lr, _ = client_ssh.exec_command('zypper lr')
        zypper_lr = lr.read().decode()
        #check patch list
        _, lp, _ = client_ssh.exec_command('zypper pchk')
        zypper_lp = lp.read().decode()
        #update patch
        _, update, _ = client_ssh.exec_command('zypper -n update')
        zypper_update = update.read().decode()
        #check system shuntdown
        filename = f'/stefan/log/{file_time}.log'
        with open(filename, 'a') as f:
            f.write(f'{timestamp}--{ip}\n--{zypper_lr}\n--{zypper_lp}\n--{zypper_update}\n')
        _, down, _ = client_ssh.exec_command('init 6')
        zypper_down = down.read().decode()
        print("shutdown server.....")
        #wait server restart set sleep time 8 minute
        sltime.sleep(180)
        timestamp = dtime.datetime.now().strftime("%Y-%m-%d %H:%M")
        file_time = dtime.datetime.now().strftime("%Y-%m-%d")
        try:
            client_ssh.connect(hostname=ip, port=22, timeout=5)
            _, uptimes, _ = client_ssh.exec_command('uptime')
            zypper_uptime = uptimes.read().decode()
            server_success = f'{ip} --- {timestamp} -- server update successful.restart server -- {zypper_uptime}\n '
            with open(f'/stefan/success_log/{file_time}.log', 'a') as f:
                f.write(server_success)
        except Exception as e:
            server_start_failed = f'{ip} --- {timestamp} -- server restat failed.Plase check through vcenter.\n'
            with open(f'/stefan/failed_log/{file_time}.log', 'a') as f:
                f.write(server_start_failed)

def is_time_in_range(time_range):
    # 获取当前日期和时间
    now = datetime.now()
    # 解析时间字符串，提取开始时间和结束时间的小时和分钟
    start_str, end_str = time_range.split("-")
    start_hour, start_minute = map(int, start_str.split(":"))
    end_hour, end_minute = map(int, end_str.split(":"))
    # 将时间字符串中的开始时间和结束时间转换为24小时制的时间表示
    start_time = time(start_hour, start_minute)
    end_time = time(end_hour, end_minute)
    # 判断时间范围是否跨越两天
    if end_time < start_time:
        if now.time() >= start_time or now.time() <= end_time:
            return True
    else:
        if start_time <= now.time() <= end_time:
            return True
    return False

with open("update_list.txt", "r") as f:
    content_list = f.readlines()

# 设置关键字列表
keywords = ["Axway"]

# 设置执行标记列表，初始为False
execution_flags = [False] * len(content_list)


# 创建线程池
executor = ThreadPoolExecutor(max_workers=20)  # 根据实际需求设置线程池大小

# 创建任务列表
tasks = []

# 循环检查时间节点并执行脚本，直到所有内容项都执行完毕
while not all(execution_flags):
    # 遍历内容列表
    for i, content in enumerate(content_list):
        # 如果内容项已经执行过，则跳过
        if execution_flags[i]:
            continue
        ip, current_keyword, time_range = content.split("\t")
        time_range, _, _,  _ = time_range.split(" ")
        if is_time_in_range(time_range):
            if any(keyword in current_keyword for keyword in keywords):
                # 执行任务
                print("正在执行有重启顺序的主机")
                execute_script(ip, current_keyword)
                execution_flags[i] = True 
                # 更新上一个关键字任务的完成状态
            else:
                # 执行任务
                print("并发执行无特殊要求的服务器")
                task = executor.submit(execute_script, ip, current_keyword)
                tasks.append(task)
                execution_flags[i] = True
        else:
            # 更新上一个关键字任务的完成状态
            pass

# 等待所有任务完成
for future in as_completed(tasks):
    # 获取结果（这里不需要结果，仅等待任务执行完成）
    pass

# 关闭线程池
executor.shutdown()

# 全部执行完成后退出
print("全部执行完成")
