# TODO: Use proper logger for CodeTimer and other diagnostic output
# TODO: set log level from command line argument parsed by argparse
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
# TODO: consider using docker + makefile commands for easy project building and running
# TODO: consider build sequence: create dockerfile to build dependencies and run autopep8 and mypy before successfully building and running