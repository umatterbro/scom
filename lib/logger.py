import datetime
import inspect

class _color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def on(self) -> str:
        return f'\033[38;2;{self.r};{self.g};{self.b}m'

    def off(self) -> str:
        return '\033[0m'

pos_c = _color(0, 255, 0)
neg_c = _color(255, 0, 0)
wrn_c = _color(255, 255, 0)
dbg_c = _color(0, 150, 255)
neu_c = _color(96, 96, 96)

def _log(fname: str, fline: int, msg: str, status: str, end: str = '\n'):
    timestamp = round(datetime.datetime.now().timestamp())
    print(f'[{status}] [{timestamp}] {fname}:{fline} - {msg}', end=end, flush=True)

def positive(msg: str, end: str = '\n'):
    current = inspect.currentframe()
    parent = inspect.getouterframes(current, 2)[1]

    fname = parent.filename.split('/')[::-1][0].split('.')[0]
    fline = parent.lineno
    _log(fname, fline, msg, f'{pos_c.on()}POS{pos_c.off()}', end)

def negative(msg: str, end: str = '\n'):
    current = inspect.currentframe()
    parent = inspect.getouterframes(current, 2)[1]

    fname = parent.filename.split('/')[::-1][0].split('.')[0]
    fline = parent.lineno
    _log(fname, fline, msg, f'{pos_c.on()}NEG{pos_c.off()}', end)

def warn(msg: str, end: str = '\n'):
    current = inspect.currentframe()
    parent = inspect.getouterframes(current, 2)[1]

    fname = parent.filename.split('/')[::-1][0].split('.')[0]
    fline = parent.lineno
    _log(fname, fline, msg, f'{wrn_c.on()}WRN{wrn_c.off()}', end)

def debug(msg: str, end: str = '\n'):
    current = inspect.currentframe()
    parent = inspect.getouterframes(current, 2)[1]

    fname = parent.filename.split('/')[::-1][0].split('.')[0]
    fline = parent.lineno
    _log(fname, fline, msg, f'{dbg_c.on()}DBG{dbg_c.off()}', end)
