class TilesetManifest:
    def __init__(self,
                 name: str,
                 minzoom: int,
                 maxzoom: int,
                 attribution: str):
        self.name = name
        self.minzoom = minzoom
        self.maxzoom = maxzoom
        self.attribution = attribution
