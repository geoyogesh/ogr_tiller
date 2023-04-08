class TilesetManifest:
    def __init__(self,
                 name: str,
                 minzoom: int,
                 maxzoom: int,
                 attribution: str,
                 extent: int,
                 tile_buffer: int,
                 simplify_tolerance: float):
        self.name = name
        self.minzoom = minzoom
        self.maxzoom = maxzoom
        self.attribution = attribution
        self.extent = extent
        self.tile_buffer = tile_buffer
        self.simplify_tolerance = simplify_tolerance
