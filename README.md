This script takes LANDSAT8 raster data, calculates NVDI and LST, and appends the results to your input GeoJson Linestring features.

To use:

1. Clone this repo.
2. Install UV (https://docs.astral.sh/uv/getting-started/installation/)
3. Run "uv sync"
4. Copy your LANDSAT8 imagery into the /data/ directory. Include bands 4, 5, and 10.
5. Run "uv run parse.py xxx.geojson", where xxx.geojson is you Line Features file.
6. See output in "out.json".


Future work:
1. A better help page.
2. Custom output format.
3. Select different LST calculation methods.
