class JobParam:
    def __init__(self,
                 mode: str,
                 data_folder: str,
                 cache_folder: str,
                 stylesheet_folder: str,
                 port: str,
                 disable_caching: bool,
                 tile_timeout: int):
        self.mode = mode
        self.data_folder = data_folder
        self.cache_folder = cache_folder
        self.stylesheet_folder = stylesheet_folder
        self.port = port
        self.disable_caching = disable_caching
        self.tile_timeout = tile_timeout
