import os
import subprocess


def run_in_sequence(reset=False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # if this is not the first function, wait for the previous function to finish
            if wrapper.prev_func is not None:
                wrapper.prev_func()
            # run the function
            result = func(*args, **kwargs)
            # set this function as the previous function for the next function to use
            wrapper.prev_func = func
            # return the function result
            return result
        if reset:
            wrapper.prev_func = None
        return wrapper
    return decorator


@run_in_sequence(reset=True)
def mk_inp():
    base_dir = './base'
    xyz_dir = './xyz'
    inp_dir = './inp'
    os.makedirs(inp_dir, exist_ok=True)

    xyz_list = []
    for xyz in os.listdir(xyz_dir):
        if xyz.endswith('.xyz'):
            xyz_list.append(xyz)

    base_list = []
    for base in os.listdir(base_dir):
        if base.endswith('.gjf'):
            base_list.append(base)

    for base in base_list:
        with open(os.path.join(base_dir, base)) as b:
            origin = b.read()
            for xyz in xyz_list:
                with open(os.path.join(xyz_dir, xyz)) as x:
                    coord = x.readlines()[2:]
                    coord = ''.join(coord)
                    inp = origin.replace('REPLACE', coord)
                    RAS_dir = os.path.join(inp_dir, base[:-4])
                    os.makedirs(RAS_dir, exist_ok=True)
                    RAS_inp = xyz[:-4] + '.gjf'
                    with open(os.path.join(RAS_dir, RAS_inp), 'w') as r:
                        r.write(inp)


@run_in_sequence(reset=True)
def mk_qsh():
    template = """#!/bin/sh
#PBS -N test
#PBS -j oe
#PBS -o test.log
#PBS -e test.err
#PBS -l pmem=24gb
#PBS -l walltime=96:00:00
#PBS -l nodes=1:ppn=4
#PBS -q batch

TS1=`echo "$PBS_JOBID" | tr -d '[]'`

export OMP_NUM_THREADS=4
export GAUSS_SCRDIR=/tmp

cd $PBS_O_WORKDIR

g16 test.gjf test.out

rm -rf $GAUSS_SCRDIR/$TS1
"""
    for root, dirs, files in os.walk("./inp"):
        for file in files:
            if file.endswith(".gjf"):
                job_name = file[:-4]
                qsh_file_name = os.path.join(root, job_name + ".qsh")

                with open(qsh_file_name, "w") as qsh_file:
                    qsh_file.write(template)

                with open(qsh_file_name, "r+") as qsh_file:
                    data = qsh_file.read().replace("test", job_name)
                    qsh_file.seek(0)
                    qsh_file.write(data)
                    qsh_file.truncate()


def submit():
    for subdir in os.listdir('./inp'):
        subdir_path = os.path.join('./inp', subdir)
        if os.path.isdir(subdir_path):
            os.chdir(subdir_path)
            for job in os.listdir('.'):
                if job.endswith('.qsh'):
                    subprocess.check_output(['qsub', job])
            os.chdir('../../')

    print("Jobs submitted successfully.")


# ===================================
mk_inp()
mk_qsh()
submit()

###
