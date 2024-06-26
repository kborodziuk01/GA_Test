import sys

import time
import datetime
import pynetlogo
from deap import base
from deap import creator
from deap import tools
import lib
import random
from multiprocessing import Process, Value, Array, Pool, Queue, Pipe, Manager
import threading
import concurrent.futures
import logging
import csv
import math


def wrapper(count, q,log, pop=None):
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(filename=f'.\\logs\\Sub_Process{current_time}.log', level=logging.DEBUG)
    log = logging.getLogger()
    res = instance_netlogo(count,log, pop)

    log.info(f"Trying to put results in Queue  {q}")
    q.put(res)
    return None


def instance_netlogo(count,log, pop=None):
    global netlogo
    log.info(f"Starting a Netlogo session")
    netlogo = pynetlogo.NetLogoLink(
        gui=False,
        jvm_path=r"C:\Program Files\NetLogo 6.3.0\runtime\bin\server\jvm.dll",
    )
    log.info(f"Session started: {netlogo}")
    log.info(f"Loading the model")
    netlogo.load_model("WolfSheep_NoPlot.nlogo")
    log.info(f"Model Loaded")
    result = []

    log.info(f"Running {count} individuals")
    if pop is None:
        for _ in range(count):
            result.append(gen_ind(netlogo))
        log.info(f"Run Completed, attempting to kill workspace")
        try:
            netlogo.kill_workspace()
            log.info(f"workspace killed")
        except:
            log.warning(f"Session couldnt be killed, Exception Raised")
            raise Exception()

        return result
    else:
        for x in pop:

            res, chromosome = run_ind(netlogo, x[0][1])
            x[0][0] = res
            del x.fitness.values
        log.info(f"Run Completed, attempting to kill workspace")
        try:
            netlogo.kill_workspace()
            log.info(f"workspace killed")
        except:
            log.warning(f"Session couldnt be killed, Exception Raised")
            raise Exception()

        return pop


def setup_and_run():
    # set parameters
    netlogo.command("set model-version \"sheep-wolves-grass\"")
    netlogo.command("set initial-number-sheep 100")
    netlogo.command("set initial-number-wolves 50")
    netlogo.command("set grass-regrowth-time 30")

    netlogo.command("setup")
    netlogo.command("repeat 1000 [go]")

    ended = False
    c = 0
    while c < 1000:
        c = int(netlogo.report("ticks"))
        ended = bool(netlogo.report("ended"))
        if ended == True:
            c = 1001
    res = lib.get_results(netlogo)
    return res


def run_ind(netlogo, chromosome):
    lib.init_GA_values(netlogo, chromosome[0], chromosome[1], chromosome[2], chromosome[3])
    res = setup_and_run()

    return [res, chromosome]


def gen_ind(netlogo):
    sf, wf, sr, wr = lib.gen_init_val()

    chromosome = lib.gen_chromosome(sf, wf, sr, wr)

    lib.init_GA_values(netlogo, sf, wf, sr, wr)
    res = setup_and_run()

    return [res, chromosome]


def hamming_distance(string1, string2):
    # Start with a distance of zero, and count up
    distance = 0
    # Loop over the indices of the string
    L = len(string1)
    for i in range(L):
        # Add 1 to the distance if these two characters are not equal
        if string1[i] != string2[i]:
            distance += 1
    # Return the final count of differences
    return distance





def dist(chromosome_list):
    final_str_l = []
    for x in chromosome_list:
        final_str=''
        for y in x:
            final_str = final_str + (bin(y)[2:].rjust(8, "0"))
        final_str_l.append(final_str)

    final_dist = []
    for x in final_str_l:
        ind_dist = []
        for y in final_str_l:
            ind_dist.append(hamming_distance(x, y))
        final_dist.append(sum(ind_dist))

    return sum(final_dist) / len(chromosome_list)




def parallel(process, count, pop=None):
    processes = []
    q = Queue()

    if pop == None:
        for _ in range(process):

            p = Process(target=wrapper, args=([count, q,log]))
            log.info(f"Starting a process {p}")
            p.start()
            processes.append(p)

    else:
        for x in pop:
            p = Process(target=wrapper, args=([count, q,log, x]))
            log.info(f"Starting a process {p}")
            p.start()
            processes.append(p)

    res = []

    for z in processes:
        log.info("Trying to get data from Pipe")
        res.append(q.get())
        log.info("Data Retrived")
        log.info(f"Trying to Join process {z}")
        #p.terminate()
        p.join(False)
        log.info(f"process {z} joined")

    return res


def div_to_pop(fl):
    res = fl.pop(0)
    return res


def select(pop,c):
    random.shuffle(pop)
    clusters = []
    div = int(len(pop) / c)
    for i in range(0, len(pop), div):
        clusters.append(pop[i:i + div])

    clusters_split = []
    for x in clusters:
        new_l = []
        div = int(len(x) / 2 )

        for i in range(0, len(x), div):
            new_l.append(x[i:i + div])
        clusters_split.append(new_l)


    offsprings = []
    for clu in clusters_split:

        first_parent = toolbox.select_2(clu[0])
        second_parent = toolbox.select_2(clu[1])
        first_clone = toolbox.clone(first_parent)
        second_clone = toolbox.clone(second_parent)
        toolbox.mate(first_clone[0][0][1], second_clone[0][0][1])

        del first_clone[0].fitness.values
        del second_clone[0].fitness.values
        offsprings.append(first_clone[0])
        offsprings.append(second_clone[0])


    return offsprings

if __name__ == "__main__":
    global log

    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(filename=f'.\\logs\\main_process_log_{current_time}.log', level=logging.DEBUG)
    log = logging.getLogger()



    log.info("STARTING THE SOFTWARE")
    PROCESSES = 5
    DIV_POP = 20
    MAX_SF = 50
    MAX_WF = 100
    MAX_SR = 20
    MAX_WR = 20
    maxes = [MAX_SF, MAX_WF, MAX_SR, MAX_WR]


    time_lsit = []

    creator.create("FitnessMin", base.Fitness, weights=([-1.0]))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    IND_SIZE = 1

    log.info("Creating initial population of individuals")
    log.info(f"{PROCESSES} cores will be used. Each processing {DIV_POP} individuals")
    start = time.perf_counter()
    generated_individuals = parallel(PROCESSES, DIV_POP)
    stop = time.perf_counter()
    log.info(f"Parallel processing finished in {round(stop - start, 2)} seconds")




    time_lsit.append(round(stop - start, 2))
    print(f'Finished in {round(stop - start, 2)} seconds')

    flattened_individuals = []
    for sub in generated_individuals:
        flattened_individuals.extend(sub)



    log.info("Creating the DEAP Toolbox")
    toolbox = base.Toolbox()
    toolbox.register("res", div_to_pop, flattened_individuals)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.res, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxOnePoint)
    toolbox.register("evaluate", lib.fitness_ratio)
    toolbox.register("select", tools.selBest, k=26)
    toolbox.register("select_new",select)
    toolbox.register("select_2",tools.selBest, k=1)
    toolbox.register("mutate", lib.mutate)

    popu = toolbox.population(n=100)

    for x in popu:
        x.fitness.values = toolbox.evaluate(x)

    fits = [ind.fitness.values for ind in popu]

    g = 0
    hof = []
    hof2 = []
    CXPB, MUTPB = 0.5, 0.2

    all_min = []
    all_wolves = []
    all_sheep = []

    all_distance = []

    while g < 5:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        chro_list = []
        for x in popu:
            chro_list.append(x[0][1])

        distance = dist(chro_list)
        print(distance)
        all_distance.append(distance)

        final_offspring = []
        # Select the next generation individuals

        # selected = toolbox.select(popu)
        # # Clone the selected individuals
        # for z in range(4):
        #     offspring = list(map(toolbox.clone, selected))
        #     random.shuffle(offspring)
        #
        #     for child1, child2 in zip(offspring[::2], offspring[1::2]):
        #         if random.random() < CXPB:
        #             toolbox.mate(child1[0][1], child2[0][1])
        #             del child1.fitness.values
        #             del child2.fitness.values
        #         final_offspring.append(child1)
        #         final_offspring.append(child2)
        #
        # final_offspring = final_offspring[:100]
        #


        for x in range(10):
            final_offspring = final_offspring + toolbox.select_new(popu,5)

        for ind in final_offspring:
            if random.random() < MUTPB:
                toolbox.mutate(ind, 2, 0.3, maxes)

        split = []

        for i in range(0, len(final_offspring), DIV_POP):
            split.append(final_offspring[i:i + DIV_POP])

        start = time.perf_counter()
        split_processed = parallel(PROCESSES, DIV_POP, split)
        stop = time.perf_counter()

        time_lsit.append(round(stop - start, 2))
        print(f'Finished in {round(stop - start, 2)} seconds')

        final_offspring = []
        for sub in split_processed:
            final_offspring.extend(sub)


        invalid_ind = [ind for ind in final_offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        popu[:] = final_offspring

        fits = [ind.fitness.values[0] for ind in popu]

        lib.prep_res_1_fit(fits, popu, all_min, all_wolves, all_sheep, hof)

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

    print("")
    print("Time per generation")
    for x in all_distance:
        print(x)

    rep = []
    head = ["Generation", "Best Fitness", "Best Wolves", "Best Sheep", "Time Elapsed", "Gene Diversity"]
    for x in range(len(all_wolves)):
        rec = [x,all_min[x],all_wolves[x],all_sheep[x],time_lsit[x],all_distance[x]]
        rep.append(rec)

    try:
        with open(f".\\Results\\Report_{current_time}.csv", 'a', newline='') as f:
            write = csv.writer(f)
            write.writerow(head)
            write.writerows(rep)
    except:
        raise Exception()
