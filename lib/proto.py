import logger
import datetime
import os
import re
import enum
import partitioner

# packet structure
# - sis (section information section), includes data on where packet sections start and end
#   * tdstart: int (transfer data section start), where the tds starts
#   * psdstart: int (packet specific data section start), where the psds starts
#   * pkend: int (packet end), where the packet ends
# - tds (transfer data section)
#   * src: 10 bytes (source), the source of the packet
#   * dst: 10 bytes (destination), the destination for the packet
#   * flags: int, with each bit representing true or false
#   * timestamp: 4 bytes, timestamp of when the packet was sent
#   * req_num int, current request number
#   * checksum 32 bytes, sha256 hash of data
# - psds (packet specific data section)
# - FOR KEY:
#   * key_id: undefined len (key_id), identifier for the requested key
#   * key_pwd: undefined len (key_pwd), password to access the key (if required)
# - FOR SEC:
#   * headers: undefined len, headers with information about the request
#   * data: undefined len, data being received (encrypted)
# - FOR NSC:
#   * headers: undefined len, headers with information about the request
#   * data: undefined len, data being received (unencrypted)
# - FOR RTP:
#   * pack_n: int (packet number), packet number to retrieve from the server

class ident:
    _MAX_IDENT_LEN = 12
    _IDENT_CHUNK_SIZE = 2
    def __init__(self, bts: bytes):
        if(len(bts) != self._MAX_IDENT_LEN): raise ValueError(f'bts value must be {self._MAX_IDENT_LEN} bytes long, not {len(bts)}')
        nb = [[]]

        # takes bytes, makes sure the length of each value is 2 & creates arrays with _IDENT_CHUNK_SIZE hex values in each
        for x in range(len(bts)):
            citm = nb[::-1][0]
            if(len(citm) + 1 >= self._IDENT_CHUNK_SIZE and x + 1 < len(bts)): nb.append([])

            ch = hex(bts[x]).lstrip("0x")
            if(len(ch) == 1): ch = '0' + ch
            citm.append(ch)

        # joins each array of _IDENT_CHUNK_SIZE using a colon
        self.ident_str = ':'.join(''.join(y for y in x) for x in nb)

    @staticmethod
    def validate(ident_str: str):
        # uses regex to make sure it follows the given pattern & matches in length
        fa = re.findall('....:....:....:....:....:....', ident_str)
        if(len(fa) == 0): return False
        if(len(fa[0]) != len(ident_str)): return False
        return True

    @staticmethod
    def generate():
        return ident(os.urandom(12))

class packet:
    class section:
        def __init__(self):
            pass

    class sis_s(section):
        def __init__(self):
            pass

    class tds_s(section):
        class flag_cont:
            class flag(enum.Enum):
                KEY = 0         # key flag
                SYN = 1         # syn flag
                ACK = 2         # ack flag
                SEC = 3         # secure flag
                URG = 4         # urgent flag
                NSC = 5         # not secure flag
                RTP = 6         # retrieve packet (packet not received / hash doesnt match)
                DON = 7         # donut flag (donut!)

            def __init__(self, flag_i: int):
                # converts flag integer to its 8 bit binary value, interpreting each 0 or 1 as true or false to set flag active state
                if(not isinstance(flag_i, int)): raise ValueError(f'flag integer must be of type int (duh), not {type(flag_i).__name__}')
                binary = bin(flag_i).lstrip('0b')
                binary = ''.join('0' for _ in range(len(self.flag.__members__) - len(binary))) + binary

                self.flags = {}
                for x in range(len(binary)):
                    self.flags.update({self.flag(x): bool(int(binary[x]))})

            def get_flag(self, flag: flag):
                if(not isinstance(flag, self.flag)): raise ValueError(f'flag must be of type flag, not {type(flag).__name__}')
                return self.flags.get(flag)

            def get_active_flags(self):
                atfs = []
                for flag in self.flags.items():
                    if(flag[1]): atfs.append(flag[0])
                return atfs

            def to_int(self) -> int:
                key = self.get_flag(self.flag.KEY)
                syn = self.get_flag(self.flag.SYN)
                ack = self.get_flag(self.flag.ACK)
                sec = self.get_flag(self.flag.SEC)
                urg = self.get_flag(self.flag.URG)
                nsc = self.get_flag(self.flag.NSC)
                rtp = self.get_flag(self.flag.RTP)
                don = self.get_flag(self.flag.DON)

                if(not isinstance(key, bool) or not isinstance(syn, bool) or not isinstance(ack, bool) or not isinstance(sec, bool) or not isinstance(urg, bool) or not isinstance(nsc, bool) or not isinstance(rtp, bool) or not isinstance(don, bool)):
                    raise ValueError(f'all flags must be of type bool')

                fstr = f'0b{int(key)}{int(syn)}{int(ack)}{int(sec)}{int(urg)}{int(nsc)}{int(rtp)}{int(don)}'
                return int(fstr, 2)

            @staticmethod
            def create(key_flag: bool = False, syn_flag: bool = False, ack_flag: bool = False, sec_flag: bool = False, urg_flag: bool = False, nsc_flag: bool = False, rtp_flag: bool = False, don_flag: bool = False): 
                # creates a key from flag values, all default to false
                if(not isinstance(key_flag, bool) or not isinstance(syn_flag, bool) or not isinstance(ack_flag, bool) or not isinstance(sec_flag, bool) or not isinstance(urg_flag, bool) or not isinstance(nsc_flag, bool) or not isinstance(rtp_flag, bool) or not isinstance(don_flag, bool)):
                    raise ValueError(f'all flags must be of type bool')

                fstr = f'0b{int(key_flag)}{int(syn_flag)}{int(ack_flag)}{int(sec_flag)}{int(urg_flag)}{int(nsc_flag)}{int(rtp_flag)}{int(don_flag)}'
                return packet.tds_s.flag_cont(int(fstr, 2))

        def __init__(self, src: ident, dst: ident, flag_i: int | flag_cont, tsmp: float, req_num: int):
            # run checks on values passed
            if(not isinstance(src, ident)): raise ValueError(f'source must be of type ident, not {type(src).__name__}')
            if(not isinstance(dst, ident)): raise ValueError(f'destination must be of type ident, not {type(dst).__name__}')

            if(isinstance(flag_i, int)):
                if(flag_i.bit_length() > 8 or flag_i <= 0): raise ValueError(f'flags integer must be > 0 and < 256')
                self.flags = self.flag_cont(flag_i)
            elif(isinstance(flag_i, self.flag_cont)): self.flags = flag_i
            else: raise ValueError(f'flags must be of type int OR flag_cont, not {type(flag_i).__name__}')

            if(isinstance(tsmp, float)): tsmp = round(tsmp)
            if(not isinstance(tsmp, int)): raise ValueError(f'timestamp must be of type int or float, not {type(tsmp).__name__}')

            # set values to self
            self.src = src
            self.dst = dst
            self.tsmp = tsmp
            self.req_num = req_num

            super().__init__()
            logger.debug('transfer data section setup')

    class psds_s(section):
        class heads:
            def __init__(self, predef_headers: dict = None): 
                self._headers = {}
                if(predef_headers is not None):
                    if(not isinstance(predef_headers, dict)): raise ValueError(f'predef_headers must be of type dict, not {type(predef_headers).__name__}')
                    print(predef_headers)
                    for header in predef_headers.items(): 
                        print(f'adding {header[0]}={header[1]}')
                        if(header[0] in self._headers): raise ValueError(f'attempt to redefine header {header[0]}')
                        self._headers.update({header[0]: header[1]})
                    logger.debug(f'loaded {len(self._headers)} predef headers')

            def get(self, key):
                return self._headers.get(key)

            def set(self, key, val):
                self._headers[key] = val

            def compile(self):
                return partitioner.partition(*[f'{h[0]}={h[1]}' for h in self._headers.items()])

        class _psds:
            def __init__(self, flag):
                if(not isinstance(flag, packet.tds_s.flag_cont.flag)): raise ValueError(f'flag must be of type flag, not {type(flag).__name__}')
                self.flag = flag

            def compile(self): 
                logger.warn('compile method has not been created for {self.flag.name}')
                return None

        class psds_key(_psds):
            def __init__(self, key_id: str, key_pwd: str):
                if(not isinstance(key_id, str)): raise ValueError(f'key_id must be of type str, not {type(key_id).__name__}')
                if(not isinstance(key_pwd, str)): raise ValueError(f'key_pwd must be of type str, not {type(key_pwd).__name__}')

                super().__init__(packet.tds_s.flag_cont.flag.KEY)
                self.key_id = key_id
                self.key_pwd = key_pwd

            def compile(self):
                return partitioner.partition(self.key_id, self.key_pwd)

        class psds_syn(_psds):
            def __init__(self):
                super().__init__(packet.tds_s.flag_cont.flag.SYN)

            def compile(self):
                return None

        class psds_ack(_psds):
            def __init__(self):
                super().__init__(packet.tds_s.flag_cont.flag.ACK)

            def compile(self):
                return None

        class psds_sec(_psds):
            def __init__(self, headers, data: str):
                if(not isinstance(headers, packet.psds_s.heads)): raise ValueError(f'headers must be of type heads, not {type(headers).__name__}')

                super().__init__(packet.tds_s.flag_cont.flag.SEC)

                self.headers = headers
                self.data = data

            def compile(self):
                return partitioner.partition(self.headers, self.data)

        class psds_urg(_psds):
            def __init__(self):
                super().__init__(packet.tds_s.flag_cont.flag.URG)

            def compile(self):
                return None

        # TODO: setup NSC packets
        class psds_nsc(_psds):
            def __init__(self, headers, data: str):
                if(not isinstance(headers, packet.psds_s.heads)): raise ValueError(f'headers must be of type heads, not {type(headers).__name__}')

                super().__init__(packet.tds_s.flag_cont.flag.NSC)

                self.headers = headers
                self.data = data

            def compile(self):
                return partitioner.partition(self.headers, self.data)

        # TODO: setup RTP packets
        class psds_rtp(_psds):
            def __init__(self, pack_n: int):
                if(not isinstance(pack_n, int)): raise ValueError(f'pack_n must be of type int, not {type(pack_n).__name__}')

                super().__init__(packet.tds_s.flag_cont.flag.RTP)

                self.pack_n = pack_n

            def compile(self):
                return partitioner.partition(self.pack_n)

        class psds_don(_psds):
            def __init__(self):
                super().__init__(packet.tds_s.flag_cont.flag.DON)

            def compile(self):
                return None

        def __init__(self, flag_c, *psds_data):
            if(not isinstance(flag_c, packet.tds_s.flag_cont)): raise ValueError(f'flag_c must be of type flag_cont, not {type(flag_c).__name__}')

            self.flag_map = {}
            for flag in flag_c.get_active_flags():
                for data in psds_data:
                    if(not isinstance(data, self._psds)): raise ValueError(f'all data passed for psds_data must be of type _psds, not {type(data).__name__}: {data}')
                    if(data.flag != flag): continue

                    logger.debug(f'found exec for {flag.name}')
                    self.flag_map.update({flag: data})
                    break
                else:
                    logger.warn(f'no exec found for {flag.name}')

            super().__init__()

            logger.debug('packet specific data section setup')

        def compile(self):
            tvals = []
            for flag in self.flag_map.items():
                res = flag[1].compile()
                if(not isinstance(res, partitioner.partition)): 
                    logger.debug(f'{flag[0].name} compile returned non partition value, type {type(res).__name__}')
                    continue
                cmp = res.data()
                tvals.append(cmp)
            return partitioner.partition(*tvals)

    def gen_sis():
        pass

    def __init__(self, tdsec: tds_s, psdsec: psds_s):
        if(not isinstance(tdsec, self.tds_s)): raise ValueError(f'transfer data section must be of type tds_s, not {type(tdsec).__name__}')

        self.tds = tdsec
        self.psds = psdsec

        logger.debug('packet OK')

    @staticmethod
    def create(src: ident, dst: ident, flags: int, req_num: int, tsmp: float = round(datetime.datetime.now().timestamp())):
        tdsec = packet.tds_s(src, dst, flags, tsmp, req_num)
        psdsec = packet.psds_s(tdsec.flags, 
                               packet.psds_s.psds_key('nuhuh', 'helloworldddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd'),
                               packet.psds_s.psds_syn(),
                               packet.psds_s.psds_ack(),
                               packet.psds_s.psds_sec(packet.psds_s.heads({'hello': 'world'}), 'erm what the sigma'),
                               packet.psds_s.psds_urg(),
                               packet.psds_s.psds_nsc(packet.psds_s.heads({'uh': 'no', 'uhh': 'yes'}), 'uh idk maybe'),
                               packet.psds_s.psds_rtp(0),
                               packet.psds_s.psds_don())
        pack = packet(tdsec, psdsec)
        return pack
