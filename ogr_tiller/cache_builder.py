from multiprocessing.pool import ThreadPool as Pool
import multiprocessing
from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.job_utils import common
from ogr_tiller.utils.ogr_utils import get_features_no_abort, get_tile_json, get_tileset_manifest, get_tilesets
from ogr_tiller.utils.sqlite_utils import cleanup_mbtile_cache, update_cache
from shapely.geometry import box, shape, mapping
from supermercado import edge_finder, uniontiles, burntiles, super_utils
import ogr_tiller.utils.tile_utils as tile_utils

def build_cache(job_param: JobParam):
    # cleanup existing mbtile cache
    cleanup_mbtile_cache(job_param.cache_folder)
    # setup mbtile cache 
    common(job_param)

    tilesets = get_tilesets()
    for tileset in tilesets:
        print('working on tileset: ', tileset)
        manifest: TilesetManifest = get_tileset_manifest()[tileset]
        tilejson = get_tile_json(tileset, job_param.port, manifest)
        bbox = box(*tilejson['bounds'])
        fc = {
            "features": [{"type": "Feature", "geometry": a} for a in [mapping(b) for b in [bbox]]]
        }
        features = [f for f in super_utils.filter_features(fc["features"])]

        print('generating tilelist')
        tiles = []
        for zoom in range(tilejson['minzoom'], tilejson['maxzoom'] + 1):
            print(f'generating tilelist for {zoom} level')
            zoom_tiles = burntiles.burn(features, zoom)
            tiles.extend(zoom_tiles)
        def process_tile(tile):
            x, y, z = tile
            x = x.item()
            y = y.item()
            z = z.item()
            try:
                layer_features, srid = get_features_no_abort(tileset, x, y, z)
                if len(layer_features) == 0:
                    return
                data = tile_utils.get_tile_no_abort(layer_features, x, y, z, srid, manifest.extent)
                update_cache(tileset, x, y, z, data)
            except Exception:
                print(f'error generating tile for {(x, y, z)}')
        print('generating tiles')
        with Pool(multiprocessing.cpu_count() - 1) as p:
            p.map(process_tile, tiles)
        print('completed generating tileset: ', tileset)

