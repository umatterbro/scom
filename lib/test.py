import scom
import cfgmgr
import proto
import partitioner
import base64
import conn
import logger

def pr_val(val, rec_n: int):
    if(partitioner.is_partition(val)):
        vals = partitioner.get_values(val)
        for x in vals:
            pr_val(x, rec_n+1)
    else: print(f'{"-"*rec_n} {val}')

def pr_vals(vals):
    for x in vals:
        pr_val(x, 0)
        print()

src_ident = proto.ident.generate()
pack = proto.packet.create(src_ident, proto.ident.generate(), proto.packet.tds_s.flag_cont.create(key_flag=True), 0)

pack_cmp = pack.compile()
pack_data = pack_cmp.data()
print(f'packet final: {pack_data}\n')

# pack_vals = partitioner.get_values(pack_data)
# pr_vals(pack_vals)

try: con = conn.open(7901, 'epickeyoat')
except ConnectionRefusedError:
    logger.negative('connection refused')
    exit(1)

con.send_packet(pack)
