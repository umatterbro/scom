import cfgmgr

class scom:
    def __init__(self, config_mgr: cfgmgr.config_manager):
        if(not isinstance(config_mgr, cfgmgr.config_manager)): raise ValueError(f'Config manager must be type of cfgmgr.config_manager, not {type(config_mgr).__name__}')
        self.config_mgr = config_mgr
