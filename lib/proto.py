import logger
import datetime
import os
import re
import enum

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
#   * path: undefined len, path to specified resource
#   * data: undefined len, data being received

class ident:
    _MAX_IDENT_LEN = 12
    _IDENT_CHUNK_SIZE = 2
    def __init__(self, bts: bytes):
        if(len(bts) != self._MAX_IDENT_LEN): raise ValueError(f'bts value must be {self._MAX_IDENT_LEN} bytes long, not {len(bts)}')
        nb = [[]]

        for x in range(len(bts)):
            citm = nb[::-1][0]
            if(len(citm) + 1 >= self._IDENT_CHUNK_SIZE and x + 1 < len(bts)): nb.append([])

            ch = hex(bts[x]).lstrip("0x")
            if(len(ch) == 1): ch = '0' + ch
            citm.append(ch)

        self.ident_str = ':'.join(''.join(y for y in x) for x in nb)
        logger.debug(f'ident generated; {self.ident_str}')

    @staticmethod
    def validate(ident_str: str):
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
                if(not isinstance(flag_i, int)): raise ValueError(f'flag integer must be of type int (duh), not {type(flag_i).__name__}')
                binary = bin(flag_i).lstrip('0b')
                binary = ''.join('0' for _ in range(len(self.flag.__members__) - len(binary))) + binary

                self.flags = {}
                for x in range(len(binary)):
                    self.flags.update({self.flag(x): bool(int(binary[x]))})

            def get_flag(self, flag: flag):
                if(not isinstance(flag, self.flag)): raise ValueError(f'flag must be of type flag, not {type(flag).__name__}')
                return self.flags.get(flag)

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
                if(not isinstance(key_flag, bool) or not isinstance(syn_flag, bool) or not isinstance(ack_flag, bool) or not isinstance(sec_flag, bool) or not isinstance(urg_flag, bool) or not isinstance(nsc_flag, bool) or not isinstance(rtp_flag, bool) or not isinstance(don_flag, bool)):
                    raise ValueError(f'all flags must be of type bool')

                fstr = f'0b{int(key_flag)}{int(syn_flag)}{int(ack_flag)}{int(sec_flag)}{int(urg_flag)}{int(nsc_flag)}{int(rtp_flag)}{int(don_flag)}'
                return packet.tds_s.flag_cont(int(fstr, 2))

        def __init__(self, src: ident, dst: ident, flag_i: int | flag_cont, tsmp: float, req_num: int):
            if(not isinstance(src, ident)): raise ValueError(f'source must be of type ident, not {type(src).__name__}')
            if(not isinstance(dst, ident)): raise ValueError(f'destination must be of type ident, not {type(dst).__name__}')

            if(isinstance(flag_i, int)):
                if(flag_i.bit_length() > 8 or flag_i <= 0): raise ValueError(f'flags integer must be > 0 and < 256')
                self.flags = self.flag_cont(flag_i)
            elif(isinstance(flag_i, self.flag_cont)): self.flags = flag_i
            else: raise ValueError(f'flags must be of type int OR flag_cont, not {type(flag_i).__name__}')

            if(isinstance(tsmp, float)): tsmp = round(tsmp)
            if(not isinstance(tsmp, int)): raise ValueError(f'timestamp must be of type int or float, not {type(tsmp).__name__}')

            self.src = src
            self.dst = dst
            self.tsmp = tsmp
            self.req_num = req_num

            super().__init__()
            logger.debug('transfer data section setup')

    class psds_s(section):
        def __init__(self):
            super().__init__()
            logger.debug('packet specific data section setup')

    def __init__(self, tdsec: tds_s):
        if(not isinstance(tdsec, self.tds_s)): raise ValueError(f'transfer data section must be of type tds_s, not {type(tds).__name__}')

        self.tds = tdsec

        logger.debug('packet OK')

    @staticmethod
    def create(src: ident, dst: ident, flags: int, tsmp: float, req_num: int):
        tdsec = packet.tds_s(src, dst, flags, tsmp, req_num)
        pack = packet(tdsec)
        return pack
