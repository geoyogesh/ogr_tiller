from multiprocessing.pool import ThreadPool as Pool
import multiprocessing
from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.job_utils import common
from ogr_tiller.utils.monitor import timeit
from ogr_tiller.utils.ogr_utils import get_tile_json, get_tileset_manifest, get_tilesets
from ogr_tiller.utils.sqlite_utils import cleanup_mbtile_cache, update_cache, update_multiple_cache
from shapely.geometry import box, shape, mapping
from supermercado import edge_finder, uniontiles, burntiles, super_utils
import ogr_tiller.utils.tile_utils as tile_utils
from rich import print
from rich.progress import Progress, TextColumn, SpinnerColumn

@timeit
def build_cache(job_param: JobParam):
    # cleanup existing mbtile cache
    cleanup_mbtile_cache(job_param.cache_folder)
    # setup mbtile cache 
    common(job_param)

    tilesets = get_tilesets()

    def process_tileset(tileset: str):
        print(f'{tileset}: working on tileset')
        manifest: TilesetManifest = get_tileset_manifest()[tileset]
        tilejson = get_tile_json(tileset, job_param.port, manifest)
        if tilejson['bounds'] is None:
            print(f'{tileset}: skipping tileset because it may be empty')
            return
        bbox = box(*tilejson['bounds'])
        fc = {
            "features": [{"type": "Feature", "geometry": a} for a in [mapping(b) for b in [bbox]]]
        }
        features = [f for f in super_utils.filter_features(fc["features"])]

        print(f'{tileset}: Generating seed tilelist with {tilejson["minzoom"]} level')
        tiles = burntiles.burn(features, tilejson['minzoom'])

        result = []
        
        progress_task_id = progress.add_task(description=f"{tileset}: Generated {len(result)} tiles", total=None)
        def process_tile(tile):
            x, y, z = tile
            x = x.item()
            y = y.item()
            z = z.item()
            tile_utils.get_tile_descendant_tiles(tileset, x, y, z, tilejson["maxzoom"], result, progress, progress_task_id)
        for tile in tiles:
            process_tile(tile)
        
        print(f'{tileset}: number of tiles generated for {tileset} {len(result)}')
        print(f'{tileset}: writing the mbtile files')
        update_multiple_cache(result)
        print(f'{tileset}: completed generating tileset: {tileset}')

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
        with Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(process_tileset, tilesets)
        

