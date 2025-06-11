import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as colorsx
from io_timings import add_data


def load_data_test_refactoring(test, cluster='meluxina', timer='total'):
    bench_home = '/home/tcolman/Dropbox/SPACE/DATA_ARCHIVE'

    data = []
    mapping_commits = {}

    # DEV Reference of public ramses version, before space (Nov 8, 2024)
    data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_HEAD_8c72f569/'+test, which=timer)
    mapping_commits['8c72f569'] = 'dev\n Nov 2024' #'starting\n reference'

    # DEV Reference of public ramses version, after clean up etc (Apr 16, 2025)
    #data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_dev_9c518f8a/'+test, which=timer)
    #mapping_commits['9c518f8a'] = 'dev\n Apr 2025'

    # nbor optims
    data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_refactor_3cube_nbor_utils_e3a620c3/'+test, which=timer)
    mapping_commits['e3a620c3'] = 'nbor\n optims'

    return data, mapping_commits


def load_dat_openmp(test, cluster='meluxina', timer='total'):
    bench_home = '/home/tcolman/Dropbox/SPACE/DATA_ARCHIVE'

    data = []
    mapping_commits = {}

    # full openMP implemenation of sedov, as mushed to ramses-romain
    #data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_openmp_hydro_bis_a0a34a7f/'+test, which=timer)

    # full openMP implemenation of multigrid for cosmo
    data = add_data(data, bench_home+'/'+cluster+'/'+'benchmark_openmp_cosmo_0c73de54/'+test, which=timer)

    return data, mapping_commits


''' Get median time and error bars from the gathered total times printed in the log files '''
def process_times(times):
    if len(times)>0:
        #time = np.median(times)
        time = np.average(times)
        error_min = time-np.min(times)
        error_max = np.max(times)-time
    else:
        time = np.nan
        error_min=0
        error_max=0
    return time, error_min, error_max


''' for making plots for PR'''
def make_table_openmp():

    ''' ----- BENCHMARK SETTINGS ----- '''

    cluster = 'meluxina'
    arr_nodes = [1,2,4,8,16,32,64]
    test='cosmo'
    reso='1024'

    data, mapping_commits = load_dat_openmp(test, cluster='meluxina', timer='poisson-rho')
    print(data)

    ''' ----- PLOT SETTING ----- '''

    # create colors
    cmap = plt.get_cmap('managua')
    cNorm  = colorsx.LogNorm(vmin=1, vmax=max(arr_nodes))
    colorVals = {}
    for val in arr_nodes:#
        colorVals[val] = cmap(cNorm(val))
    #colorVals[1] = 'black'

    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

    ''' ----- MAKE FIGURE ----- '''

    for nodes in arr_nodes:
        times = []
        for omp in [0,2,4,8]:
            for entry in data:
                if entry['resolution']!=reso:
                    continue
                if entry['nodes']!=nodes:
                    continue
                if entry['omp_threads']!=omp:
                    continue
                # reduce time data
                time, error_min, error_max = process_times(entry['timings'])
                times.append(float(time))

        # nodes MPI 2th 4th 8thr gain
        diff = (-1)*(min(times[1],times[2],times[3]) - times[0])/times[0] * 100
        space_report_string = '{} & {:.3f} & {:.3f} & {:.3f}& {:.3f}& {:.1f} \\\\ \\hline'.format(str(nodes).rjust(2),times[0],times[1],times[2],times[3],diff)
        print(space_report_string)



''' for making plots for PR'''
def make_table():

    ''' ----- BENCHMARK SETTINGS ----- '''

    cluster = 'meluxina'
    arr_nodes = [1,2,4,8,16,32,64]
    test='sedov'
    reso='1024'

    #data, mapping_commits = load_data_test_refactoring(test,cluster=cluster,timer='total')
    data, mapping_commits = load_data_test_refactoring(test,cluster=cluster,timer='hydro-godunov')


    ''' ----- PLOT SETTING ----- '''

    # create colors
    cmap = plt.get_cmap('managua')
    cNorm  = colorsx.LogNorm(vmin=1, vmax=max(arr_nodes))
    colorVals = {}
    for val in arr_nodes:#
        colorVals[val] = cmap(cNorm(val))
    #colorVals[1] = 'black'

    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(5,4))

    ''' ----- MAKE FIGURE ----- '''

    for nodes in arr_nodes:
        times = []
        labels = []
        err_min,err_max = [], []
        for entry in data:
            if entry['resolution']!=reso:
                continue
            if entry['nodes']!=nodes:
                continue
            commit = entry['commit']
            # reduce time data
            time, error_min, error_max = process_times(entry['timings'])
            times.append(float(time))
            labels.append(mapping_commits[commit])
            err_min.append(error_min)
            err_max.append(error_max)
            axes.scatter(np.full(len(entry['timings']),mapping_commits[commit]),entry['timings'],marker='o',s=3,color=colorVals[nodes])


        axes.errorbar(labels, times, fmt='x',markersize=10, color=colorVals[nodes])

        diff = (-1)*(times[-1]-times[0])/times[0]*100
        #print(f'performance diff: {diff} %')

        #space_report_string = '{} & {:.3f} & {:.3f} & {:.1f} \\\\ \\hline'.format(str(nodes).rjust(2),times[0],times[-1],diff)
        space_report_string = '{:.3f} & {:.3f} & {:.1f} \\\\ \\hline'.format(times[0],times[-1],diff)
        print(space_report_string)

    axes.tick_params(axis='x', labelrotation=90)
    axes.set_ylabel('time [s]')
    axes.set_title(f'{test} {reso} on {cluster}')
    plt.savefig('check_refactor.png', bbox_inches='tight', dpi=200)
    plt.close()

if __name__ == '__main__':

    make_table_openmp()
    #make_table()