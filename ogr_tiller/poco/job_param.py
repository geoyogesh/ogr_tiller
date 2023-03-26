class JobParam:
    def __init__(self,
                 data_folder: str,
                 cache_folder: str,
                 port: str):
        self.data_folder = data_folder
        self.cache_folder = cache_folder
        self.port = port
