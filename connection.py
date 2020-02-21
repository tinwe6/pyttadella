from enum import Enum

import commands as cmd
from utils import Version, filter_tags
from bbs import goto

debug = False

HOST = 'cittadella.cittadellabbs.it'
PORT = 4000

client_name = 'Pyttadella'
client_version = Version(0, 1, 0)

GUEST_USERNAME = 'Guest'

class ClientState(Enum):
    start = 1
    login = 2
    march = 3
    read  = 4


def serv_info(tn):
    server_data = cmd.info(tn)
    if server_data is not None:
        print('Server: {} version {}'.format(server_data['software'],
                                             server_data['version']))
        print('        {} ({})'.format(server_data['node'],
                                       server_data['where']))
        print('Client: {} version {} - protocol {}'.format(
        client_name, client_version, server_data['client_v']))

    return server_data


def bbs_show_banner(tn, short = True):
    """
    Displays the bbs banner.
    """
    lines = cmd.lban(tn, short_banner = short)
    for line in lines:
        print(filter_tags(line))


def bbs_chek(tn):
    chek_data = cmd.chek(tn)
    print(f"{chek_data['num_users']} connected users.\n")
    print('Call n.{} for user n.{} of level {}'.format(chek_data['num_calls'],
            chek_data['userid'], chek_data['level']))       
    print('Last connection {} at {} from {}'.format(chek_data['num_calls'],
            chek_data['userid'], chek_data['lasthost']))
    print('{} new mail.'.format(chek_data['new_mail']))


def bbs_login(tn, username: str, password: str):
    success = False
    user_is_guest = False
    if username is None:
        username = input(
            "Insert your bbs nickname or 'Guest' if to have a look around.\n"
            "('Off' to close the connection)\n\n"
            "Name    : "
            )
    if username.lower() in ['off', 'esci', 'exit', 'quit']:
        return False, None, None

    code, params = cmd.user(tn, username)
    if code == '223': # utente validato
        already_connected = (params[0] == '1')
        if already_connected:
            print('Your other connection will be kicked out.')
        password = input("password: ")
        code, line = cmd.usr1(tn, username, password)
        print(line)
        if code == cmd.RESP_OK:
            print('User logged in.')
            success = True
        elif code == '100': # already logged in
            pass
        elif code == '130': # wrong password
            pass
    elif code == '221': # guest
        code, line = cmd.usr1(tn, username, password)
        print(line)
        if code == cmd.RESP_OK:
            print('User logged in as guest.')
            user_is_guest = True
            success = True
    
    if success and not user_is_guest:
        bbs_chek(tn)

    return success, user_is_guest, code


import telnetlib

def send_command(tn, cmd):
    if debug:
        print(f'> send {cmd}')
    tn.write(cmd.encode('ascii') + b'\n')

def connect(host: str, port: int):
    """
    Connects to the server. If the connection is correctly established
    returns the telnet connection object, otherwise exits the program.
    """
    print('Connecting to the server...')
    print(cmd.RESP_OK, type(cmd.RESP_OK))
    tn = telnetlib.Telnet(host = host, port = port)
    code, params = cmd.serv_read_resp(tn)
    if code != cmd.RESP_OK:
        print(f'Connection problem. {code, params}')
        exit(0)
    print(f'{params[0]}\n')
    return tn


def server_connect(host = HOST, port = PORT, show_banner: bool = True,
                   short_banner = False):
    """
    Connects to the bbs server and retrieves server info.
    If show_banner, displays the bbs banner.
    """
    tn = connect(host, port)
    # retrieve server info
    server_data = serv_info(tn)
    # show login banner
    bbs_show_banner(tn, short = short_banner)
    # complete login procedure

    return tn


def login(tn, username, password):
    success, user_is_guest, code = bbs_login(tn, username, password = '')
    if success:
        # TODO check polls

        user_is_logged_in = True
        client_state = ClientState.login
        # go to lobby
        goto(tn, 'skip_home')
        client_state = ClientState.march

    return success

