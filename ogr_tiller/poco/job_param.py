class JobParam:
    def __init__(self,
                 data_folder: str,
                 cache_folder: str,
                 port: str,
                 disable_caching: bool):
        self.data_folder = data_folder
        self.cache_folder = cache_folder
        self.port = port
        self.disable_caching = disable_caching
