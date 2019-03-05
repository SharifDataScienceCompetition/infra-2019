import json
import pty
import random
import string

from fabric import Connection
from invoke import Responder


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def _startConnection(host, user, port, password=None):
    c = Connection(host=host, user=user, port=port)
    return c


def _initialize():
    # c.run('pkill -f ')
    c.run('pip install jupyter notebook')
    c.run('apt install screen htop vim net-tools -y')
    c.run('apt install cmake libncurses5-dev libncursesw5-dev git -y;'
          'rm -rf nvtop;'
          'git clone https://github.com/Syllo/nvtop.git;'
          'mkdir -p nvtop/build;'
          'cd nvtop/build;'
          'cmake .. -DNVML_RETRIEVE_HEADER_ONLINE=True;'
          'make;'
          'make install')


def _create_user(c):
    username: str = id_generator(10)
    password = id_generator()
    users.append(User(username, password))
    f.write(username + " " + password + "\n")
    # sudoPass = Responder(pattern=r'\[sudo\] password:', response=password + '\n', )
    c.run('adduser --disabled-password --force-badname --gecos "" ' + username)
    c.run('echo "{username}:{password}" | chpasswd'.format(
        username=username,
        password=password))
    return (username, password)
    # c.run('adduser ' + username + ' sudo')


def _ssh_config(c):
    c.run('echo -e "PasswordAuthentication yes\n$(cat /etc/ssh/sshd_config)" > "/etc/ssh/sshd_config"')
    c.run('service ssh reload')


def _run_jupyter(username, password, host, port):
    c = Connection(username + '@' + host + ':' + str(port),
                   connect_kwargs={"password": password})
    jup_port = random.randint(500, 6500)
    c.run('nohup jupyter notebook --ip=0.0.0.0 --port='
          + jup_port
          + '--NotebookApp.token=\'\' '
            '--NotebookApp.password=\'\' '
            '0<&- &> '
            'my.admin.log.file &')
    return jup_port

users = []
server_info = {}

if __name__ == '__main__':
    f = open("user_pass.txt", 'a+')
    # f.write("try:\n")
    count = 0
    for host, user, port in [('ssh5.vast.ai', 'root', 16084), ('ssh4.vast.ai', 'root', 16092),
                             ('ssh5.vast.ai', 'root', 16093), ]:
        count += 1
        server_name = 'server' + str(count)
        server_info[server_name] = {}

        c = _startConnection(host=host, user=user, port=port)
        _initialize()
        server_info[server_name]['port'] = port
        server_info[server_name]['root_user'] = user
        server_info[server_name]['host'] = host
        server_info[server_name]['users'] = []
        for i in range(0, 2):
            user_username, user_password = _create_user(c)
            _ssh_config(c)
            jup_port = _run_jupyter(user_username, user_password, host, port)
            server_info[server_name]['users'].append({'username': user_username, 'password': user_password, 'port': jup_port})
        # c.run('echo -e "PasswordAuthentication yes\n$(cat /etc/ssh/sshd_config)" > "/etc/ssh/sshd_config"')
        # c.run('service ssh reload')
        c.close()
        # _run_jupyter(users[len(users) - 1].username, users[len(users) - 1].password, host, port)

    json_data = json.dumps(server_info)
    f.write(json_data)
    f.close()
