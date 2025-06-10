'''
This script analyses the data produced by the benchmark runs.
The input is the test case name.

Several plots are produced:
  - strong_scaling: shows the speedup in function of the number of nodes.
                    The datapoint show an average of the execution time,
                    while the error bars indicate the variation between timings.
                    Previous measurements are shown in differently colored lines
                    using a colormap. The legend indicates the data of the benchmark.
  - execution_time: show the execution time in function of the benchmark date.
                    The datapoint show an average of the execution time,
                    while the error bars indicate the variation between timings.
                    A curve is drawn for each number of nodes used in the strong scaling.
  - weak_scaling: Shows the parallel efficiency as a function of nodes, keeping the
                  the problem size per node constant.
                  The datapoint show an average of the execution time,
                  while the error bars indicate the variation between timings.
                  Previous measurements are shown in differently colored lines
                  using a colormap. The legend indicates the data of the benchmark.
'''

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as colorsx
from collections import OrderedDict
from io_timings import update_timings, load_data, add_data
from collections import OrderedDict


TAGS = {'9e7b310b':'dev2017-09', # mpi not functioning?
        #'':'dev2018-04',
        #'':'dev2018-10',
        #'':'dev2019-04',
        #'':'dev2019-10',
        #'':'dev2020-04',
        #'':'dev2020-10',
        #'':'dev2021-04',
        #'':'dev2021-10',
        #'7c2b0363':'dev2022-04', # broken
        #'cce4cf97':'dev2022-10', # broken
        'ebcb6769':'dev2023-03',
        '00717e77':'dev2023-10',
        #'d2c4c9e':'dev2024-04', # broken
        '7308417b':'dev2024-10'}
# broken ones all have floating point exeception error

reso_strong = 1024
nodes_strong = [1,2,4,8,16,32,64]


#######################################################################
# Analysis and plotting
#######################################################################

''' Remove or combine data entries '''
def filter_data(data, timescale='long', omp=0):
    merged_data = OrderedDict()

    for entry in data:
        commit = entry[0:8]
        if timescale=='long' and (commit not in TAGS):
            # we just can to plot those points corresponding to tags to get the longterm evolution
            continue

        if commit in TAGS:
            new_entry = TAGS[commit]
        #elif timescale=='medium':
            # we want to plot the evolution per month on the cluster
        #elif timescale=='short':
            # we want to plot each commit individually
        else:
            #Take together timings executed on different day of the same month, for the same commit
            # remove day from entry date
            new_entry = entry[:-3]

        if new_entry not in merged_data:
            merged_data[new_entry] = {}
        for subentry in data[entry]:
            if int(subentry.split()[2])==omp:
                if (subentry not in merged_data[new_entry]):
                    merged_data[new_entry][subentry] = []
                # join lists
                merged_data[new_entry][subentry] += data[entry][subentry]

    # remove empty entries
    keys = list(merged_data.keys())
    for entry in keys:
        if len(merged_data[entry])==0:
            merged_data.pop(entry)

    return merged_data

''' Get average time and error bars from the gathered total times printed in the log files '''
def process_times(total_time):
    if len(total_time)>0:
        # take the average and determine the error
        time = np.sum(total_time) / len(total_time)
        error_min = time-np.min(total_time)
        error_max = np.max(total_time)-time
    else:
        time = np.nan
        error_min=0
        error_max=0
    return time, error_min, error_max

def gather_execution_time_data(data,omp):
    # make an entry for each possible number of nodes
    nodes_strong = range(1,512)
    dates = OrderedDict({n:[] for n in nodes_strong})
    times = OrderedDict({n:[] for n in nodes_strong})
    errors_min = OrderedDict({n:[] for n in nodes_strong})
    errors_max = OrderedDict({n:[] for n in nodes_strong})

    # gather available data
    for entry in data:
        for n in nodes_strong:
            subentry = str(reso_strong)+' '+str(n)+' '+str(omp)
            if subentry in data[entry]:
                time, error_min, error_max = process_times(data[entry][subentry])
                dates[n].append(entry)
                times[n].append(time)
                errors_min[n].append(error_min)
                errors_max[n].append(error_max)

    # remove unused entries
    for n in nodes_strong:
        if dates[n]==[]:
            del dates[n]
            del times[n]
            del errors_min[n]
            del errors_max[n]

    return dates, times, errors_min, errors_max

def gather_strong_scaling_data(data, reso_strong,omp):
    # make an entry for each possible number of nodes
    nodes_strong = range(1,512)
    dates = OrderedDict({n:[] for n in nodes_strong})
    times = OrderedDict({n:[] for n in nodes_strong})
    errors_min = OrderedDict({n:[] for n in nodes_strong})
    errors_max = OrderedDict({n:[] for n in nodes_strong})

    # gather available data
    strong_scaling = OrderedDict()
    for entry in data:
        strong_scaling[entry] = ([],[])
        for n in nodes_strong:
            subentry = str(reso_strong)+' '+str(n)+' '+str(omp)
            if subentry in data[entry]:
                time, error_min, error_max = process_times(data[entry][subentry])
                strong_scaling[entry][0].append(n)
                strong_scaling[entry][1].append(time)

    return strong_scaling


def plot_strong_scaling(data, reso_strong, axes=None, omp=0):

    #gather data for plotting
    strong_scaling = gather_strong_scaling_data(data, reso_strong,omp)
    if not bool(strong_scaling):
        # don't do anything if there is no data
        return

    # create colors
    cmap = plt.get_cmap('gray_r')
    cNorm  = colorsx.Normalize(vmin=-1, vmax=len(strong_scaling)-1)
    colorVals =  []
    for val in range(len(strong_scaling)):
        colorVals.append(cmap(cNorm(val)))
    colorVals.reverse()

    # create figure if none is given
    save_plot=False
    if axes==None:
        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))
        save_plot=True

    # plot all entries as lines
    max_nodes = 1
    for entry, c in zip(strong_scaling,colorVals):
        nodes = strong_scaling[entry][0]
        if len(nodes)==0:
            continue
        max_nodes = max(max_nodes, max(nodes))
        times = strong_scaling[entry][1]
        if times[0] != np.nan:
            speedups = times[0]*np.divide(nodes[0],times)
            axes.plot(nodes, speedups, color=c, label=entry)
            axes.scatter(nodes, speedups, color=c,s=20)

    # plot last entry also as circles
    #if strong_scaling: #if dict is not empty
    #    axes.scatter(nodes, speedups, color=c)
    
    # add ideal scaling line
    axes.plot([1,max_nodes],[1,max_nodes], c=(0.25,0.85,0.25),ls=':', lw=2)

    axes.set_xlabel('number of nodes')
    axes.set_ylabel('speedup')
    axes.set_xscale('log')
    axes.set_yscale('log')
    axes.legend()
    if save_plot:
        plt.savefig('strong_scaling.png', bbox_inches='tight', dpi=200)
        plt.close()


''' Plot of the evolution of execution time for different number of nodes '''
def plot_execution_time(data, axes=None, omp=0, **kwargs):

    #gather data for plotting
    dates, times, errors_min, errors_max = gather_execution_time_data(data,omp)
    nodes_strong = [1,2,4,8,16,32,64]#dates.keys()

    # create colors
    cmap = plt.get_cmap('managua')
    cNorm  = colorsx.LogNorm(vmin=1, vmax=max(nodes_strong)/2.)
    colorVals = {}
    for val in nodes_strong:
        colorVals[val] = cmap(cNorm(val))

    # plot
    save_plot=False
    if axes==None:
        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))
        save_plot=True
    for n in dates.keys():
        axes.errorbar(dates[n], times[n], yerr=[errors_min[n],errors_max[n]], fmt='o', markersize=5,
                     label=str(n)+' nodes', color=colorVals[n], **kwargs)
        # plot a line from the last point to make comparison easier
        axes.plot([dates[n][0],dates[n][-1]], [times[n][-1],times[n][-1]], ls=':', lw=1.3, color=colorVals[n])

    if save_plot:
        axes.set_ylabel('execution time [s]')
        axes.set_yscale('log')
        axes.tick_params(axis='x', labelrotation=90)
        axes.legend()
        plt.savefig('execution_time.png', bbox_inches='tight', dpi=200)
        plt.close()


''' Show evolution of execution time on EuroHPC systems '''
def eurohpc_dashboard(test_name, statistic='time', reso_strong=1024, timescale='short'):

    #euroHPC_systems = ['discoverer', 'karolina', 'meluxina', 'vega',
    #                   'deucalion', 'leonardo', 'lumi', 'marenostrum']
    euroHPC_systems = ['discoverer', 'meluxina','marenostrum',
                       'karolina', 'vega', 'leonardo']

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(10,8), sharey=True, sharex=(statistic=='strong'))

    for cluster, ax in zip(euroHPC_systems, axes.flatten()):
        # load the data and process
        benchmark_file = 'data_openmp/timings_'+cluster+'_'+test_name+'.txt'
        data = load_data(benchmark_file)

        # filter data to keep
        omp=0
        data_f = filter_data(data, timescale,omp=omp)

        if statistic=='time':
            plot_execution_time(data_f, axes=ax,omp=omp)
        elif statistic=='strong':
            plot_strong_scaling(data_f, reso_strong, axes=ax,omp=omp)

        # filter data to keep
        omp=1
        data_f_omp = filter_data(data, timescale,omp=omp)
        if statistic=='time':
            plot_execution_time(data_f_omp, axes=ax,omp=omp, markerfacecolor='none', marker='x')
        #    ax.scatter([],[],color='black',label='MPI')
        #    ax.scatter([],[],color='black',facecolor='none',label='OpenMP '+str(omp))
        #elif statistic=='strong':
        #    plot_strong_scaling(data_f, reso_strong, axes=ax,omp=omp)

        ax.set_title(cluster)

    # fanciness
    if statistic=='time':
        axes[0,0].set_ylabel('execution time [s]')
        axes[1,0].set_ylabel('execution time [s]')
        axes[0,0].set_yscale('log')
        for ax in axes.flatten():
            ax.tick_params(axis='x', labelrotation=90)
            ax.legend()

    #fig.subplots_adjust(wspace=0.1)
    fig.tight_layout()
    plt.savefig(f'eurohpc_dashboard_{statistic}_{test_name}.png', bbox_inches='tight', dpi=200)
    plt.close()


''' (for testing purposes) add locally stored benchmark results to file '''
def make_files():

    bench_home = '/home/tcolman/Dropbox/SPACE/benchmarks/'
    test='sedov'

    cluster = 'marenostrum'
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_24fe23ee_2025-02-17/'+test, test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_b5104a59_2025-02-17/'+test, test)

    cluster = 'meluxina'
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_2025-02-14_c41fffd1/'+test, test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_2025-02-18_c172e905/'+test, test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_2025-02-19_c172e905/'+test, test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_2025-02-19_c3a66c16/'+test, test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_performance_tests_2025-02-19_8543d1bb/'+test, test)

    cluster = 'discoverer'
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_HEAD_2025-02-27_ebcb6769/'+test, test) #dev2023-04
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_HEAD_2025-02-27_00717e77/'+test, test) #dev2023-10
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_HEAD_2025-02-27_7308417b/'+test, test) #dev2024-10

''' (for testing purposes) add locally stored benchmark results to file '''
def manually_add():

    bench_home = '/home/tcolman/Dropbox/SPACE/benchmarks_openmp_progress'
    test='cosmo'
    cluster = 'meluxina'

    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_openmp_2025-03-17_c766fbfc/'+test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_openmp_2025-03-19_c766fbfc/'+test, 'openmp')
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_openmp_2025-03-19_f4f4930a/'+test, 'openmp')
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_openmp_2025-03-19_4b965ce4/'+test, 'openmp_hydro_unigrid')

    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_optimise_gauss_seidel_2025-03-21_09fc6b01/'+test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_optimise_gauss_seidel_2025-03-21_96a6a41b/'+test)
    update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_optimise_gauss_seidel_2025-03-21_34bd4a25/'+test)

    test='cosmo_amr'
    cluster = 'meluxina'
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_dev_2025-03-21_c766fbfc/'+test)
    #update_timings(cluster, bench_home+'/'+cluster+'/'+'benchmark_optimise_gauss_seidel_2025-03-21_34bd4a25/'+test)


def test_database():
    reso='1024'
    test='cosmo'
    #reso='lvl9-10'
    #test='cosmo_amr'
    cluster = 'meluxina'
    benchmark_file = 'data_wip/timings_'+cluster+'_'+test+'.json'
    data = load_data(benchmark_file)
    print(data)

    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

    arr_nodes = [1,2,4]
    for commit in ["c766fbfc", "34bd4a25"]:
        ar_times = []
        ar_err_min = []
        ar_err_max = []
        for nodes in arr_nodes:
            # get requested entries
            filtered_data = [entry for entry in data if 
                             #(entry['omp_threads'] == 0) and
                             (entry['resolution'] == reso) and
                             (entry['nodes'] == nodes) and
                             (entry['commit'] == commit)]
            print(filtered_data)
            # merged timings data
            times = []
            for entry in filtered_data:
                times = times + entry['timings']
            # process timings
            time, error_min, error_max = process_times(times)
            ar_times.append(time)
            ar_err_min.append(error_min)
            ar_err_max.append(error_max)
        print(ar_times)
        #axes.scatter(arr_nodes, ar_times, label=commit)
        axes.errorbar(arr_nodes, ar_times, yerr=[ar_err_min,ar_err_max],
                      fmt='o', markersize=4, label=commit)

    axes.set_ylabel('execution time [s]')
    axes.set_xscale('log')
    axes.set_yscale('log')
    axes.legend()
    plt.savefig('test.png', bbox_inches='tight', dpi=200)
    plt.close()


def performance_test_branch_amr_constants():

    bench_home = '/home/tcolman/Dropbox/SPACE/benchmarks_openmp_progress'
    cluster = 'meluxina'
    arr_nodes = [1,2,4]

    data = []
    for test,reso in zip(['cosmo','cosmo_amr'],['1024','lvl9-10']):

        # load only specific data
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_dev_2025-03-24_c766fbfc/'+test)
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_amr_constants_2025-03-24_13b21384/'+test)

        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

        for commit,branch in zip(["c766fbfc", "13b21384"],["dev","amr_constants"]):
            ar_times = []
            ar_err_min = []
            ar_err_max = []
            for nodes in arr_nodes:
                # get requested entries
                filtered_data = [entry for entry in data if 
                                (entry['branch'] == branch) and
                                (entry['resolution'] == reso) and
                                (entry['nodes'] == nodes) and
                                (entry['commit'] == commit)]
                # merged timings data
                times = []
                for entry in filtered_data:
                    times = times + entry['timings']
                # process timings
                time, error_min, error_max = process_times(times)
                ar_times.append(time)
                ar_err_min.append(error_min)
                ar_err_max.append(error_max)
            #axes.scatter(arr_nodes, ar_times, label=commit)
            axes.errorbar(arr_nodes, ar_times, yerr=[ar_err_min,ar_err_max],
                        fmt='o', markersize=4, label=branch)
            print(ar_times)

        axes.set_ylabel('execution time [s]')
        axes.set_xscale('log')
        axes.set_yscale('log')
        axes.legend()
        plt.savefig(f'performance_{test}_branch_amr_constants.png', bbox_inches='tight', dpi=200)
        plt.close()



def performance_test_branch_openmp_cosmo():

    bench_home = '/home/tcolman/Dropbox/SPACE/benchmarks_openmp_progress'
    cluster = 'meluxina'
    arr_nodes = [1,2,4]

    data = []
    for test,reso in zip(['cosmo','cosmo_amr'],['1024','lvl9-10']):

        # load only specific data
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_dev_2025-03-24_c766fbfc/'+test)
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_openmp_cosmo_2025-03-26_3265b938/'+test)

        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

        for commit,branch in zip(["c766fbfc", "3265b938"],["dev","openmp_cosmo"]):
            ar_times = []
            ar_err_min = []
            ar_err_max = []
            for nodes in arr_nodes:
                # get requested entries
                filtered_data = [entry for entry in data if 
                                (entry['branch'] == branch) and
                                (entry['resolution'] == reso) and
                                (entry['nodes'] == nodes) and
                                (entry['commit'] == commit)]
                # merged timings data
                times = []
                for entry in filtered_data:
                    times = times + entry['timings']
                # process timings
                time, error_min, error_max = process_times(times)
                ar_times.append(time)
                ar_err_min.append(error_min)
                ar_err_max.append(error_max)
            #axes.scatter(arr_nodes, ar_times, label=commit)
            axes.errorbar(arr_nodes, ar_times, yerr=[ar_err_min,ar_err_max],
                        fmt='o', markersize=4, label=branch)
            print(ar_times)

        axes.set_ylabel('execution time [s]')
        axes.set_xscale('log')
        axes.set_yscale('log')
        axes.legend()
        plt.savefig(f'performance_{test}_branch_{branch}.png', bbox_inches='tight', dpi=200)
        plt.close()

def performance_test_iskip():

    bench_home = '/home/tcolman/Dropbox/SPACE/benchmarks_openmp_progress'
    cluster = 'meluxina'
    arr_nodes = [1,2,4,8]

    data = []
    for test,reso in zip(['cosmo','cosmo_amr'],['1024','lvl9-10']):

        # load only specific data
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_dev_2025-03-24_c766fbfc/'+test)
        data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_one_iskip_for_all_2025-03-29_bf9df35e/'+test)

        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

        for commit,branch in zip(["c766fbfc", "bf9df35e"],["dev","one_iskip_for_all"]):
            ar_times = []
            ar_err_min = []
            ar_err_max = []
            for nodes in arr_nodes:
                # get requested entries
                filtered_data = [entry for entry in data if 
                                (entry['branch'] == branch) and
                                (entry['resolution'] == reso) and
                                (entry['nodes'] == nodes) and
                                (entry['commit'] == commit)]
                # merged timings data
                times = []
                for entry in filtered_data:
                    times = times + entry['timings']
                # process timings
                time, error_min, error_max = process_times(times)
                ar_times.append(time)
                ar_err_min.append(error_min)
                ar_err_max.append(error_max)
            #axes.scatter(arr_nodes, ar_times, label=commit)
            axes.errorbar(arr_nodes, ar_times, yerr=[ar_err_min,ar_err_max],
                        fmt='o', markersize=4, label=branch)
            print(ar_times)

        axes.set_ylabel('execution time [s]')
        axes.set_xscale('log')
        axes.set_yscale('log')
        axes.legend()
        plt.savefig(f'performance_{test}_branch_{branch}.png', bbox_inches='tight', dpi=200)
        plt.close()

if __name__ == '__main__':

    #make_files()
    #eurohpc_dashboard('sedov', statistic='time',  timescale='long')

    # maybe cool to have the combo weak-strong scaling plot

    #manually_add()
    #test_database()

    #eurohpc_dashboard('sedov', statistic='time',  timescale='short')
    #eurohpc_dashboard('sedov', statistic='strong', reso_strong=1024, timescale='short')
    #eurohpc_dashboard('cosmo', statistic='time',  timescale='short')
    #eurohpc_dashboard('cosmo', statistic='strong', reso_strong=1024, timescale='short')


    #performance_test_branch_amr_constants()
    #performance_test_branch_openmp_cosmo()
    performance_test_iskip()