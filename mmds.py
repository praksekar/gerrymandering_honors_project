import gerrychain
from pptx import Presentation
from gerrychain.accept import always_accept
from functools import partial
import random
from gerrychain import constraints, Graph, Partition, MarkovChain
from gerrychain.updaters import cut_edges, Tally
from gerrychain.tree import random_spanning_tree
import geopandas as gp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from geopandas import GeoSeries, GeoDataFrame
import networkx as nx


SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
PRES_FILE = "./pres_output/mmd_recom1"
SMD_ASSIGNMENT_COL = "CD_2011"
MARKOV_CHAIN_STEPS = 100
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])


plt.figure(figsize=(13.0, 8.0))  
def add_plot_to_pres(prs):
    # plt.title("Markov chain step: %d" % step_no)
    plt.savefig("/tmp/graph.png")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture("/tmp/graph.png", 0, 0)
    print("slide added")


def plot_partition(partition: Partition, precinct_geometries: GeoSeries, prs, show=False, cmap=COLORS):
    partition.plot(precinct_geometries, cmap=cmap)
    centroids : dict[tuple] = get_district_centroids(partition, precinct_geometries)
    total_pop = get_total_pop(partition)
    for partID, coord in centroids.items():
        pop_frac = float(partition["population"][partID]/total_pop) * 18
        plt.text(coord[0], coord[1], "District %d\nPopulation: %d\nPop Frac: %3f/18" % (partID, partition["population"][partID], pop_frac))
    if prs is not None:
        add_plot_to_pres(prs)
    if show:
        plt.show()


def count_components(G: nx.Graph) -> int:
    components = [c for c in nx.connected_components(G)]
    return len(components), components


def split_graph(graph: nx.Graph, partIDs: tuple, graph_pop: int, pop_target: int, epsilon: float, cut_iterations: int = 100, node_repeats: int = 100) -> dict[int, int]:
    pop_rng = (pop_target * (1 - epsilon), pop_target * (1 + epsilon))
    for i in range(node_repeats):
        # graph = graph.copy()
        spanning_tree = random_spanning_tree(graph)
        edges_left = set(spanning_tree.edges)
        for j in range(len(edges_left)):
            random_edge = random.choice(list(edges_left))
            spanning_tree.remove_edge(random_edge[0], random_edge[1])
            pop_sum = 0
            components = [c for c in nx.connected_components(spanning_tree)]
            for nodeID in components[0]:
                pop_sum += int(graph.nodes[nodeID][POP_COL])
            if pop_rng[0] <= pop_sum <= pop_rng[1] or pop_rng[0] <= graph_pop-pop_sum <= pop_rng[1]:
                flips = {}
                for idx, component in enumerate(components):
                    for nodeID in component:
                        flips[nodeID] = partIDs[idx]
                print("finished recom after %d iterations" % ((i+1)*(j+1)))
                return flips
            spanning_tree.add_edge(random_edge[0], random_edge[1])
            edges_left.remove(random_edge)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def mmd_recom(partition: Partition):
    edge = random.choice(tuple(partition["cut_edges"]))
    parts_to_merge = (partition.assignment[edge[0]], partition.assignment[edge[1]])
    print("doing recom on districts %d, %d" % (parts_to_merge[0], parts_to_merge[1]))
    print("part 1 components: %d, part 2 components: %d" % (count_components(partition.graph.subgraph(partition.parts[parts_to_merge[0]])), count_components(partition.graph.subgraph(partition.parts[parts_to_merge[1]]))))
    subgraph = partition.graph.subgraph(
        list(partition.parts[parts_to_merge[0]]) + list(partition.parts[parts_to_merge[1]])
    )
    print("subgraph components = %d" % count_components(subgraph))
    subgraph_pop = partition["population"][parts_to_merge[0]] + partition["population"][parts_to_merge[1]] 
    pop_target = partition["population"][parts_to_merge[0]] 
    flips = split_graph(graph=subgraph.graph, partIDs=parts_to_merge, graph_pop=subgraph_pop, pop_target=pop_target, epsilon=0.1)
    return partition.flip(flips)


def get_total_pop(partition: Partition, pop_col=POP_COL):
    total_pop = 0
    for partID, nodeIDs in partition.parts.items():
        for nodeID in nodeIDs:
            total_pop += int(partition.graph.nodes[nodeID][pop_col])
    return total_pop


def gen_mmd_configs(smd_partition: Partition) -> list[tuple]:
    n_reps = len(smd_partition.parts)
    configs = []
    for x1 in range(n_reps//3+1):
        for x2 in range(n_reps//4+1):
            for x3 in range(n_reps//5+1):
                if x1*3 + x2*4 + x3*5 == n_reps:
                    configs.append((x1, x2, x3))
    return configs


def get_district_centroids(partition: Partition, precinct_geometries: GeoSeries) -> dict[int, tuple]:
    district_centroids = {}
    for part, nodes in partition.parts.items():
        part_geometries = precinct_geometries.loc[precinct_geometries.index[list(nodes)]]
        district_centroids[part] = tuple(part_geometries.unary_union.centroid.coords)[0]
    return district_centroids


def gen_district_graph(partition: Partition) -> nx.Graph:
    edgelist = []
    for edge in partition["cut_edges"]:
        edgelist.append((partition.assignment[edge[0]], partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def partition_district_graph(G: nx.Graph, component_sizes: tuple, cut_iterations: int = 100000, node_repeats: int = 5) -> nx.Graph:
    nparts: int = sum(component_sizes)
    for _ in range(node_repeats):
        spanning_tree: nx.Graph = nx.random_spanning_tree(G)
        for _ in range(cut_iterations):
            random_edges: list[tuple] = random.sample(list(spanning_tree.edges), nparts-1)
            spanning_tree.remove_edges_from(random_edges)
            sizes = [len(component) for component in nx.connected_components(spanning_tree)]
            if sizes.count(3) == component_sizes[0] and sizes.count(4) == component_sizes[1] and sizes.count(5) == component_sizes[2]:
                return spanning_tree
            spanning_tree.add_edges_from(random_edges)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def gen_mmd_assignment(smd_partition: Partition, partitioned_district_graph: nx.Graph) -> Partition:
    new_assignment = {}
    district_counter = 0
    for component in nx.connected_components(partitioned_district_graph):
        for part_node in component:
            for precinct_node in smd_partition.parts[part_node]:
                new_assignment[precinct_node] = district_counter
        district_counter += 1
    return new_assignment


def main() -> None:
    # precinct_graph: gerrychain.Graph = Graph.from_json(GRAPH_FILE)
    # precinct_geometries: GeoSeries = gp.GeoSeries.from_file(SHAPE_FILE)
    precinct_geo_df: GeoDataFrame = gp.GeoDataFrame.from_file(SHAPE_FILE)
    precinct_geometries: GeoSeries = precinct_geo_df["geometry"]
    # for geometry in precinct_geometries:
    #     print(geometry.geom_type)
    precinct_graph: gerrychain.Graph = Graph.from_geodataframe(dataframe=precinct_geo_df)
    print(precinct_geo_df)
    # print(len(precinct_geo_df))
    # print(len(precinct_graph.nodes))
    # print(len(precinct_geometries))
    smd_partition: Partition = Partition(precinct_graph, assignment=SMD_ASSIGNMENT_COL)
    smd_graph: nx.Graph = gen_district_graph(smd_partition)
    mmd_configs: list[tuple] = gen_mmd_configs(smd_partition)
    mmd_config = mmd_configs[0]
    print("mmd config: %s" % str(mmd_config))
    district_partition = partition_district_graph(smd_graph, mmd_config)
    mmd_partition = Partition(
        precinct_graph, 
        assignment=gen_mmd_assignment(smd_partition, district_partition),
        updaters={"cut_edges": cut_edges, "population": Tally(POP_COL, "population")} 
    )

    prs = Presentation()
    plot_partition(smd_partition, precinct_geometries, prs=None, show=False)
    for partID, subgraph in smd_partition.subgraphs.items():
        n, components = count_components(subgraph)
        if n > 1:
            print("SMD District %d components: %d" % (partID, n))
            print("components = " + str(components))
            comp_size = 9999999
            for component in components:
                if len(component) < comp_size:
                    min_comp = component
            print("min_comp = " + str(min_comp))
            df = precinct_geo_df.loc[list(min_comp)]
            # for nodeID in min_comp:
            df.plot(color="#000000")
    plt.show()


    for partID in mmd_partition.parts:
        print("MMD District %d components: %d" % (partID, count_components(mmd_partition.graph.subgraph(mmd_partition.parts[partID]))))
    
    proposal = partial(mmd_recom)

    pop_constraint = constraints.within_percent_of_ideal_population(mmd_partition, 0.5)

    chain = MarkovChain(
        proposal=proposal,
        constraints=[pop_constraint],
        accept=always_accept,
        initial_state=mmd_partition,
        total_steps=MARKOV_CHAIN_STEPS
    )

    count = 0
    try:
        for partition in chain:
            print("step: %d" % count)
            print("partition components: %d" % count_components(partition.graph))
            plot_partition(partition, precinct_geometries, prs=prs, show=False)
            count += 1
    except KeyboardInterrupt:
        prs.save("%s" % PRES_FILE)
        print("done, saved as %s" % PRES_FILE)
    finally:
        prs.save("%s" % PRES_FILE)
        print("done, saved as %s" % PRES_FILE)


if __name__ == "__main__":
    main()