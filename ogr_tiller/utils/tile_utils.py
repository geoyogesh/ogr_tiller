from typing import Any, List, Tuple
import mercantile
import mapbox_vector_tile
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.proj_utils import get_bbox_for_crs
from multiprocessing.pool import ThreadPool as Pool
import multiprocessing

@abort_after(1)
def get_tile(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int, srid: str):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)
    
    if srid != 'EPSG:4326':
        bbox = get_bbox_for_crs("EPSG:4326", srid, bbox)

    def process_layer(lf):
        layer_name, features = lf
        tile = mapbox_vector_tile.encode([
            {
                "name": layer_name,
                "features": features
            }
        ], default_options={'quantize_bounds': bbox})
        return tile
 
    result = b''
    with Pool(multiprocessing.cpu_count() - 1) as pool:
        tiles = pool.map(process_layer, layer_features)
        for tile in tiles:
            result += tile
    return result
