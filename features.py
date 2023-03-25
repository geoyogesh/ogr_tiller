import fiona
from shapely.geometry import mapping, shape
import pprint

import fiona.meta
fiona.meta.print_driver_options("GeoJSON")

# Open the shapefile
layers = fiona.listlayers('data/data.gpkg')
for layer_name in layers:
    with fiona.open('data/data.gpkg', 'r', layer=layer_name) as layer:
        pprint.pprint(layer.schema)

        # Create a bounding box
        minx, miny, maxx, maxy = layer.bounds
        bbox = (minx, miny, maxx, maxy)

        count = 0
        features = layer.filter(bbox=bbox)
        for feat in features:
            count += 1
            print(feat) # shape(feat.geometry)
            print(feat.properties)
        print('count: ', count)

    

