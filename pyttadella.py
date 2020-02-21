#!/usr/local/bin/python3

from time import sleep
from sys import argv

from curtsies import Input #, send
#import tty
#import sys
#import termios

import commands as cmd
import bbs
from connection import server_connect, login
from tests import make_tests

from bot import cittabot

######
username = 'Guest'
password = ''

######

user_is_guest = False
user_is_logged_in = False

current_room = ''


##########

def get_cmd(tn, input_generator):
    ch = input_generator.send(timeout = 0)
    if ch is not None:
        if ch == 'a':
            bbs.goto(tn, 'abandon')
        if ch == 'g':
            bbs.goto(tn, 'goto')
        elif ch == 'L':
            bbs.goto(tn, 'skip_home')
        elif ch == 's':
            bbs.goto(tn, 'skip')
        elif ch == 'k':
            bbs.known_rooms(tn)
        elif ch == 'Q':
            return False
        elif ch == '5':
            bbs.read(tn, 'last5')
        elif ch == 'n':
            bbs.read(tn, 'new')
        elif ch == 'n':
            bbs.read(tn, 'next')
        elif ch == 'w':
            bbs.hwho(tn)
        elif ch == 'KEY_F(1)':
            cmd.toggle_debug()
            print(f'Toggle debug: {"on" if cmd.debug else "off"}')
        else:
            print(f'Pressed {ch}')
    else:
        pass
        #print('.', end = '.', flush = True)
    return True


def client_cycle(tn, input_generator):
    cmd.esegue_cmd_old(tn)

    while get_cmd(tn, input_generator):
        cmd.elabora_input(tn)
        cmd.esegue_comandi(tn)
        if True: # only if non urgent also
            cmd.esegue_cmd_old(tn)
        sleep(0.1)
        #print('.', end = '', flush = True)

if __name__ == '__main__':
    host, port = None, None

    if '-t' in argv:
        make_tests()

    if '-bot' in argv:
        cittabot()
        exit(0)

    # tn = server_connect(host, port)
    tn = server_connect()
    login(tn, username, password)

    with Input(keynames='curses') as input_generator:
        client_cycle(tn, input_generator)

    bbs.quit(tn)
    tn.close()

