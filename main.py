import pynetlogo
from deap import base
from deap import creator
from deap import tools
import lib
import random
import time

def instance_netlogo():
    netlogo = pynetlogo.NetLogoLink(
        gui=False,
        jvm_path=r"C:\Program Files\NetLogo 6.3.0\runtime\bin\server\jvm.dll",
    )

    netlogo.load_model("WolfSheep_NoPlot.nlogo")
    return netlogo

if __name__ == "__main__":

    netlogo = instance_netlogo()
    MAX_SF = 50
    MAX_WF = 100
    MAX_SR = 20
    MAX_WR = 20
    maxes = [MAX_SF, MAX_WF, MAX_SR, MAX_WR]

    # creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -2.0))
    creator.create("FitnessMin", base.Fitness, weights=([-1.0]))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    IND_SIZE = 1

    toolbox = base.Toolbox()
    toolbox.register("res", lib.gen_ind, netlogo)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.res, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxOnePoint)
    toolbox.register("evaluate", lib.fitness_ratio)
    toolbox.register("select", tools.selBest, k=26)
    toolbox.register("mutate", lib.mutate)

    time_lsit = []

    start = time.perf_counter()
    pop = toolbox.population(n=100)
    stop = time.perf_counter()
    time_lsit.append(round(stop-start,2))

    print(f'Finished in {round(stop-start,2)} seconds')
    for x in pop:
        x.fitness.values = toolbox.evaluate(x)

    fits = [ind.fitness.values for ind in pop]

    g = 0
    hof = []
    hof2 = []
    CXPB, MUTPB = 0.5, 0.2

    all_min = []
    all_wolves = []
    all_sheep = []

    while g < 30:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        final_offspring = []
        # Select the next generation individuals
        selected = toolbox.select(pop)
        # Clone the selected individuals
        for z in range(4):
            offspring = list(map(toolbox.clone, selected))
            random.shuffle(offspring)

            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1[0][1], child2[0][1])
                    del child1.fitness.values
                    del child2.fitness.values
                final_offspring.append(child1)
                final_offspring.append(child2)

        final_offspring = final_offspring[:100]

        for ind in final_offspring:
            if random.random() < MUTPB:
                toolbox.mutate(ind, 2, 0.3, maxes)

        start = time.perf_counter()
        for x in final_offspring:
            res, chromosome = lib.run_ind(netlogo, x[0][1])
            x[0][0] = res
            del x.fitness.values
        stop = time.perf_counter()
        time_lsit.append(round(stop - start, 2))
        print(f'Finished in {round(stop - start, 2)} seconds')

        invalid_ind = [ind for ind in final_offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = final_offspring

        fits = [ind.fitness.values[0] for ind in pop]

        lib.prep_res_1_fit(fits, pop, all_min, all_wolves, all_sheep, hof)

    print("Hall of Fame ")
    print(hof)

    print("Tables")

    print("")
    print("MIN")
    for x in all_min:
        print(x)

    print("")
    print("Wolves")
    for x in all_wolves:
        print(x)

    print("")
    print("Sheep")
    for x in all_sheep:
        print(x)

    print("")
    print("Time per generation")
    for x in time_lsit:
        print(x)
