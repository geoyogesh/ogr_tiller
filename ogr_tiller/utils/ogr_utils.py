from typing import Any
import fiona
import mercantile
from shapely.geometry import box
from shapely.geometry import shape
import random
import os
from shapely.ops import clip_by_rect
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.proj_utils import get_bbox_for_crs

data_location = None
cached_tileset_names = None


def get_tilesets():
    return cached_tileset_names


def setup_ogr_cache(data_folder):
    # update global variablea
    global data_location, cached_tileset_names
    data_location = data_folder
    cached_tileset_names = []
    dir_list = os.listdir(data_location)
    for file in dir_list:
        if file.endswith('.gpkg'):
            cached_tileset_names.append(file.split('.')[0])


def format_layer_name(name: str):
    return name.lower()


def format_field_name(name: str):
    return name.lower()


def format_field_type(name: str):
    return name.lower()


def get_tile_json(tileset: str, port: str) -> Any:
    result = {
        'tilejson': '3.0.0',
        'id': 'ogr_tiller_tileset',
        'name': 'ogr_tiller_tileset',
        'description': 'OGR Tiller Tileset',
        'version': '1.0.0',
        'attribution': 'UNLICENSED',
        'scheme': 'xyz',
        'tiles': [f'http://localhost:{port}/tilesets/' + tileset + '/tiles/{z}/{x}/{y}.mvt'],
        'minzoom': 0,
        'maxzoom': 22,
        'bounds': None,
        'center': None
    }
    ds_path = os.path.join(data_location, f'{tileset}.gpkg')
    layers = fiona.listlayers(ds_path)

    vector_layers = []
    for layer_name in layers:
        fields = {}
        geometry_type = None
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            result['crs'] = str(layer.crs)
            result['crs_wkt'] = layer.crs_wkt
            schema = layer.schema
            geometry_type = layer.schema['geometry']
            for field_name, field_type in schema['properties'].items():
                fields[format_field_name(field_name)] = format_field_type(field_type)
            
            # layer bounds cannot be computed if layer dont have any features
            try:
                minx, miny, maxx, maxy = layer.bounds
                if result['bounds'] is None:
                    result['bounds'] = [minx, miny, maxx, maxy]
                else:
                    existing_bbox = box(result['bounds'][0],result['bounds'][1],result['bounds'][2],result['bounds'][3])
                    minx_new, miny_new, maxx_new, maxy_new = existing_bbox.union(box(minx, miny, maxx, maxy)).bounds
                    result['bounds'] = [minx_new, miny_new, maxx_new, maxy_new]
            except:
                print(f'error getting bounds for {layer_name}')
        vector_layers.append({
            'id': layer_name,
            'fields': fields,
            'geometryType': geometry_type
        })
    
    result['vector_layers'] = vector_layers

    # reproject bounds
    if result['crs'] != 'EPSG:4326' and result['bounds'] is not None:
        bounds = get_bbox_for_crs(result['crs'], 'EPSG:4326', result['bounds'])
        result['bounds'] = bounds
        result['center'] = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]
    else:
        result['center'] = None

    return result


def get_starter_style(port: str) -> Any:
    style_json = {
        'version': 8,
        'sources': {},
        'layers': [],
    }

    for tileset in cached_tileset_names:
        style_json['sources'][tileset] = {
            'type': 'vector',
            'url': f'http://0.0.0.0:{port}/tilesets/{tileset}/info/tile.json'
        }

    layer_geometry_types = []
    for tileset in cached_tileset_names:
        ds_path = os.path.join(data_location, f'{tileset}.gpkg')
        layers = fiona.listlayers(ds_path)
        for layer_name in layers:
            with fiona.open(ds_path, 'r', layer=layer_name) as layer:
                layer_geometry_types.append((tileset, layer_name, layer.schema['geometry']))

    geometry_order = ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon', 'Unknown']
    layer_index = 0
    for orderGeometry in geometry_order:
        for tileset, layer_name, geometryType in layer_geometry_types:
            if orderGeometry == geometryType:
                # getting color for layer
                color = get_color(layer_index)
                layer_index += 1
                
                if geometryType == 'Unknown':
                    for g in ['Point', 'LineString', 'Polygon']:
                        style_json['layers'].append(get_layer_style(tileset, color, f'{layer_name}_{g.lower()}', layer_name, g))
                else:
                    style_json['layers'].append(get_layer_style(tileset, color, layer_name, layer_name, orderGeometry))
            
    
    return style_json


def get_layer_style(tileset: str, color: str, layer_name: str, source_layer: str, geometry_type: str) -> Any:
    if geometry_type == 'LineString' or geometry_type == 'MultiLineString':
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': source_layer,
            'filter': ["==", "$type", "LineString"],
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color,
                'line-width': 1,
                'line-opacity': 0.75
            }
        }
    elif geometry_type == 'Polygon' or geometry_type == 'MultiPolygon':
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': source_layer,
            'filter': ["==", "$type", "Polygon"],
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color,
                'line-width': 1,
                'line-opacity': 0.75
            }
        }
    elif geometry_type == 'Point' or geometry_type == 'MultiPoint':
        return {
            'id': layer_name,
            'type': 'circle',
            'source': tileset,
            'source-layer': source_layer,
            'filter': ["==", "$type", "Point"],
            'paint': {
                'circle-color': color,
                'circle-radius': 2.5,
                'circle-opacity': 0.75
            }
        }
    else:
        print('unhandled geometry type')
    return None


def get_color(i: int):
    colors = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'];
    if i < len(colors):
        return colors[i]
    return f"#{''.join([random.choice('0123456789ABCDEF') for i in range(6)])}"


@abort_after(1)
def get_features(tileset: str, x: int, y: int, z: int):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)

    ds_path = os.path.join(data_location, f'{tileset}.gpkg')
    layers = fiona.listlayers(ds_path)
    result = []

    srid = None

    for layer_name in layers:
        processed_features = []
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            srid = layer.crs

            if srid != 'EPSG:4326':
                bbox = get_bbox_for_crs("EPSG:4326", srid, bbox)

            features = layer.filter(bbox=bbox)
            for feat in features:
                processed_geom = clip_by_rect(
                    shape(feat.geometry),
                    bbox[0],
                    bbox[1],
                    bbox[2],
                    bbox[3],
                )
                if z < 13:
                    processed_geom = processed_geom.simplify(0.00005, False)
                processed_features.append({
                    "geometry": processed_geom,
                    "properties": feat.properties
                })
        result.append((layer_name, processed_features))
    return result, srid
    