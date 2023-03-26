from pathlib import Path


STATE: str = "NY"
PRES_OUTPUT_FILE: Path = None
NUM_RECOM_STEPS: int = 100
EPSILON: float = 0.01
REP_VOTE_TALLY_COL: str = "2020_PRES_DEM"
DEM_VOTE_TALLY_COL: str = "2020_PRES_REP"
VOTING_MODEL: str = None