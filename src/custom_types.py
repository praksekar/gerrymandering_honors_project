from enum import Enum
from gerrychain import Partition, Graph
from gerrychain.updaters import cut_edges, Tally
from geopandas import GeoSeries
from typing import Callable, Dict, List
from pathlib import Path
import io
from io import BufferedReader
import os
import json
import consts
import jsonpickle
import logging
logger = logging.getLogger(__name__)


RepsPerDistrict: type = Dict[int, int]
Assignment: type = Dict[int, int]


class VMDPartition(Partition):
    """Class that extends Gerrychain Partition, adding a dict field mapping
    districts to the number of representatives in that district"""

    district_reps: RepsPerDistrict
    seed_type: str

    def __init__(self, district_reps: RepsPerDistrict, seed_type: str, *args, **kwargs):
        self.district_reps = district_reps
        super(VMDPartition, self).__init__(*args, **kwargs)
    
    def flip(self, flips): # needed because original flip method won't copy over district_reps field, clean this up
        return self.__class__(parent=self, flips=flips, district_reps=self.district_reps) 
    
    @staticmethod
    def from_file(json_file: Path, graph_file: Path, geom_file: Path=None) -> VMDPartition:
        logger.info(f"loading VMDPartition from {json_file}")
        prec_graph: Graph = Graph.from_json(graph_file) 
        vmd_info: dict = jsonpickle.decode(open(json_file, "r").read())
        if geom_file:
            prec_graph.geometry = GeoSeries.from_file(geom_file) 
        return VMDPartition(graph=prec_graph, assignment=vmd_info.assignment, district_reps=vmd_info.district_reps, updaters={consts.CUT_EDGE_UPDATER: cut_edges, consts.POP_UPDATER: Tally(consts.POP_COL, consts.POP_UPDATER)})

    def to_file(self, file: Path) -> str:
        logger.info(f"saving VMDPartition to {file}")
        json.dump(self.to_json(), open(file, "w+"))

    def to_json(self) -> str:
        return jsonpickle.encode({ "assignment": self.assignment, "district_reps": self.district_reps })

    def __repr__(self): 
        number_of_parts = len(self)
        s = "s" if number_of_parts > 1 else ""
        return "<%s [%d part%s], district reps: %s>" % (self.__class__.__name__, number_of_parts, s, str(self.district_reps))


class Party(Enum):
    """Enum to represent each political party participating in an election."""

    DEMOCRAT = 1
    REPUBLICAN = 2


class Candidate:
    """Class representing an election candidate."""

    party: Party
    name: str
    district: int
    favoritism: int

    def __init__(self, party: Party, name: str, district: int, favoritism: int) -> None:
        self.party = party
        self.name = name
        self.district = district
        self.favoritism = favoritism
    
    def __repr__(self) -> str:
        return "party = %s, name = %s, district = %s" % (self.party.name, self.name, self.district)


class Voter:
    """ 
    Class representing the profile of a voter. Currently, this class only
    contains information about the voter's party affiliation, but this should be
    extended in the future to contain more comprehensive information about the
    voter for more complex voting models.
    """

    party: Party

    def __init__(self, party: Party):
        self.party = party


class Ballot:
    """
    Class that represents the physical ballot a voter casts during a ranked
    election. Each ballot is comprised of a ranked list of candidates. This
    class is generalized to work for both SMD and MMD elections, as we can think
    of an SMD ballot as a special case of a ranked-choice ballot with just two
    candidates.

    Fields:
        choices_left: remaining list of ranked candidates on ballot that have
        not yet been counted in a round of tabulation; the first element will be
        the candidate that this ballot will next count for
        was_transferred: flag to prevent double transfer of the same ballot
        during a surplus tabulation round in which there are multiple winners
        weight: used for summing the vote count for a candidate when this
        ballot is tabulated; is reweighted every surplus tabulation round
    
    Methods:
        curr_choice: returns candidate that this ballot will next count for (0th
        element of choices_left)
        next_continuing_choice: pops candidates from front of choices_left until
        a continuing candidate is at the front; used after each round to
        'transfer' a vote to the next candidate on that ballot
    """

    choices_left: list[Candidate]
    was_transferred: bool = False
    weight: float = float(1)

    def __init__(self, ranked_choices: list[Candidate]) -> None:
        self.choices_left = ranked_choices

    def curr_choice(self) -> Candidate:
        return self.choices_left[0]

    def next_continuing_choice(self, continuing_candidates: set[Candidate]) -> None:
        self.choices_left.pop(0)
        while len(self.choices_left) > 0 and self.choices_left[0] not in continuing_candidates:
            self.choices_left.pop(0)
    
    def __repr__(self) -> str:
        return "choices = %s, weight = %f" % (str(self.choices_left), self.weight)


class Ensemble():
    """
    Class representing an ensemble, or collection of random maps. Contains
    fields to describe parameters used to generate ensemble and helper methods
    for serializing to files.
    """

    maps: list[Partition]
    n_recom_steps: int
    epsilon: float
    seed_type: str

    def __init__(self, maps: list[Partition], n_recom_steps: int, epsilon: float) -> None:
        self.maps = maps
        self.n_recom_steps = n_recom_steps
        self.epsilon = epsilon

    @staticmethod
    def from_file(self, file: Path):
        logger.info(f"loading Ensemble from {file}")
        return jsonpickle.decode(open(file, "r"))

    def to_json(self) -> str:
        return jsonpickle.encode(self)
    
    def to_file(self, file: Path) -> None:
        logger.info(f"saving Ensemble to {file}")
        json.dump(self.to_json(), open(file, "w")) 
    

Precinct: type = Dict[str, int|str]
CurriedVotingComparator: type = Callable[[Candidate, Candidate], int]
VotingComparator: type = Callable[[Candidate, Candidate, Voter], int]
Tabulator: type = Callable[[list[Ballot], list[Candidate], int], list[Candidate]]
ElectionsResults: type = list[list[Candidate]]