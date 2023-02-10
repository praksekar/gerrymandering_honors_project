# TODO: Use proper logger for CodeTimer and other diagnostic output
# TODO: update documentation for gen_mmd_seed_assignment() (and many other funcs) as we are now passing in an mmd config
# TODO: encapsulate Partition and mmd_config into the same data structure called MMD_Partition
# TODO: simplify recom to maybe one function and simplify complement_or_not logic; it is very confusing
# TODO: fix find_cut() because the tuple return format is very confusing
# TODO: plot vote-seat share curve (search up Shen Github) proportionality
# TODO: look into caching the gen_ensemble() function (perhaps with @cache decorator)
# TODO: use linter 
# TODO: use a testing framework to test parts of program (such as running an election)
# TODO: fix gen_mmd_seed_assignment to be faster by using modified kruskals to glue together adjacent smd districts
# TODO: for modeling, come up with machine learning function f(v) -> c that maps voter profile vector v = ([age, %race, rural/suburban ...]) to desired candidate vector c = ([age, democrat/rep, policy1, policy2]). These vectors should have the same overlapping properties. Compute the vector differences between each prediction c and candidate to get a ranking of candidates for that voter.
# TODO: prepend each module function not intended to be used externally with underscore by convention
# TODO: abstract partition data structures, candidate generation, voting model, and election functions to work regardless of partition type (smd or mmd)


from __future__ import annotations
from typing import TYPE_CHECKING
from functools import partial
from geopandas import GeoSeries
from gerrychain import Graph, MarkovChain, Partition
from gerrychain.accept import always_accept
from gerrychain.updaters import Tally, cut_edges
from matplotlib.colors import ListedColormap
from pptx import Presentation
import itertools
flatten = itertools.chain.from_iterable
if TYPE_CHECKING:
    from election import Candidate
from election import run_mmd_election
from mmd_seed_generation import gen_mmd_configs, gen_mmd_seed_assignment
from ensemble_generation import mmd_recom
from plotting import plot_partition


SHAPE_FILE = "../state_data/PA/PA.shp"
GRAPH_FILE = "../state_data/PAjson_wo_geometry"
PRES_FILE = "../pres_output/mmd_recom5"
SMD_DISTRICT_ASSIGNMENT_COL = "CD_2011"
PLOT_INTERVAL = 1 
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])


def main() -> None:
    prs = Presentation() # perhaps make this a static variable inside plotting functions

    prec_graph: Graph = Graph.from_json(GRAPH_FILE)
    prec_geometries: GeoSeries = GeoSeries.from_file(SHAPE_FILE)

    smd_partition: Partition = Partition(prec_graph, assignment=SMD_DISTRICT_ASSIGNMENT_COL)
    mmd_config: dict[int, int] = gen_mmd_configs(len(smd_partition.parts))[0]
    print("mmd config: %s" % str(mmd_config))
    mmd_assignment: dict[int, int] = gen_mmd_seed_assignment(smd_partition, mmd_config)

    mmd_partition: Partition = Partition(
        graph=prec_graph, 
        assignment=mmd_assignment,
        updaters={"cut_edges": cut_edges, "population": Tally(POP_COL, "population")},
    )

    #plot_partition(mmd_partition, prec_geometries, prs, mmd_config, cmap=COLORS, show=True)   

    chain = MarkovChain(
        partial(mmd_recom, mmd_config=mmd_config, epsilon=0.01),
        [],
        always_accept,
        mmd_partition,
        total_steps=100
    )

    for partition in chain:
        continue

    plot_partition(partition, prec_geometries, prs=None, district_reps=mmd_config, cmap=COLORS, show=True)

    #prs.save(PRES_FILE)
    # mmd_election_results: set[Candidate] = run_mmd_election(mmd_partition, 1, mmd_config)
    # print(mmd_election_results)


if __name__ == "__main__":
    main()