
from time import sleep
from queue  import SimpleQueue
from enum import Enum
from typing import List, Dict, Any

from utils import Version
from connection import send_command

#from asyncio import SimpleQueue

post_timeout = False

debug = False

def toggle_debug():
    global debug
    debug = not debug

class Response(Enum):
    OK         = '200'
    START_LIST = '210'
    END_LIST   = '000'
    ERROR      = '100'

RESP_OK         = '200'
RESP_START_LIST = '210'
RESP_END_LIST   = '000'
RESP_ERROR      = '100'

#def ifnone(a: Any, b: Any) -> Any:
#    "`a` if `a` is not None, otherwise `b`."
#    return b if a is None else a

def intOrZero(value):
    return 0 if value is '' else int(value)

###


def unpack_parms(params, parm_names = None):
    if len(parm_names) != len(params):
        print('Error: number of parameters does not match.', )
        parm_dict = dict(zip(range(len(params)), params))
    else:
        parm_dict = dict(zip(parm_names, params))
    return parm_dict

def unpack_parms_t(params, parm_desc):
    parm_dict = {}
    if len(parm_desc) != len(params):
        print('Error: number of parameters does not match.')
        print(params, params)
        assert False
    else:
        for value, (name, t) in zip(params, parm_desc):
            parm_dict[name] = t(value)
    return parm_dict



##########

#########
def esegue_urgenti(command):
    """ Esegue i comandi urgenti provenienti dal server. """
    assert command[0] == '8'

    cmd_type, cmd_subtype = command[1], command[2]
    {800: "Login timeout.",
     810: "Idle timeout.",
     820: "Kick out",
     830: "Shutdown",
     831: "Shutdown canceled",
     840: "Request for remote host",
     850: "Deleted room",
     860: "Post timeout"}
    
    if cmd_type == '0': # login timeout
        print('\n\nLogin timeout.\n')
        exit(1)
    elif cmd_type == '1': # idle timeout
        print('\n\nIdle timeout.\n')
    elif cmd_type == '2': # kick out
        print('\n\n*** {command[4:]} kicked you out.\n')
    elif cmd_type == '3':        
        params = command[4:].split('|')
        if cmd_subtype == '0': # shutdown
            if int(params[1]) == 1:
                print('*** Warning: server shutdown in {} minutes.'
                      .format(int(params[0])))
            else:
                print('*** Warning: daily reboot in {} minutes.'
                      .format(int(params[0])))
        elif cmd_subtype == '1': # shutdown canceled
                print('*** Shutdown canceled.')
    elif cmd_type == '4': # the server requests the host
        pass
    elif cmd_type == '5': # the current room has been deleted
        print('*** The current room has been deleted.')
        bbs_goto(tn, 'skip_home')
    elif cmd_type == '6': # idle timeout
        # todo beep()
        if cmd_subtype == '0':
            print('\n*** Available time to post has elapsed.')
            post_timeout = True
        elif cmd_subtype == '1':
            print('\n*** The deadline for this vote is approaching!')

def chat_exit():
    # current_chat_channel = 0
    pass

def notifica(cmd):
    kind = cmd[2]
    #sex = cmd[4]        # we don't use it
    name = cmd[5:]
    if kind == '0':
        print(f'*** {name} has just logged in.')
    elif kind == '1':
        print(f'*** {name} has left the bbs.')
    elif kind == '2':
        print(f'*** {name} has entered the chat.')
    elif kind == '3':
        print(f'*** {name} has left the chat.')
    elif kind == '4':
        print(f"*** {name}'s connection dropped.")
    elif kind == '5':
        print(f"*** {name} went for a nap...")
    elif kind == '6':
        print('*** Oops... you slid off the chat!')
        chat_exit()
    elif kind == '6':
        print(f'*** {name} you slid off the chat!')
    else:
        return False
    return True

def notifica_post(cmd):
    kind = cmd[2]
    #sex = cmd[4]        # we don't use it
    name = cmd[4:] if len(cmd) > 4 else 'Someone'
    if kind == '0':
        print(f'*** {name} has posted a new message in this room.')
    elif kind == '1':
        print(f"*** You've got mail.")
    elif kind == '2':
        print(f'*** {name}, meanwhile, posted a new message.')
    elif kind == '3':
        print(f'*** {name} has posted a message in your blog.')
    else:
        return False
    return True

def notifica_idle(cmd):
    kind = cmd[2]
    if kind == '0':
        print(f'*** Is there anybody out there?')
    elif kind == '1':
        print(f"*** Warning! you'll soon be kicked out!")
        # close_session = True
    else:
        return False
    return True

class MsgKind(Enum):
    NONE = 0
    BROADCAST = 1
    EXPRESS = 2

    @classmethod
    def from_code(cls, code: str):
        d = {'0': MsgKind.BROADCAST, '1': MsgKind.EXPRESS}
        return d[code[2]]

    def __str__(self) -> str:
        if self is MsgKind.BROADCAST:
            return 'Broadcast'
        elif self is MsgKind.EXPRESS:
            return 'Express Message'
        else:
            return 'Message'

class Xmsg():
    def __init__(self, sender: str, hour: int = -1, minute: int = -1,
                 text: List[str] = [], kind = MsgKind.NONE) -> None:
        self.sender = sender
        self.text = text
        self.hour, self.minute = hour, minute
        self.kind = kind
        self.recipients = []

    def append_line(self, line: str):
        self.text.append(line)

    def add_recipient(self, recipient: str):
        self.recipients.append(recipient)

    @classmethod
    def from_dict(cls, d: Dict[str, Any], kind = MsgKind.NONE):
        xmsg = cls(sender = d['sender'], hour = d['hour'], minute = d['min'],
                   text = d.get('body', []), kind = kind)
        return xmsg

    @property
    def header(self):
        header = ('*** {} by {} at {:02d}:{:02d}'
                  .format(self.kind, self.sender, self.hour, self.minute))
        return header

    def __repr__(self) -> str:
        return "<Xmsg sender: {}, hour: {}, min: {}, kind: {}, text: {}>".format(
                self.sender, self.hour, self.minute, self.kind, self.text
                )

    def __str__(self) -> str:
        result = self.header + '\n'
        for line in self.text:
            result += ('> ' + line + '\n')
        return result


class XmsgManager():
    def __init__(self) -> None:
        self.msg_queue = SimpleQueue()
        self.incoming = None

    def server_cmd(self, cmd: str) -> None:
        code, params = cmd[:3], cmd[4:].split('|')
        assert code[2]

bx_incoming = None
bx_queue = SimpleQueue()

def bx(cmd):
    global bx_incoming

    #print('BX > ', cmd)
    kind = cmd[2]
    if kind == '0' or kind == '1':
        if bx_incoming is not None:
            print('Error: discarding incomplete Xmsg')
            bx_incoming = None
        params = cmd[4:].split('|')
        parm_desc = [('sender', str), ('hour', int), ('min', int)]
        data = unpack_parms_t(params, parm_desc)
        bx_incoming = Xmsg.from_dict(data, kind = MsgKind.from_code(cmd[:3]))
    elif kind == '2': # incoming txt line
        line = cmd[4:]
        bx_incoming.append_line(line)
    elif kind == '3': # end of message
        print('\n' + bx_incoming.__str__() + '\n')

        bx_incoming = None
    elif kind == '4': # incoming message from chat channel
        pass
    elif kind == '5': # incoming line from chat channel
        pass
    elif kind == '6': # end of chat message
        pass
    elif kind == '7': # destinatari
        bx_incoming.add_recipient(cmd[4:])
    else:
        return False
    return True

def test_bx():
    bx("901 Ping|12|16")
    assert repr(bx_incoming) == '<Xmsg sender: Ping, hour: 12, min: 16, kind: Express Message, text: []>'
    bx("907 Mr Test")
    assert repr(bx_incoming) == '<Xmsg sender: Ping, hour: 12, min: 16, kind: Express Message, text: []>'
    bx("902 hello!")
    assert repr(bx_incoming) == "<Xmsg sender: Ping, hour: 12, min: 16, kind: Express Message, text: ['hello!']>"
    bx("902 Hoe gaat het met dit Express Message?")
    assert repr(bx_incoming) == "<Xmsg sender: Ping, hour: 12, min: 16, kind: Express Message, text: ['hello!', 'Hoe gaat het met dit Express Message?']>"
    bx("903")
    assert bx_incoming == None


def esegue_comandi(tn):
    ret = 0
    while not command_queue.empty():
        cmd = command_queue.get()
        cmd_type = cmd[1]
        if cmd_type == '0':
            #print('esegue_comandi:', cmd)
            ret = bx(cmd)
            pass
        elif cmd_type == '1':
            ret = notifica(cmd)
            pass
        elif cmd_type == '2':
            ret = idle_cmd(cmd)
            pass
        elif cmd_type == '3':
            ret = notifica_post(cmd)
            pass
        elif cmd_type == '4':
            print('load userconfig:', cmd)
            #carica_userconfig(0);
            pass
    return ret

def esegue_cmd_old(tn):
    if not command_queue.empty():
        print('\nThese messages arrived while you were busy.\n')
        esegue_comandi(tn)

##########
class Connection:
    def __init__(self, tn):
        self.tn = tn
        self.server_queue_in = SimpleQueue()
        self.command_queue = SimpleQueue()
        self.server_buffer = b''


server_queue_in = SimpleQueue()
command_queue = SimpleQueue()
server_buffer = b''

def server_read(tn):
    """
    Buffers the available input from the server and queues complete
    commands.
    """
    global server_buffer 

    buf = tn.read_very_eager()
    server_buffer += buf

    while True:
        i = server_buffer.find(b'\n')
        if i >= 0:
            server_queue_in.put(server_buffer[:i].decode('ascii'))
            server_buffer = server_buffer[i + 1:]
        else:
            break
    #print('exit server_read')


def elabora_input(tn) -> int:
    """
    reads available input from the queue, executes immediately urgent
    complete commands and queues the other complete commands in the
    command_queue.
    Returns the number of queued commands
    """
    server_read(tn)

    # if debug:
    #         print(f'&S {server_buffer}')

    # TODO Se c'e' altro input in coda, segnala in una variabile globale */
    # server_input_waiting = serv_buffer_has_input();

    while not server_queue_in.empty():
        #print('elabint loop')
        line = server_queue_in.get()
        #print('line', line)
        if line[0] == '8': # Urgent message
            execute_urgent(line)
        elif line[0] == '9':
            #print('insert in command queue')
            command_queue.put(line)
        else:
            command_queue.put(line)
        #print(server_queue_in.empty(), server_queue_in.qsize())
    #print('exit elabora_input - command.qsize', command_queue.qsize())
    return command_queue.qsize()


def serv_gets(tn) -> str:
    """
    Reads a string from the server. Keeps on reading with elabora_input()
    until it receives a non-command string.
    """

    while command_queue.qsize() == 0:
        elabora_input(tn)
    #print('serv_gets', command_queue.qsize())
    line = command_queue.get()
    #print('serv_gets line', line)

    return line

#########

def send_cmd_parms(tn, cmd, parms):
    command = cmd + ' ' + '|'.join(map(str, parms))
    send_command(tn, command)


# def serv_read(tn):
#     line = tn.read_until(b'\n').decode('ascii')
#     line = line[:-1] # drop the ending '\n'
#     if debug:
#         print(f'> {line}')
#     return line

def serv_read_line(tn):
    answer = serv_gets(tn)
    if len(answer) == 3:
        # It's just a code, no parameters
        code = answer
        line = ''
    else:
        code = answer[:3]
        assert answer[3] == ' '
        line = answer[4:]
    
    if debug:
        print(f"< read {code}: '{line}'")

    return code, line

def serv_read_resp(tn):
    """
    Reads a response from the server.
    Return code, params
    with code a 3 digit response code and params the list of parameters
    """
    line = serv_gets(tn)
    if len(line) == 3:
        # It's just a code, no parameters
        code = line
        params = []
    else:
        code = line[:3]
        assert line[3] == ' '
        params = line[4:]
        params = params.split('|')
    
    if debug:
        print(f'< read {code}: {params}')
        #for i, p in enumerate(params):
        #    print(i, p)

    return code, params


#######

def user(tn, username: str):
    send_command(tn, f'USER {username}')
    code, params = serv_read_resp(tn)
    return code, params

def usr1(tn, username: str, password: str):
    # don't send a password field if logging in as guest
    args = [username, password] if password is not None else [username]
    send_cmd_parms(tn, 'USR1', args)
    code, line = serv_read_line(tn)
    return code, line

def info(tn):
    send_cmd_parms(tn, 'INFO', ['locale', '0'])
    code, params = serv_read_resp(tn)

    if code != RESP_OK:
        return None

    parm_desc = [('software', str),
                 ('version', Version.from_code),
                 ('node', str),
                 ('where', str),
                 ('client_v', Version.from_code), # client protocol vers.
                 ('chat', int),    # number chat channels
                 ('maxpost', int),  # max lines per post
                 ('maxbx', int),   # max lines per x/bc/
                 ('flags', int),   # valid key, floors, referendum, memstats
                 ('compression', bool),
                 ('p10', int), ('p11', int), ('p12', int), ('p13', str)]
    server_data = unpack_parms_t(params, parm_desc)
    return server_data

def lban(tn, short_banner = True):
    send_command(tn, f'LBAN {0 if short_banner else 1}')
    code, params = serv_read_resp(tn)
    lines = []
    if code == RESP_START_LIST:
        while code != RESP_END_LIST:
            code, line = serv_read_line(tn)
            if code == RESP_OK:
                lines.append(line)
    else:
        print(f'Error: {code}')
    return lines

def chek(tn):
    send_command(tn, f'CHEK')
    code, params = serv_read_resp(tn)
    parm_desc = [
        ('num_users', int), # number of users presently connected to the bbs
        ('userid', int),    # unique user id
        ('level', int),     # user level
        ('num_calls', int), # total number of calls 
        ('lastcall', int),  # date and time of last connection
        ('lasthost', str),  # host of last connection
        ('new_mail', int),  # number new mail messages
    ]
    chek_data = unpack_parms_t(params, parm_desc)
    return chek_data

def hwho(tn):
    users, num_guests = [], 0
    send_command(tn, f'HWHO')
    code, params = serv_read_resp(tn)
    if code == RESP_START_LIST:
        while code != RESP_END_LIST:
            code, params = serv_read_resp(tn)
            if code == RESP_OK:
                parm_names = ['socket', 'name', 'unused',
                              'login_time', 'room', 'chat_ch']
                user_data = unpack_parms(params, parm_names)
                code, line = serv_read_line(tn)
                user_data['host_doing'] = line
                users.append(user_data)
        code, params = serv_read_resp(tn)
        num_guests = int(params[0])
    return users, num_guests

def rkrl(tn, mode: int = 1):
    """
    RKRL mode|floor"                                                                         
    mode : 0 - Tutte le room conosciute (anche zappate)                                                 
           1 - con messaggi nuovi                                                                       
           2 - senza messaggi nuovi                                                                     
           3 - room zappate                                                                             
    floor: 0 - Considera tutte le room presenti                                                         
           1 - Solo le room nel floor corrente                                                          
   Restituisce: "Nome Room|Num Room|Zap"                                                                
             - Zap: 1 se zappata.          
    """
    rooms = []
    send_command(tn, f'RKRL {mode}')
    code, _ = serv_read_resp(tn)
    if code == RESP_START_LIST:
        while code != RESP_END_LIST:
            code, params = serv_read_resp(tn)
            if code == RESP_OK:
                parm_desc = [('name', str), ('id', int), ('is_zapped', bool)]
                parm_desc = parm_desc[:len(params)]
                room_data = unpack_parms_t(params, parm_desc)
                rooms.append(room_data)
    return rooms


goto_mode = {'goto': 0, 'skip': 1, 'abandon': 2, 'scan': 3, 'skip_home': 4,
             'abandon_mail':5, 'abandon_home': 6, 'abandon_blog': 7}
goto_type = {'room': 0, 'floor': 1, 'blog': 2}

def goto(tn, mode: str, name: str = '', dest_type: str = 'room'):
    send_cmd_parms(tn, 'GOTO', [goto_mode[mode], name, dest_type])
    code, params = serv_read_resp(tn)
    if code != RESP_OK:
        return code, None
    param_desc = [('name', str), ('room_type', str), ('num_msg', int),
                  ('new_msg', int), ('new_gen', bool), ('flags', int),
                  ('rooms_new', int), ('rooms_zap', int)]
    data = unpack_parms_t(params, param_desc)
    return code, data


read_mode = {'forward': 0, 'new': 1, 'reverse': 2, 'brief': 3, 'last5': 5,
    'lastN': 6, 'from_msgnum': 7, 'next': 10, 'prev': 11, 'back': 12}

def read(tn, mode, num = 0):
    send_cmd_parms(tn, 'READ', [read_mode[mode], num])
    code, params = serv_read_resp(tn)

    if code != RESP_OK:
        return None, code

    local_num, remain = int(params[0]), int(params[1])
    code, params = serv_read_resp(tn)
    assert code == RESP_START_LIST
    param_desc = [
        ('msgnum', int), ('roomname', str), ('author', str), ('timestamp', int),
        ('subject', str), ('flags', int), ('recipient', str),
        ('reply_to', str), ('reply_locnum', intOrZero), ('nickname', str),
        ('len', int)
        ]
    # at the moment admin posts and mails send less parameters
    param_desc = param_desc[:len(params)]
    header = unpack_parms_t(params, param_desc)
    header['local_num'] = local_num
    header['remain'] = remain
    body = []
    while True:
        code, line = serv_read_line(tn)
        if code == RESP_END_LIST:
            break
        body.append(line)
    return header, body

def quit(tn):
    send_command(tn, 'QUIT')
    code, params = serv_read_resp(tn)
    return code, params
