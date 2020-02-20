from datetime import datetime

class Version:
    def __init__(self, major, minor, sublvl):
        self.major = major
        self.minor = minor
        self.sublvl = sublvl        

    @classmethod
    def from_code(self, code):
        if isinstance(code, str):
            code = int(code)
        major = code >> 16
        minor = (code >> 8) & 0xff
        sublvl = code & 0xff
        return Version(major, minor, sublvl)

    @property
    def code(self):
        return (self.major << 16) | (self.minor << 8) | self.sublvl

    def __repr__(self):
        return f'{self.major}.{self.minor}.{self.sublvl}'

def version_str(code: int):
    major = code >> 16
    minor = (code >> 8) & 0xff
    sublvl = code & 0xff
    return f'{major}.{minor}.{sublvl}'

# Date and time utilities

def time_from_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%H:%M')

def date_from_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

#

# CML utils

def filter_tags(line):
    n = len(line)
    i = 0
    result = ''
    while i < n:
        if line[i] == '<' and (i + 1 < n) and line[i + 1] != '<':
            while i < n and line[i] != '>':
                i += 1
        elif line[i] == '\\':
            if (i + 1 < n) and line[i + 1] == '\\':
                i += 1
                result += '\\'
        else:
            result = result + line[i]
        i += 1
    result = result.replace('&eacute;', 'é')
    result = result.replace('&agrave;', 'à')
    result = result.replace('&egrave;', 'è')
    result = result.replace('&igrave;', 'ì')
    result = result.replace('&ograve;', 'ò')
    result = result.replace('&ugrave;', 'ù')
    return result

