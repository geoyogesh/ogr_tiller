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

    def __str__(self):
        return f'name: {self.name} minzoom: {self.minzoom} maxzoom: {self.maxzoom} attribution: {self.attribution} extent: {self.extent} tile_buffer: {self.tile_buffer} simplify_tolerance: {self.simplify_tolerance}'

    def __repr__(self):
        return {'name': self.name, 'minzoom': self.minzoom, 'maxzoom': self.maxzoom, 'attribution': self.attribution, 'extent': self.extent, 'tile_buffer': self.tile_buffer, 'simplify_tolerance': self.simplify_tolerance}.__repr__()

