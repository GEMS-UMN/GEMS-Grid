from gemsgrid.grid_align import gems_grid_bounds
from rasterio.crs import CRS
from pyproj import Transformer

level = 6
min_x_src, min_y_src, max_x_src, max_y_src = 347775.0, 5464212.0, 350202.0, 5467809.0

print (min_x_src, min_y_src, max_x_src, max_y_src)
min_x, min_y, max_x, max_y = gems_grid_bounds((min_x_src, min_y_src, max_x_src, max_y_src),level=level, source_crs=CRS.from_epsg(26915))
print (min_x, min_y, max_x, max_y)

source_crs=CRS.from_epsg(26915)
print (source_crs)
ease_crs = CRS.from_epsg(6933)
print (ease_crs)
tranform_coords = Transformer.from_crs(source_crs, ease_crs, always_xy=True).transform
print (tranform_coords)
