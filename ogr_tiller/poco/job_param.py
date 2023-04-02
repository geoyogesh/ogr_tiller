class JobParam:
    def __init__(self,
                 mode: str,
                 data_folder: str,
                 cache_folder: str,
                 port: str,
                 disable_caching: bool):
        self.mode = mode
        self.data_folder = data_folder
        self.cache_folder = cache_folder
        self.port = port
        self.disable_caching = disable_caching
