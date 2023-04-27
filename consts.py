import os
from matplotlib.colors import ListedColormap
from pathlib import Path


PROJ_ROOT: Path = Path(os.path.dirname(__file__))
STATE_DATA_BASE_DIRPATH: Path = PROJ_ROOT / "state_data"
STATE_GEOMETRY_FILENAME: str = "geometries.gpkg"
STATE_GRAPH_FILENAME: str = "graph.json"
SMD_SEED_DIRNAME: str = "smd_seeds"
MMD_SEED_DIRNAME: str = "mmd_seeds"
SMD_SEED_FILENAME: str = "actual"
POP_COL: str = "TOTAL"
DISTRICT_NO_COL = "DISTRICTNO"
POP_UPDATER: str = "population"
CUT_EDGE_UPDATER: str = "cut_edges"
DISTINCT_COLORS: ListedColormap = ListedColormap(['#e6194b', '#3cb44b',
'#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c',
'#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3',
'#808000', '#ffd8b1', '#000075', '#808080'])


STATE_DIRPATH = lambda state: STATE_DATA_BASE_DIRPATH / state
STATE_GEOMETRY_FILEPATH = lambda state: STATE_DIRPATH(state) / STATE_GEOMETRY_FILENAME
STATE_GRAPH_FILEPATH = lambda state: STATE_DIRPATH(state) / STATE_GRAPH_FILENAME
SMD_SEEDS_DIRPATH = lambda state: STATE_DIRPATH(state) / SMD_SEED_DIRNAME
MMD_SEEDS_DIRPATH = lambda state: STATE_DIRPATH(state) / MMD_SEED_DIRNAME
ENSEMBLE_FILENAME = lambda ensemble: f"{ensemble.seed_type}-{len(ensemble.maps)}-{ensemble.constraints}-{ensemble.n_recom_steps}-{ensemble.epsilon}"
ELECTIONSRESULTS_FILENAME = lambda electionsresults: f"{electionsresults.ensemble_name}-{electionsresults.voting_model}-{electionsresults.tabulator}"
ELECTIONSRESULTS_DIRPATH = lambda state: STATE_DIRPATH(state) / "elections_results"
SMD_ENSEMBLE_DIRPATH = lambda state: STATE_DIRPATH(state) / "smd_ensembles"
MMD_ENSEMBLE_DIRPATH = lambda state: STATE_DIRPATH(state) / "mmd_ensembles"
PLOT_DIRPATH = PROJ_ROOT / "plots"

STATES = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

# def construct_mmd_ensemble_dirname() -> str:
#     return f{}

# def construct_smd_ensemble_dirname() -> str:


# def get_smd_seed_dirpath(state: str) -> Path:
#     return os.path.join(STATE_DATA_BASE_DIR, state)

# def get_mmd_seed_path