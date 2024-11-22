import scom
import cfgmgr

cmgr = cfgmgr.config_manager(file_path='conf.json')
scm = scom.scom(cmgr)
