import subprocess
import os
import re
import time


def bye():
    input('\n按下回车键关闭窗口')
    exit(0)


def clear():
    os.system('cls')


def ping(to):
    out = str(subprocess.run(
        ['ping', to, '-n', '2', '-w', '200'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='gbk'
    ).stdout)
    en = re.search(r'time=([0-9]*)', out)
    zh = re.search(r'时间=([0-9]*)', out)
    if en:
        try:
            ms = en.group(1)
        except:
            ms = '>200'
    elif zh:
        try:
            ms = zh.group(1)
        except:
            ms = '>200'
    else:
        ms = '>200'
    return ms


if __name__ == '__main__':

    configs = []
    for filename in os.listdir('config/'):
        if filename.endswith('.ovpn') or filename.endswith('.conf'):
            configs.append(filename)

    if not configs:
        print('未在config目录下发现配置文件')
        bye()

    print('找到的配置文件:')
    for i in range(len(configs)):
        print("%d. %s" % (i + 1, configs[i]))

    print()
    while True:
        inp = input('请输入要连接的配置文件序号: ')
        config_index = int(inp)
        if re.match(r'^[0-9]*$', inp) and 1 <= config_index <= len(configs):
            break

    config = configs[config_index - 1]

    print('\n正在连接 %s\n' % config)

    proc = subprocess.Popen(
        ['bin/openvpn.exe', '--config', 'config/%s' % config, '--log', 'log.log', '--status', 'status.log'],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )

    while True:
        time.sleep(0.5)
        f = open('log.log', 'r', errors='ignore')
        log = f.read()
        f.close()
        if proc.poll():
            if 'There are no TAP-Windows adapters on this system.' in log:
                print('没有找到Tap网卡驱动，请先安装驱动')
            elif 'All TAP-Windows adapters on this system are currently in use.' in log:
                print('Tap网卡被占用，请检查任务管理器里是否有openvpn.exe')
            else:
                print('程序因未知错误而退出，错误信息请查看log.log')
            bye()
        if 'Initialization Sequence Completed' in log:
            index = log.find('Notified TAP-Windows driver to set a DHCP IP/netmask of ') + 56
            ip = re.match(r'^(.*)/.*', log[index:]).group(1)
            break

    host_ip = re.match(r'^([0-9]{0,3}\.[0-9]{0,3}\.[0-9]{0,3}\.)[0-9]{0,3}$', ip).group(1) + '1'

    while True:
        with open('status.log', 'r') as f:
            log = f.read()
            tap_read = int(re.search(r'TUN/TAP read bytes,([0-9]*)', log).group(1)) / 1048576
            tap_write = int(re.search(r'TUN/TAP write bytes,([0-9]*)', log).group(1)) / 1048576
            udp_read = int(re.search(r'TCP/UDP read bytes,([0-9]*)', log).group(1)) / 1048576
            udp_write = int(re.search(r'TCP/UDP write bytes,([0-9]*)', log).group(1)) / 1048576
        p = ping(host_ip)
        clear()
        print('连接成功，你的IP是: %s\n网络延迟: %sms\n' % (ip, p))
        print('上行流量: %.2fMB\t实际消耗上行流量: %.2fMB' % (tap_read, udp_write))
        print('下行流量: %.2fMB\t实际消耗下行流量: %.2fMB' % (tap_write, udp_read))
        print('\n关闭本窗口即可断开连接', end='')
        time.sleep(5)
