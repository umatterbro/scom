import scom
import cfgmgr
import proto
import datetime

cmgr = cfgmgr.config_manager(file_path='conf.json')
scm = scom.scom(cmgr)

src_ident = proto.ident.generate()
pack = proto.packet.create(src_ident, proto.ident.generate(), proto.packet.tds_s.flag_cont.create(key_flag=True), round(datetime.datetime.now().timestamp()), 0)
print(pack.tds.flags.to_int())
