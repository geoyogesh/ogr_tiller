from typing import Any, List, Tuple
import mercantile
import mapbox_vector_tile
from ogr_tiller.utils.fast_api_utils import abort_after


@abort_after(1)
def get_tile(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)
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