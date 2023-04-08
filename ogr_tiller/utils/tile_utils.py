from typing import Any, List, Tuple
import mapbox_vector_tile
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.proj_utils import get_bbox_for_crs
import morecantile

tms = morecantile.tms.get("WebMercatorQuad")


def get_tile_no_abort(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int, srid: str, extent: int):
    bbox_bounds = tms.xy_bounds(morecantile.Tile(x, y, z))
    bbox = (bbox_bounds.left, bbox_bounds.bottom, bbox_bounds.right, bbox_bounds.top)

    if srid != 'EPSG:3857':
        bbox = get_bbox_for_crs("EPSG:3857", srid, bbox)

    result = b''
    for layer_name, features in layer_features:
        tile = mapbox_vector_tile.encode([
            {
                "name": layer_name,
                "features": features
            }
        ], default_options={'quantize_bounds': bbox, 'extents':extent})
        result += tile
    return result

@abort_after(3)
def get_tile(layer_features: Tuple[str, List[Any]], x: int, y: int, z: int, srid: str, extent: int):
    return get_tile_no_abort(layer_features, x, y, z, srid, extent)
