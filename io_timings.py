'''
Functions to read/write benchmark data to file

The timings are extracted from the logfiles and stored in JSON files,
ready to be uploaded to the git.
The name of the file is: timings_<system>_<testname>.txt
The file contains a table with several columns:
   benchmark date, short commit hash, resolution, number of nodes, list of total execution times
'''

import os
import subprocess
import json
import numpy as np

# -------- Helper functions -----------

''' Dissect name of the base benchmark directory:
    benchmark_<branch>_<run date>_<commit>/<testname> '''
def get_info_from_benchmark_dir_name(benchmark_dir):
    parts = benchmark_dir.split('/')
    test_name = parts[-1]
    commit = parts[-2][-8:]    # last 8 characters
    #date = parts[-2][-19:-9]   # 10 characters YYYY-MM-DD before commit
    #branch = parts[-2][10:-20] # located between the word benchmark and date
    date = 'xxxx-xx-xx'
    branch = parts[-2][10:-9]
    return branch, date, commit, test_name

''' Dissect name of the benchmark configuration subdirectory:
    nodes<N>_<resolution>_omp<threads> '''
def get_info_from_subdir_name(subdir):
    [nodes, reso, omp] = subdir.split('_')
    nodes = int(nodes[5:])
    reso = reso[4:]
    omp = omp[3:]
    return nodes, reso, omp

# -------- database IO -----------

''' Write data to disk as a structured JSON list '''
def write_data(benchmark_file, data):
    with open(benchmark_file, 'w') as f:
        json.dump(data, f, indent=4)
    print("Updated", benchmark_file)

'''' Load previous data from JSON file '''
def load_data(benchmark_file):
    try: 
        with open(benchmark_file, 'r') as f:
            data= json.load(f)
    except FileNotFoundError:
        print(benchmark_file,"not found. No data to load.")
        data = []
    return data

def add_data(data, benchmark_dir, which='total'):
    """Extract new benchmark data and add it to the dataset efficiently."""
    branch, date, commit, test_name = get_info_from_benchmark_dir_name(benchmark_dir)

    if(not os.path.isdir(benchmark_dir)):
        return data

    # list subdirectories in benchmark test
    for item in os.listdir(benchmark_dir):
        name = os.path.join(benchmark_dir, item)
        if os.path.isdir(name) and item.startswith('nodes'):
            nodes, reso, omp = get_info_from_subdir_name(item)
            total_times = get_timings_from_log(name, which)

            new_entry = {
                "branch": branch,
                "date": date,
                "commit": commit,
                "nodes": int(nodes),
                "resolution": reso,
                "omp_threads": int(omp),
                "timings": total_times
            }
            new_header_keys = sorted(list(new_entry.keys()))
        
            '''# Check if the same entry already exists and update it
            for entry in data:
                # check if the same meta data is present
                old_header_keys = sorted(list(entry.keys()))
                if new_header_keys != old_header_keys:
                    continue
                # check if metadata is the same
                match = True
                new_header_keys.remove('timings')
                for key in new_header_keys:
                    match = match and (entry[key]==new_entry[key])
                if match:
                    # entry exists -> update it by merging lists
                    entry['timings'] = entry['timings'] + total_times
                else:
                    # entry does not exist -> add the new entry'''
            data.append(new_entry)

    return data

'''def filter_data(data, omp_threads=None, nodes=None, commit=None):
    """Filter data based on OpenMP threads, number of nodes, or commit hash."""
    return [entry for entry in data if 
            (omp_threads is None or entry['omp_threads'] == omp_threads) and
            (nodes is None or entry['nodes'] == nodes) and
            (commit is None or entry['commit'] == commit)]'''



def get_timings_from_log(run_dir, which='total'):
    ''' Use grep to get the times from all logfiles in a directory '''
    if which=='total':
        subprocess.call("grep --no-filename 'Total elapsed time' {}/*.log".format(run_dir) +" | awk '{print $4}' > total_time.txt", shell=True)
        with open('total_time.txt', 'r') as file:
            total_time = [float(line.strip()) for line in file]
    else:
        total_time = get_specific_timer(run_dir, which)
    return total_time


def read_timers(logfile):
    ''' retrieve timer for individual parts of the code from the end of the logfile '''
    # get timers that are printed inbetween pattern TIMER and TOTAL
    subprocess.call("awk '/TIMER/{flag=1; next}/TOTAL/{flag=0} flag' " + logfile +" | awk '{print $2}' > indiv_times.txt", shell=True)
    subprocess.call("awk '/TIMER/{flag=1; next}/TOTAL/{flag=0} flag' " + logfile +" | awk '{print substr($0,91,104)}' | sed 's/ //g' > timer_names.txt", shell=True)
    # read data and put into dict
    indiv_times = np.loadtxt('indiv_times.txt')
    timer_names = np.genfromtxt('timer_names.txt',dtype='str')
    timings = {}
    for timer_name, indiv_time in zip(timer_names, indiv_times):
        timings[timer_name] = indiv_time
    # add total time
    #subprocess.call("grep --no-filename 'Total elapsed time' {}".format(logfile) +" | awk '{print $4}' > total_time.txt", shell=True)
    #total_time = np.loadtxt('total_time.txt', unpack=True)
    #timings['total'] = total_time
    return timings


def get_specific_timer(test_dir, which):
    # go through all files
    all_timers = []
    for item in os.listdir(test_dir):
        if item.endswith('.log'):
            timers = read_timers(os.path.join(test_dir, item))
            all_timers.append(timers)
    # get the requested one
    final_times = []
    for measurement in all_timers:
        try:
            final_times.append(measurement[which])
        except:
            continue
    return final_times

''' Update the timings with a new benchmark '''
def update_timings(cluster, benchmark_dir):
    branch, date, commit, test_name = get_info_from_benchmark_dir_name(benchmark_dir)
    #database_file = f'data_{branch}/timings_{cluster}_{test_name}.json'
    database_file = f'data_wip/timings_{cluster}_{test_name}.json'
    # load existing database
    data = load_data(database_file)
    # add/update benchmark entry
    data = add_data(data, benchmark_dir)
    # update file
    write_data(database_file, data)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description="Extract benchmark timings and save to file.")
    parser.add_argument('cluster', help="HPC system on which the benchmark has been run")
    parser.add_argument('benchmark_dir', help="test directory where the benchmarks have been executed")
    args = parser.parse_args()

    update_timings(args.cluster, args.benchmark_dir)
