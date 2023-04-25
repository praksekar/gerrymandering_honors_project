# To do
## Organizational/Quality of Life
### In Progress
    [ ] - initialize VMDPartition without kwargs
    [ ] - Use / syntax instead of os.path.join
    [ ] - figure out how to properly disable external loggers (maybe create my own logger instead of using the root one)
    [ ] - use fstrings instead of modulo strings for printing
    [ ] - use autopep8 linter and configure settings in pyproject.toml
    [ ] - use a testing framework to test parts of program (such as running an election)
    [ ] - set log level from command line argument parsed by argparse
    [ ] - prepend each module function not intended to be used externally with underscore by convention
    [ ] - abstract partition data structures, candidate generation, voting model, and election functions to work regardless of partition type (smd or mmd)
    [ ] - consider using docker + makefile commands for easy project building and running. autopep8 and mypy, for instance, can be invoked during the build sequence
    [ ] - update documentation for functions 
    [ ] - simplify recom to maybe one function and simplify complement_or_not logic; it is very confusing
    [ ] - fix find_cut() because the tuple return format is very confusing
    [ ] - look into caching the gen_ensemble() function (perhaps with @cache decorator)
    [ ] - use pprint in base logger so that all prints are ran through a pprint first
    [ ] - use more custom types in custom_types in py and put them into function annotations
### Finished
[x] - Use proper logger for CodeTimer and other diagnostic output

## Core Functionality
### In Progress
    [ ] - Properly organize all of the data-saving methods into the "load_state_data" module (should be renamed); put "main" code in /bin directory scripts that calls these data-saving methods, such as "save_ensembles"
    [ ] - fix type for mmd choosing strategy function
    [ ] - shouldn't candidates be generated once per district and not for every map?
    [ ] - reimplement voting model as a comparator that works on a ranked choice ballot to sort the votes. Also, make the SMD ballot a ballot with just 2 candidates so that we can use the voting model code for the SMD voting simulations.
    [ ] - change plot split method to be more generic. Given a set of state-wide election results and a some measure, output a graph.
    [ ] - generate hr3863 desired ensembles and max districts ensembles for NY, NC, FL, PA, MD, LA, GA
    [ ] - Use VMDPartition class which extends Partition and adds district_reps field, and change all functions to use it. Then we can simply pass in a VMDPartition with district_reps of all 1 to have the code work for SMD partitions.
    [ ] - Use regular Partition election functions for smd partitions 
    [ ] - Create function to choose mmd config that maximizes the number of 5 districts and minimizes the number of 4 districts desired by H.R. 3863 SEC. 313. E and F: https://www.congress.gov/bill/117th-congress/house-bill/3863/text#H8E776F90310F45FEA20AC3152FBC697E. 
    [ ] - Also check section D for restrictions on the political uniformity of districts
    [ ] - write Slurm script for Seawulf
    [ ] - finish embarrassingly parallel mpi script for generating ensembles
    [ ] - fix rand_spanning_tree method in graph_utils to take in a seed for reproducible output
    [ ] - plot vote-seat share curve (search up Shen Github) proportionality
    [ ] - mmd ranked choice election currently not working. print logger debug statements for every round of vote tabulation. display each candidate and the number of votes currently for that candidate. perhaps caused by pass by reference of ballot array??

## Research Ideas
### In Progress
    [ ] - for modeling, come up with machine learning function f(v) -> c that maps voter profile vector v = ([age, %race, rural/suburban ...]) to desired candidate vector c = ([age, democrat/rep, policy1, policy2]). These vectors should have the same overlapping properties. Compute the vector differences between each prediction c and candidate to get a ranking of candidates for that voter.
    [ ] - consider 3rd parties in elections