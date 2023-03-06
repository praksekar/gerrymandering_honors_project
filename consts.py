import os
from matplotlib.colors import ListedColormap
from pathlib import Path


PROJ_ROOT: Path = os.path.dirname(__file__)
STATE_DATA_BASE_DIR: Path = os.path.join(PROJ_ROOT, "state_data")
STATE_GEOMETRY_FILENAME: str = "geometries.gpkg"
STATE_GRAPH_FILENAME: str = "graph.json"
POP_COL: str = "TOTAL"
DISTRICT_NO_COL = "DISTRICTNO"
POP_UPDATER: str = "population"
CUT_EDGE_UPDATER: str = "cut_edges"
DISTINCT_COLORS: ListedColormap = ListedColormap(['#e6194b', '#3cb44b',
'#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c',
'#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3',
'#808000', '#ffd8b1', '#000075', '#808080'])
