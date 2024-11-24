import math

class partition:
    def __init__(self, *values):
        self.values = values
    
    _DIV_VAL = 255
    _EOS_VAL = 0
    _EOF_VAL = 254
    _SOF_VAL = 253
    _MAX_LEN = 252

    def _byteify(self, data):
        if(isinstance(data, str)): return data.encode()
        if(isinstance(data, int)): return str(data).encode()
        try: 
            return data.compile().data()
            return str(data).encode()
        except: pass
        return data

    def data(self):
        barr = bytearray()
        barr.append(self._SOF_VAL)
        for value in self.values:
            current = []
            value = self._byteify(value)

            lv = len(value)
            if(lv > self._MAX_LEN):
                f = 0
                div = math.floor(lv / self._MAX_LEN)
                rem = lv % self._MAX_LEN

                for x in range(div): current.append(self._MAX_LEN)
                current.append(rem)
            else: current.append(lv)

            barr.extend(current)
            barr.append(self._DIV_VAL)

        barr.append(self._EOS_VAL)
        for value in self.values:
            barr.extend(self._byteify(value))

        barr.append(self._EOF_VAL)
        return barr

def get_values(data: bytearray):
    print(f'get_values call')
    if(not isinstance(data, bytearray)): raise ValueError(f'data must be of type bytearray, not {type(data).__name__}')

    lens = []
    clen = 0
    plen = 0
    eos = False
    eos_l = 0
    rest = bytearray()
    for x in range(len(data)):
        if(x == 0 or x == len(data) - 1): continue

        itm = data[x]
        if(eos): 
            rest.append(itm)
        else:
            if(x > 0 and itm == 0):
                eos = True
                eos_l = x
                continue

            if(itm == 255):
                clen += plen
                lens.append(clen)
                plen = clen
                clen = 0
                continue
            clen += itm

    nlen = 0
    olen = 0
    vals = []

    for x in lens: 
        nlen = x
        vals.append(rest[olen:nlen])
        olen = nlen
    return vals

def is_partition(data: bytearray):
    if(not isinstance(data, bytearray)): raise ValueError(f'data must be of type bytearray, not {type(data).__name__}')
    if(len(data) == 0): return False

    return data[0] == 253 and data[::-1][0] == 254
