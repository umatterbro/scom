import socket
import sys

sys.path.insert(1, '../lib/')

import scom
import proto
import cfgmgr

cmgr = cfgmgr.config_manager(file_path='conf.json')
sc = scom.scom(cmgr)

@sc.froute(proto.packet.tds_s.flag_cont.flag.SEC)
def sec_req(packet, data):
    print(f'sec: {packet}, {data}')

sc.accept_forever()
