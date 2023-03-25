# ogr_tiler
Serve vector tiles from local spatial data

https://gis.stackexchange.com/questions/41465/generating-geojson-with-python

```
import datetime
import logging
import sys

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


def signed_area(coords):
    """Return the signed area enclosed by a ring using the linear time
    algorithm at http://www.cgafaq.info/wiki/Polygon_Area. A value >= 0
    indicates a counter-clockwise oriented ring.
    """
    xs, ys = map(list, zip(*coords))
    xs.append(xs[1])
    ys.append(ys[1])
    return sum(xs[i] * (ys[i + 1] - ys[i - 1]) for i in range(1, len(coords))) / 2.0


with fiona.open("docs/data/test_uk.shp", "r") as source:

    # Copy the source schema and add two new properties.
    sink_schema = source.schema
    sink_schema["properties"]["s_area"] = "float"
    sink_schema["properties"]["timestamp"] = "datetime"

    # Create a sink for processed features with the same format and
    # coordinate reference system as the source.
    with fiona.open(
        "oriented-ccw.shp",
        "w",
        crs=source.crs,
        driver=source.driver,
        schema=sink_schema,
    ) as sink:
        for f in source:
            try:
                # If any feature's polygon is facing "down" (has rings
                # wound clockwise), its rings will be reordered to flip
                # it "up".
                g = f["geometry"]
                assert g["type"] == "Polygon"
                rings = g["coordinates"]
                sa = sum(signed_area(r) for r in rings)

                if sa < 0.0:
                    rings = [r[::-1] for r in rings]
                    g["coordinates"] = rings
                    f["geometry"] = g

                # Add the signed area of the polygon and a timestamp
                # to the feature properties map.
                f["properties"].update(
                    s_area=sa, timestamp=datetime.datetime.now().isoformat()
                )

                sink.write(f)

            except Exception as e:
                logging.exception("Error processing feature %s:", f["id"])

        # The sink file is written to disk and closed when its block ends.
```