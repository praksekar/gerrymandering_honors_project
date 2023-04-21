from pathlib import Path
from src.custom_types import VotingComparator
from src.modules.voting_models import party_line_voting_comparator
from src.modules.mmd_seed_generation import pick_HR_3863_desired_mmd_config, pick_max_districts_config
import logging


LOGGING_LEVEL = logging.DEBUG
# STATE: str = "NY"
PRES_OUTPUT_FILE: Path = None
SMD_NUM_RECOM_STEPS: int = 10
MMD_NUM_RECOM_STEPS: int = 5
SMD_ENSEMBLE_SIZE: int = 10
MMD_ENSEMBLE_SIZE: int = 10
SMD_EPSILON: float = 0.01
MMD_EPSILON: float = 0.01
REP_VOTE_TALLY_COL: str = "2020_PRES_DEM"
DEM_VOTE_TALLY_COL: str = "2020_PRES_REP"
VOTING_MODEL: VotingComparator = party_line_voting_comparator
MMD_CONFIG_CHOOSER = pick_HR_3863_desired_mmd_config