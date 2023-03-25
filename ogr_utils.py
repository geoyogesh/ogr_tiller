from typing import Any
import fiona
import pprint
import mercantile
from shapely.ops import cascaded_union
from shapely.geometry import box
from osgeo import osr
from shapely.geometry import shape
import math
import random 

def format_layer_name(name: str):
    return name.lower()

def format_field_name(name: str):
    return name.lower()

def format_field_type(name: str):
    return name.lower()

def get_tile_json() -> Any:
    result = {
        'tilejson': '3.0.0',
        'id': 'ogr_tiller_tileset',
        'name': 'ogr_tiller_tileset',
        'description': 'OGR Tiller Tileset',
        'version': '1.0.0',
        'attribution': 'UNLICENSED',
        'scheme': 'xyz',
        'tiles': ['http://localhost:8080/tileset/tiles/{z}/{x}/{y}.mvt'],
        'minzoom': 0,
        'maxzoom': 22,
        'bounds': None,
        'center': None
    }
    layers = fiona.listlayers('data/data.gpkg')

    vector_layers = []
    for layer_name in layers:
        fields = {}
        with fiona.open('data/data.gpkg', 'r', layer=layer_name) as layer:
            result['crs'] = str(layer.crs)
            result['crs_wkt'] = layer.crs_wkt
            schema = layer.schema
            for field_name, field_type in schema['properties'].items():
                fields[format_field_name(field_name)] = format_field_type(field_type)
            
            minx, miny, maxx, maxy = layer.bounds
            if result['bounds'] is None:
                result['bounds'] = [minx, miny, maxx, maxy]
            else:
                existing_bbox = box(result['bounds'][0],result['bounds'][1],result['bounds'][2],result['bounds'][3])
                minx_new, miny_new, maxx_new, maxy_new = existing_bbox.union(box(minx, miny, maxx, maxy)).bounds
                result['bounds'] = [minx_new, miny_new, maxx_new, maxy_new]

        vector_layers.append({
            'id': layer_name,
            'fields': fields
        })
    
    result['vector_layers'] = vector_layers
    result['center'] = None if result['bounds'] is None else [(result['bounds'][0] + result['bounds'][2]) / 2, (result['bounds'][1] + result['bounds'][3]) / 2]
    return result


def get_starter_style() -> Any:
    styleJson = {
        'version': 8,
        'sources': {
            'vt': {
                'type': 'vector',
                'url': 'http://0.0.0.0:8080/tileset/info/tile.json'
            }
        },
        'layers': [],
    }

    layerGeometryTypes = []
    layers = fiona.listlayers('data/data.gpkg')
    for layer_name in layers:
        with fiona.open('data/data.gpkg', 'r', layer=layer_name) as layer:
            layerGeometryTypes.append((layer_name, layer.schema['geometry']))


    geometryOrder = ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']
    layerIndex = 0
    for orderGeometry in geometryOrder:
        color = getColor(layerIndex)
        for layer_name, geometryType in layerGeometryTypes:
            if orderGeometry == geometryType:
                styleJson['layers'].append(getLayerStyle(color, layer_name, orderGeometry))
        layerIndex += 1
    
    return styleJson



def getLayerStyle(color: str, layer_name: str, geometry_type: str) -> Any: 
        if geometry_type == 'LineString' or geometry_type == 'MultiLineString':
            return {
                'id': layer_name,
                'type': 'line',
                'source': 'vt',
                'source-layer': layer_name,
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
                'source': 'vt',
                'source-layer': layer_name,
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
                'source': 'vt',
                'source-layer': layer_name,
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

def getColor(i: int):
    colors = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'];
    if i < len(colors):
        return colors[i]
    return f"#{''.join([random.choice('0123456789ABCDEF') for i in range(6)])}"

def get_features(x: int, y: int, z: int):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)

    layers = fiona.listlayers('data/data.gpkg')
    result = []
    for layer_name in layers:
        processed_features = []
        with fiona.open('data/data.gpkg', 'r', layer=layer_name) as layer:
            features = layer.filter(bbox=bbox)
            for feat in features:
                processed_features.append({
                    "geometry": shape(feat.geometry),
                    "properties": feat.properties
                })
        result.append((layer_name, processed_features))
    return result
    