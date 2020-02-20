import commands as cmd
from utils import date_from_timestamp, time_from_timestamp

class Post:
    def __init__(self, header: dict, body: list):
        assert header is not None and body is not None
        self.header = header
        self.body = body

    @property
    def formatted(self) -> str:
        result = '{}, {} at {} - by {}\n'.format(
            self.header['roomname'],
            date_from_timestamp(self.header['timestamp']),
            time_from_timestamp(self.header['timestamp']),
            self.header['author']
            )
        if self.header['reply_locnum']:
            if self.header['subject'] != '':
                result += 'Reply: {}, msg #{} by {}\n'.format(
                    self.header['subject'],
                    self.header['reply_locnum'],
                    self.header['reply_to']
                    )
            else:
                result += 'Reply to msg #{} by {}\n'.format(
                    self.header['reply_locnum'],
                    self.header['reply_to']
                    )
        elif self.header['subject'] != '':
            result += 'Subject: {}\n'.format(self.header['subject'])
        result += '\n'
        for line in self.body:
            result += filter_tags(line) + '\n'
        return result

###

def read(tn, mode, num = 0):
    header, body = cmd.read(tn, mode, num = num)
    if header is None:
        return
    post = Post(header, body)
    print('\n' + post.formatted)


def goto(tn, mode = 'goto'):
    code, room = cmd.goto(tn, mode)
    print('\n{}{} - {}/{} new messages.'.format(room['name'], room['room_type'],
        room['new_msg'], room['num_msg']), end = '\n', flush = True)
    if room['name'] == 'Lobby':
        print('\nYou have {} rooms with new messages and {} zapped rooms.'
              .format(room['rooms_new'], room['rooms_zap']))

def known_rooms(tn, mode = 'new_msg'):
    known_room_mode = {'all': 0, 'new_msg': 1, 'no_new_msg': 2, 'zapped': 3}
    rooms = cmd.rkrl(tn, known_room_mode[mode])
    count = 0
    for room in rooms:
        if count == 3:
            print()
            count = 0
        #print(f'{room['id']:>3}. {room['name']:<19}', end = '')
        print(f"{room['id']:>3}. {room['name']:<20}", end = '')
        count += 1
    print()


def hwho(tn):
    print(
"""

Login        Nome Utente               Room               Da Host/[Doing]
----- ------------------------- ------------------- ----------------------------
""", end = '')
    users, num_guests = cmd.hwho(tn)
    num_users, num_logging_in = 0, 0
    for user in users:
        login_time = time_from_timestamp(int(user['login_time']))
        host_doing = f"{user['host_doing']:<26}"
        if user['host_doing'][0] == '[':
            host_doing += ']'

        print('{} {:<24}{} {:<19} {}'.format(
            login_time, user['name'], 'C' if int(user['chat_ch']) else ' ',
            user['room'], host_doing
            ))
        if user['name'] == '(login in corso)':
            num_logging_in += 1
        else:
            num_users += 1
    print()
    if num_users + num_guests == 1:
        print('Cheer up, others will soon arrive! :)')
    else:
        if num_users == 1:
            if (num_guests == 1):
                print(f'There is 1 user and 1 guest.')
            else:
                print(f'There are 1 user and {num_guests} guests.')
        else:
            if num_guests == 0:
                print(f'There are {num_users} users.')
            elif num_guests == 1:
                print(f'There are {num_users} users and 1 guest.')
            else:
                print(f'There are {num_users} users and {num_guests} guests.')
    print()
    if num_logging_in > 0:
        print('{} login{} in progress'.format(
            num_logging_in, '' if num_logging_in == 1 else 's'
            ))

def quit(tn):
    """%d %ld|%ld|%ld|%ld\n", OK, t->num_cmd, t->bytes_in,
                t->bytes_out, time_online"""
    code, params = cmd.quit(tn)
    if code == cmd.RESP_OK:
        print('[Disconnessione...]')
        print('Hai inviato {} bytes, ricevuto {} bytes [compressione 0%].'
            .format(params[1], params[2]))
        print('{} comandi, {} sec)'.format(params[0], params[3]))
    else:
        print('[Deconnection failed]')


