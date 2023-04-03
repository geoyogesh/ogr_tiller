from typing import Any, List, Tuple
import mercantile
import mapbox_vector_tile
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.proj_utils import get_bbox_for_crs


def get_tile_no_abort(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int, srid: str):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)
    
    if srid != 'EPSG:4326':
        bbox = get_bbox_for_crs("EPSG:4326", srid, bbox)
    
    result = b''
    for layer_name, features in layer_features:
        tile = mapbox_vector_tile.encode([
            {
                "name": layer_name,
                "features": features
            }
        ], default_options={'quantize_bounds': bbox})
        result += tile
    return result

@abort_after(1)
def get_tile(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int, srid: str):
    return get_tile_no_abort(layer_features, x, y, z, srid)
