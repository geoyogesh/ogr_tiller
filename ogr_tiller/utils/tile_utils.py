from typing import Any, List, Tuple
import mapbox_vector_tile
from ogr_tiller.utils import tile_utils
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.ogr_utils import get_data_location, get_tileset_manifest
from ogr_tiller.utils.proj_utils import get_bbox_for_crs
import morecantile
from shapely.geometry import box, shape
import fiona
from shapely.ops import clip_by_rect, polylabel
import os
import traceback
import warnings
from shapely.wkt import dumps as dump_wkt
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

tms = morecantile.tms.get("WebMercatorQuad")


def check_has_features_layers(layer_features: Tuple[str, List[Any]]):
    result = False
    for layer_name, features in layer_features:
        if len(features) > 0:
            result = True
            break
    return result

def get_tile_descendant_tiles(tileset, seed_x, seed_y, seed_z, max_zoom, result, progress: Progress, progress_task_id):
    def process(
            parent_layer_features: Tuple[str, List[Any]], 
            x: int, y: int, z: int, extent: int, max_zoom: int, result, 
            progress: Progress, progress_task_id):
        if z > max_zoom:
            return

        try:
            # generated features for that level
            bbox_bounds = tms.xy_bounds(morecantile.Tile(x, y, z))
            bbox = (bbox_bounds.left, bbox_bounds.bottom,
                    bbox_bounds.right, bbox_bounds.top)
            bbox_shape = shape(box(*bbox))
            
            unit_distance = unit_pixel_distance(bbox, manifest.extent)
            

            # buffer to vertor tile
            clip_bbox = buffered_bbox(bbox_shape, unit_distance, manifest.tile_buffer)
            clip_bbox_shape = shape(box(*clip_bbox))
            tolerance = unit_distance * manifest.simplify_tolerance
            layer_features = filter_features(parent_layer_features, clip_bbox_shape)
            if not check_has_features_layers(layer_features):
                return


            new_z = z + 1
            new_x = x * 2
            new_y = y * 2
            process(layer_features, new_x, new_y, new_z, extent, max_zoom, result, progress, progress_task_id)
            process(layer_features, new_x + 1, new_y, new_z, extent, max_zoom, result, progress, progress_task_id)
            process(layer_features, new_x, new_y + 1, new_z, extent, max_zoom, result, progress, progress_task_id)
            process(layer_features, new_x + 1, new_y + 1, new_z, extent, max_zoom, result, progress, progress_task_id)

            # print('\t processing', tileset, new_x, new_y, new_z)

            layer_features = process_features(layer_features, clip_bbox, tolerance)
            if not check_has_features_layers(layer_features):
                return
            
            if srid != 'EPSG:3857':
                bbox = get_bbox_for_crs("EPSG:3857", srid, bbox)
            data = tile_utils.encode_tile(layer_features, bbox, extent)
            result.append((tileset, x, y, z, data))

            tile_count = len(result)
            if tile_count < 100 or (tile_count > 100 and tile_count % 100 == 0):
                progress.update(progress_task_id, description=f"{tileset}: Generated {tile_count} tiles")
                
        except Exception as e:
            print('error processing ', tileset, x, y, z)
            print(e)
            traceback.print_exc()

    
    #print('working on seed ', tileset, seed_x, seed_y, seed_z)
    ds_path = os.path.join(get_data_location(), f'{tileset}.gpkg')
    bbox_bounds = tms.xy_bounds(morecantile.Tile(seed_x, seed_y, seed_z))
    bbox = (bbox_bounds.left, bbox_bounds.bottom,
            bbox_bounds.right, bbox_bounds.top)
    bbox_shape = shape(box(*bbox))
    
    manifest: TilesetManifest = get_tileset_manifest()[tileset]
    unit_distance = unit_pixel_distance(bbox, manifest.extent)

    # buffer to vertor tile
    clip_bbox = buffered_bbox(bbox_shape, unit_distance, manifest.tile_buffer)
    tolerance = unit_distance * manifest.simplify_tolerance

    layer_features, srid = get_features(ds_path, clip_bbox)
    # no need to process desending features
    if not check_has_features_layers(layer_features):
        return
    
    process(layer_features, seed_x, seed_y, seed_z, manifest.extent, max_zoom, result, progress, progress_task_id)



@abort_after()
def get_tile(tileset: str, x: int, y: int, z: int, extent: int):
    ds_path = os.path.join(get_data_location(), f'{tileset}.gpkg')
    bbox_bounds = tms.xy_bounds(morecantile.Tile(x, y, z))
    bbox = (bbox_bounds.left, bbox_bounds.bottom,
            bbox_bounds.right, bbox_bounds.top)
    bbox_shape = shape(box(*bbox))

    
    manifest: TilesetManifest = get_tileset_manifest()[tileset]
    unit_distance = unit_pixel_distance(bbox, manifest.extent)

    # buffer to vertor tile
    clip_bbox = buffered_bbox(bbox_shape, unit_distance, manifest.tile_buffer)
    tolerance = unit_distance * manifest.simplify_tolerance

    layer_features, srid = get_features(ds_path, clip_bbox)
    if len(layer_features) == 0:
        return None
    layer_features = process_features(layer_features, clip_bbox, tolerance)
    if not check_has_features_layers(layer_features):
        return  None
    
    if srid != 'EPSG:3857':
        bbox = get_bbox_for_crs("EPSG:3857", srid, bbox)
    data = tile_utils.encode_tile(layer_features, bbox, extent)
    return data
    

def buffered_bbox(bbox_shape, unit_distance: float, buffer: int):
    buffer_distance = unit_distance * buffer
    clip_bbox = bbox_shape.buffer(buffer_distance).bounds
    return clip_bbox

def unit_pixel_distance(bbox, extent: int):
    width = abs(bbox[0] - bbox[2])
    height = abs(bbox[1] - bbox[3])
    distance_meters = max([width, height])
    unit_distance = (1/extent) * distance_meters
    return unit_distance


def make_valid_polygon(polygon):
    if not polygon.is_valid:
        return polygon.buffer(0)
    return polygon


def get_features(ds_path: str, clip_bbox):
    layers = fiona.listlayers(ds_path)
    result = []

    srid = None

    for layer_name in layers:
        processed_features = []
        label_features = []
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            srid = layer.crs
            if srid != 'EPSG:3857':
                clip_bbox = get_bbox_for_crs("EPSG:3857", srid, clip_bbox)

            features = layer.filter(bbox=clip_bbox)
            for feat in features:
                geom = shape(feat.geometry)
                processed_features.append({
                    "geometry": geom,
                    "properties": feat.properties
                })

                if geom.geom_type in ['Polygon', '3D Polygon', 'MultiPolygon', '3D MultiPolygon']:
                    label_point = None
                    if geom.geom_type in ['MultiPolygon', '3D MultiPolygon']:
                        max_area = 0
                        max_polygon = 0
                        polygons = geom.geoms
                        for polygon in polygons:
                            processed_poly = make_valid_polygon(polygon)
                            area = processed_poly.area
                            if area > max_area:
                                max_area = area
                                max_polygon = processed_poly
                        label_point = polylabel(max_polygon)
                    else:
                        label_point = polylabel(make_valid_polygon(geom))

                    label_features.append({
                        "geometry": label_point,
                        "properties": feat['properties']
                    })   
        result.append((layer_name, processed_features))
        if len(label_features) > 0:
            result.append((f'{layer_name}_label', label_features))
    return result, srid

def filter_features(layer_features: Tuple[str, List[Any]], clip_bbox_shape):
    result = []
    for layer_name, features in layer_features:
        filtered_features = []
        for feat in features:
            geom = feat['geometry']
            processed_geom = clip_by_rect(
                geom,
                *clip_bbox_shape.bounds
            )
            if not processed_geom.is_empty:
                filtered_features.append(feat)
        result.append((layer_name, filtered_features))
    return result

def process_features(layer_features: Tuple[str, List[Any]], clip_bbox, tolerance: float):
    result = []
    for layer_name, features in layer_features:
        processed_features = []
        for feat in features:
            geom = feat['geometry']
            processed_geom = clip_by_rect(
                geom,
                *clip_bbox
            )
            processed_geom = processed_geom.simplify(tolerance, False)
            processed_features.append({
                "geometry": processed_geom,
                "properties": feat['properties']
            })
        result.append((layer_name, processed_features))
    return result



def encode_tile(layer_features: Tuple[str, List[Any]], bbox, extent: int):
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
