import os
import subprocess
import shutil
import pandas as pd
import time 
from pprint import pprint

'''
Tested on hpc

sub/[EntryNo_A2.zip]
execs/<entryno_a2>.exe : Renamed
scripts/test-id/<scripts>

'''
home_dir: str = os.path.expanduser('~')
scratch_dir: str = os.path.join(home_dir, 'scratch')
execs_dir: str = os.path.join(scratch_dir, 'execs')
sub_dir: str = os.path.join(scratch_dir, 'sub')
script_dir: str = os.path.join(scratch_dir, 'script')
assignment_dir: str = os.path.join(home_dir, 'Assignment2')
students:list = []


if os.path.exists(execs_dir):
    for f in os.listdir(execs_dir):
        students.append(f.split('_')[0])
    students.sort()

    pprint (students)

def create_executables() -> None:
    for folder in os.listdir(sub_dir):
        print (f'Creating exectuable for {folder}')
        if os.path.isdir(os.path.join(sub_dir, folder)):
            path: str = os.path.join(sub_dir, folder)
            executable_path: str = os.path.join(sub_dir, folder, 'a2')
            print ("Trying clean if student wrote ")
            subprocess.run(['make', 'clean', '-C', path])

            if os.path.exists(executable_path):
                print (f'directory content before: {os.listdir(os.path.join(sub_dir, folder))}')
                print (f"Removing executable as it already exists {executable_path}")
                os.remove(executable_path)
                print (f'directory content before: {os.listdir(os.path.join(sub_dir, folder))}')
            print (f"Creating new executable")
            subprocess.run(['make', '-C', path])
            print (f'Make run call finished\n directory content after make {os.listdir(os.path.join(sub_dir, folder))}')
            print ("=="*50)

def save_exec() -> None:
    destination_path: str = execs_dir
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    for folder in os.listdir(sub_dir):
        print (folder)
        if os.path.isdir(os.path.join(sub_dir, folder)):
            info: list = folder.split('_')
            if len(info) < 2:
                print (folder)
                continue
            student_entry_no: str = info[1]
            source_path: str = os.path.join(sub_dir, folder, 'a2')
            if not os.path.exists(source_path):
                continue
            destination_path: str = os.path.join(execs_dir, f'{student_entry_no}_a2')
            print (source_path, destination_path)
            if os.path.exists(destination_path):
                print (f'Removing already existing files at {destination_path}')
                os.remove(destination_path)
            shutil.copy(source_path, destination_path)
   
def generate_pbs_script(
		test_id, student_id, 
		executable_location, 
		nodes, cpus, walltime, 
		taskid, input_path, 
		header_path, 
		output_path, verbose, 
		startk, endk, p) -> None:
    print (f''' test_id = {test_id}, student_id = {student_id}, 
		executable_location = {executable_location}, 
		nodes = {nodes}, cpus = {cpus}, 
		walltime={walltime}, taskid = {taskid},
    		input_path = {input_path}, 
		header_path = {header_path}, 
		output_path = {output_path}, verbose = {verbose}
		startk = {startk}, endk= {endk}, p = {p}
	    ''')
    err_out_path:str = os.path.join(scratch_dir, f'test{test_id}_output_extra') 
    pbs_script = \
f'''#!/bin/bash
#PBS -N autograder_{student_id}
#PBS -l select={nodes}:ncpus={cpus}:mpiprocs=1
#PBS -l place=scatter
#PBS -l walltime={walltime}
#PBS -o {err_out_path}/{student_id}_output.out
#PBS -e {err_out_path}/{student_id}_error.err
### PBS -l software=c++

module purge
module load compiler/gcc/9.1/openmpi/4.0.2

### export NODES=`cat ${{PBS_NODEFILE}}|sort|uniq|tr '\\n' ','|sed 's:,$::g'`

### echo "Nodes: ${{NODES}}"

echo "==============================="
echo $PBS_JOBID
cat $PBS_NODEFILE
echo "==============================="
cd $PBS_O_WORKDIR
echo $PBS_O_WORKDIR

echo "Running the code"
time mpirun -np {nodes} {executable_location} --taskid={taskid} --inputpath={input_path} --headerpath={header_path} --outputpath={output_path} --verbose={verbose} --startk={startk} --endk={endk} --p={p}
echo "done"'''
    
    script_path: str = os.path.join(script_dir, f'test-{test_id}', f'{student_id}_testid-{test_id}_taskid-1_nodes-{nodes}_cpus-{cpus}.job')
    f = open(script_path, 'w')
    f.write(pbs_script)
    f.close()

def make_scripts(id, task_info_file) -> None:
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    script_path: str = os.path.join(script_dir, f'test-{test_id}')
    header_path: str = f'{scratch_dir}/test{id}/test-header-{id}.dat'
    input_path: str = f'{scratch_dir}/test{id}/test-input-{id}.gra'
    print (f'Scripts will be stored at {script_path} and executables will be picked from {execs_dir}')
    print (f'input path = {input_path}, header_path = {header_path}')
    if not os.path.exists(script_path):
        os.makedirs(script_path)
 
    for f in os.listdir(script_path):
        print (f'Removing old scripts')
        os.remove(os.path.join(script_path, f))
    nodes: int = int(input("Enter nodes: "))
    cpus: int = int(input("Enter cpus: "))
    walltime: int = input("Enter walltime: ")
    taskid: int = int(input("task id: "))
    verbose: int = int(input("verbose: "))
    with open(f'{script_path}/conf.txt', 'w+') as f:
        f.write(f'''
		For test case {id}, configuration setup within scripts nodes = {nodes}, 
		cpus = {cpus}, walltime = {walltime}, taskid = {taskid}, verbose = {verbose}
	''')
        f.close()

    print (f'cpus = {cpus}, nodes = {nodes}, walltime = {walltime}, taskid = {taskid} and verbose = {verbose}')
    
    valid: str = input("Please validate info ? (y/n)")
    if valid.lower() == 'n':
        return
    startk, endk = None, None
    with open(task_info_file, 'r') as f:
        line: str = f.readline().split(',')
        startk: int = int((line[0]).split('=')[1])
        endk: int = int((line[1]).split('=')[1])
        print (f'startk = {startk} and endk = {endk}')
        f.close()

    for student_id in students:
        print (student_id)
        output_path: str = f'{scratch_dir}/test{id}_output/{student_id}.txt'   
        student_executable_path: str = os.path.join(execs_dir, f'{student_id}_a2')
        generate_pbs_script(test_id=id, 
                            student_id=student_id, 
			    nodes=nodes, 
			    cpus=cpus, 
			    walltime=walltime,
                            taskid=taskid, 
			    input_path=input_path,
                            header_path=header_path, 
                            output_path=output_path, 
                            verbose=verbose, 
                            startk=startk, 
                            endk=endk, 
			    p=1, 
			    executable_location=student_executable_path)
        

#Run code for a specific student on all the test cases...

def student_run_code(test_id: int, student_id: str = "") -> None:
    
    output_path: str = os.path.join(scratch_dir, f'test{test_id}_output')
    err_out_path: str = os.path.join(scratch_dir, f'test{test_id}_output_extra')
    scripts_path: str = os.path.join(script_dir, f'test-{test_id}')
   
    print (f'output path = {output_path}, err and output logs = {err_out_path}, scripts path = {scripts_path}')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.exists(err_out_path):
        os.makedirs(err_out_path)
   
    for f in os.listdir(scripts_path):               
        if 'conf' in f:
            continue
        if not (student_id in f):
            continue
        print (f"Running for entry number = {student_id}")
        path: str = os.path.join(scripts_path, f)
        entry_no: str = path.split('_')[0].split('/')[-1]
        extra_error_file: str = os.path.join(err_out_path, f'{entry_no}_error.err')
        extra_output_file: str = os.path.join(err_out_path, f'{entry_no}_output.out')
        student_output_file: str = os.path.join(output_path, f'{entry_no}.txt')
        if len(student_id) and student_id != entry_no:
             break
        if os.path.exists(extra_error_file):
            print (f'Removing already existing extra output files {entry_no}')
            os.remove(extra_error_file)
            os.remove(extra_output_file)
        if os.path.exists(student_output_file):
            os.remove(student_output_file) # Removing in case if student is appending to these file
        print (f'Running at {path}')
        subprocess.run(['nohup', 'qsub', '-P', 'col380', '-q', 'standard', path])



def run_code(test_id: int, i: int, j: int, student_id: str = "") -> None:
    output_path: str = os.path.join(scratch_dir, f'test{test_id}_output')
    err_out_path: str = os.path.join(scratch_dir, f'test{test_id}_output_extra')
    scripts_path: str = os.path.join(script_dir, f'test-{test_id}')
   
    print (f'output path = {output_path}, err and output logs = {err_out_path}, scripts path = {scripts_path}')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.exists(err_out_path):
        os.makedirs(err_out_path)
    for f in os.listdir(scripts_path)[i: j + 1]:
        if 'conf' in f:
            continue
        path: str = os.path.join(scripts_path, f)
        entry_no: str = path.split('_')[0].split('/')[-1]
        extra_error_file: str = os.path.join(err_out_path, f'{entry_no}_error.err')
        extra_output_file: str = os.path.join(err_out_path, f'{entry_no}_output.out')
        student_output_file: str = os.path.join(output_path, f'{entry_no}.txt')
        if len(student_id) and student_id != entry_no:
             break
        print (f"Entry no: {entry_no}")
        if os.path.exists(extra_error_file):
            print (f'Removing already existing extra output files {entry_no}')
            os.remove(extra_error_file)
            os.remove(extra_output_file)
        if os.path.exists(student_output_file):
            os.remove(student_output_file) # Removing in case if student is appending to these file
        print (f'Running at {path}')
        subprocess.run(['nohup', 'qsub', '-P', 'col380', '-q', 'standard', path])


def convert_time_to_seconds(time_str: str) -> float:
    store = dict()
    t = str()
    for c in time_str:
        if c.isalpha():
            store[c] = t
            t = ""
        else:
            t += c
    total_seconds = 0.0
    conversion = {'h': 3600, 'm': 60, 's': 1}
    for unit, t in store.items():
        total_seconds += float(t) * conversion[unit]

    return total_seconds


def check_files_verbose0(testid, task_info_file, actual_output_file: str, student_submissions) -> None:
    correct_output: dict = dict()
    start_k = None 
    end_k = None
    range_k = None
    actual_output_file = actual_output_file.replace('_verbose', '')
    logs_dir: str = os.path.join(scratch_dir, f'logs_{testid}') #f'{scratch_dir}/logs_{testid}'
    extra_dir: str = os.path.join(scratch_dir, f'test{testid}_output_extra') #f'{scratch_dir}/test{testid}_output_extra'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    else:
        for f in os.listdir(logs_dir):
            os.remove(os.path.join(logs_dir, f))
    with open(task_info_file, 'r') as f:
        line = f.readline().split(',')
        start_k = int((line[0]).split('=')[1])
        end_k = int((line[1]).split('=')[1])
        range_k = (end_k - start_k) + 1
        f.close()
    with open(actual_output_file, 'r') as f:
        while True:
            new_k: str = f.readline()
            if not new_k:
                break
            isKGroupPresent: int = int(new_k.split('\n')[0].strip())
            correct_output[start_k] = isKGroupPresent
            start_k += 1
        f.close()
    entry_numbers: list = list()
    for student_file in student_submissions:
        entry_no: str = student_file.split('/')[-1]
        entry_numbers.append(entry_no)
   
    time_df: dict = {"Entry_number": entry_numbers}
    time_df: pd.DataFrame = pd.DataFrame(time_df)
    time_df.set_index('Entry_number', inplace=True)
    time_df['Total Run Time (if correct)'] = 'NA'
    for k in range(start_k, end_k + 1):
        time_df[f'Verdict: GroupSize={k}'] = 'WA'

    for student_file in student_submissions:
        with open(task_info_file, 'r') as f:
            line: str = f.readline().split(',')
            start_k: int = int((line[0]).split('=')[1])
            end_k: int = int((line[1]).split('=')[1])
            print (f'start_k = {start_k}, end_k = {end_k}')
            f.close()
        entry_no: str = student_file.split('/')[-1]
        student_output: dict = dict()
        try:
            with open(os.path.join(scratch_dir, f'test{test_id}_output/{student_file}'), 'r') as f:
                lines: list = f.readlines()
                if len(lines) == 1:    
                    lines = lines[0].strip().split(' ')
                for i in range(len(lines)):
                    student_output[i + start_k] = int(lines[i].strip())
                f.close()
 
            correct_cnt: int = 0
            logs: list = []
                       
            def getLogMessage(log, k) -> str:
                formatted: str = f'{"=" * 70}\n\tFOR GROUP OF SIZE = {k}\n{"=" * 70}\n' 
                log_message = ""
                if log == 'correct':
                    log_message: str = f'ACCEPTED: For group of size {k}, your output is correct!\n'
                elif log == 'incorrect':
                    log_message: str = f'WRONG ANSWER: For group of size {k}, your output is incorrect!\n'
                return formatted + log_message


            for k, studentSayKGroupPresent in student_output.items():
                local_correct: bool = False # Is correct for a current value of k 
                
                actualKGroupPresent = correct_output[k]
                category: str = str() # Four subcategory
                if studentSayKGroupPresent == actualKGroupPresent:
                    local_correct: bool = True
                    correct_cnt += 1
                    category: str = 'correct'
                else:
                    category: str = 'incorrect'
                
                logs.append(getLogMessage(category, k))
                
                if local_correct: 
                    time_df.loc[entry_no, f'Verdict GroupSize={k}'] = 'AC' # Accepted
                else:
                    time_df.loc[entry_no, f'Verdict GroupSize={k}'] = 'WA' # Wrong Answer
             
            if correct_cnt == range_k: # If correct for all the value of k, then only time will be consider else not
                e_no = entry_no.split('.')[0]
                with open(os.path.join(extra_dir, f'{e_no}_error.err'), 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'real' in line:
                            real_time = convert_time_to_seconds(line.split(' ')[-1].split('real')[1].strip())
                            print (f"{e_no} Run time: {real_time}")
                            time_df.loc[entry_no, "Total Run Time (if correct)"] = real_time

            if os.path.exists(os.path.join(logs_dir, entry_no)):
                with open(os.path.join(logs_dir, entry_no), 'r+') as f:
                    f.truncate(0)
                    f.close()

            with open(os.path.join(logs_dir, entry_no), 'w+') as f: 
                for log in logs:
                    f.write(log)
                f.close()
        except Exception as e:
            print (f'Something bad happen at {student_file} : ', e)
    time_df.rename(columns={'Total Run Time (if correct)': 'Runtime(in sec)'}, inplace=True)
    time_df.to_csv(f'{logs_dir}/time_test_{testid}.csv')


def check_files_verbose1(testid, task_info_file, actual_output_file: str, student_submissions) -> None:
    print (f'Check file verbose = 1 called')
    correct_output = dict()
    start_k = None 
    end_k = None
    print (task_info_file, actual_output_file, student_submissions) 
    logs_dir = os.path.join(scratch_dir, f'logs_{testid}')
    extra_dir = os.path.join(scratch_dir, f'test{testid}_output_extra')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    else:
        for f in os.listdir(logs_dir):
            os.remove(os.path.join(logs_dir, f))
    with open(task_info_file, 'r') as f:
        line = f.readline().split(',')
        start_k = int((line[0]).split('=')[1])
        end_k = int((line[1]).split('=')[1])
        f.close()
        print (f'start_k = {start_k} and end_k = {end_k}')
    with open(actual_output_file, 'r') as f:
        while True:
            new_k: str = f.readline()
            if not new_k:
                break
            isKGroupPresent: int = int(new_k.split('\n')[0].strip())
            components: list = list()
            if isKGroupPresent:
                number_of_groups = int(f.readline().split('\n')[0].strip())
                for _ in range(0, number_of_groups):
                    line: str = f.readline()
                    if not line:
                        break
                    line = list((line.split('\n')[0]).strip().split(' '))
                    line = [int(val) for val in line if val != ' ']
                    line.sort()
                    components.append(line)
                components.sort()
                correct_output[start_k] = (isKGroupPresent, number_of_groups, components)
            else: 
                correct_output[start_k] = (0, 0, components)
            start_k += 1
        f.close()
    entry_numbers: list = list()
    for student_file in student_submissions:
        entry_no: str = student_file.split('/')[-1]
        entry_numbers.append(entry_no)

    time_df: dict = {"Entry_number": entry_numbers}
    time_df: pd.DataFrame = pd.DataFrame(time_df)
    time_df.set_index('Entry_number', inplace=True)
    time_df['Total Run Time (if correct)'] = 'NA'
    for k in range(start_k, end_k + 1):
        time_df[f'Verdict: GroupSize={k}'] = 'WA'


    for student_file in student_submissions:
        range_k: int = 0
        with open(task_info_file, 'r') as f:
            line: str = f.readline().split(',')
            start_k: int = int((line[0]).split('=')[1])
            end_k: int = int((line[1]).split('=')[1])
            range_k = (end_k - start_k) + 1
            print (f'start_k = {start_k}, end_k = {end_k}')
            f.close()
        entry_no: str = student_file.split('/')[-1]
        student_output: dict = {k: dict() for k in range(start_k, end_k + 1)}
        try:
            print (f'{scratch_dir}/test{test_id}_output/{student_file}')
            with open(os.path.join(scratch_dir, f'test{test_id}_output/{student_file}'), 'r') as f:
                while True:
                    new_k: str = f.readline()
                    if not new_k:
                        break
                    isKGroupPresent: str = new_k.split('\n')[0].strip()
                    if len(isKGroupPresent):
                        isKGroupPresent = int(isKGroupPresent)
                    components = list()
                    if isKGroupPresent:
                        number_of_groups = int(f.readline().split('\n')[0].strip())
                        for _ in range(0, number_of_groups):
                            line = f.readline()
                            if not line:
                                break
                            if line == ['']:
                                continue
                            line = list((line.split('\n')[0].strip()).split(' '))
                            line = [int(val) for val in line if val != ' ' and val != '']
                            line.sort()
                            components.append(line)
                        components.sort()
                        student_output[start_k] = (isKGroupPresent, number_of_groups, components)
                    else:
                        number_of_groups=0 
                        student_output[start_k] = (0, number_of_groups, components)
                    start_k += 1
                    if start_k > end_k:
                        break
                                
            def getLogMessage(log, k, numberOfGroupsByStudent, actualNumberOfGroups, 
			      studentSayKGroupPresent, actualKGroupPresent, 
			      actualGroups, studentGroups) -> str:
                formatted = f'{"=" * 70}\n\tFOR GROUP OF SIZE = {k}\n{"=" * 70}\n' 
                log_message = ""
                if log == 'group_present_mismatch':
                    log_message = f'''INCORRECT: For group of size {k}, you are telling there are no group(s), 
                        but there are. Expecting: {actualKGroupPresent}, Got: {studentSayKGroupPresent}\n'''
                if log == 'no_of_groups_mismatch':
                    log_message = f'''INCORRECT: For group of size {k}, you are telling there are {numberOfGroupsByStudent} group(s). 
                        Expecting: {actualNumberOfGroups}, Got: {numberOfGroupsByStudent}\n'''
                if log == 'group_mismatch':
                    need = False
                    make_log_message = "\nMore details...\n" if need else ''
                    if need:
                        mismatched = list()
                        for a, s in zip(actualGroups, studentGroups):
                            if a != s:
                                mismatched.append((a, s))

                        for a, s in mismatched:        
                            make_log_message += (f'''Expecting: {a}\nGot: {s}\n''')

                    log_message = f'''PARTIAL CORRECT: You are saying right that groups of size {k} exists, 
                    but your groups are mismatched.. {make_log_message}\n'''
                if log == 'correct':
                    log_message = f'ACCEPTED: For group of size {k}, your output is correct!\n'

                return formatted + log_message
            
            correct_count: int = 0 # If this matches range_k, then only check the time, else no need.
            logs: list = []
            # Every code will get an entry to the for loop, regardless of what they what was content in their file(or even file is empty)
            for k, values in student_output.items():
                try:
                    studentSayKGroupPresent, numberOfGroupsByStudent, studentGroups = values 
                    local_correct: bool = False # Is correct for a current value of k 
                    if k not in correct_output:
                        logs.append(f'\n Total number of lines expected in output are exceding \n\n\n')
                        continue
                    actualKGroupPresent, actualNumberOfGroups, actualGroups = correct_output[k]
                    category: str = str() # Four subcategory
                    partial_correct: bool = False # Only saying that group is present of not (verbose = 0) setting
                    if studentSayKGroupPresent == actualKGroupPresent:
                        partial_correct: bool = True
                        if numberOfGroupsByStudent == actualNumberOfGroups:
                            if (len(studentGroups) == len(actualGroups)) and (studentGroups == actualGroups):
                                local_correct: bool = True
                                correct_count += 1
                                category: str = 'correct'
                            else:
                                category: str = 'group_mismatch'
                        else: 
                            category: str = 'no_of_groups_mismatch'
                    else:
                        category: str = 'group_present_mismatch'
                    
                    logs.append(getLogMessage(category, k, numberOfGroupsByStudent, 
                    actualNumberOfGroups, studentSayKGroupPresent, 
                    actualKGroupPresent, actualGroups, studentGroups))
                    time_df.loc[entry_no, f'Verdict GroupSize={k}'] = 'WA'
                    if local_correct: 
                        time_df.loc[entry_no, f'Verdict GroupSize={k}'] = 'AC' # Accepted
                    elif partial_correct:
                        time_df.loc[entry_no, f'Verdict GroupSize={k}'] = 'PC' # Partial Correct
                except Exception as e:
                    print (f'While checking file {e} happened')
                    continue
                
            if correct_count == range_k: # NOTE: If correct for all the value of k, then only time will be consider else not
                e_no = entry_no.split('.')[0]
                print (f'For entry number: {e_no}_error.err')
                print ("extra dir" + os.path.join(extra_dir, f'{e_no}_err.err'))

                with open(os.path.join(extra_dir, f'{e_no}_error.err'), 'r') as f:
                    lines = f.readlines()
                    print (lines)
                    for line in lines:
                        if 'real' in line:
                            real_time = convert_time_to_seconds(line.split(' ')[-1].split('real')[1].strip())
                            print (f'Real time: {real_time}')
                            time_df.loc[entry_no, "Total Run Time (if correct)"] = real_time


            if os.path.exists(os.path.join(logs_dir, entry_no)):
                with open(os.path.join(logs_dir, entry_no), 'r+') as f:
                    f.truncate(0)
                    f.close()

            with open(os.path.join(logs_dir, entry_no), 'w+') as f:
                for log in logs:
                    f.write(log)
                f.close()
        except Exception as e:
            print (f'Something bad happen at {student_file} : ', e)

    time_df.rename(columns={'Total Run Time (if correct)': 'Runtime(in sec)'})
    time_df.to_csv(os.path.join(logs_dir, f'time_test_{testid}.csv'))
 

def task2_check_files_verbose0(testid, task_info_file, actual_output_file, student_submissions) -> None:
    k, p = None, None 
    print (task_info_file, actual_output_file, student_submissions) 
    logs_dir = os.path.join(f'a3_logs_{testid}')
    extra_dir = os.path.join(f'a3_test{testid}_output_extra')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    else:
        for f in os.listdir(logs_dir):
            os.remove(os.path.join(logs_dir, f))    

       
    correct_output = list()
    with open(actual_output_file, 'r') as f:
        while True:
            first_line: str = f.readline()
            if not first_line:
                break
            c: int = int(first_line.split('\n')[0].strip())
            correct_output.append([c])
            if c > 0:
                influencer_node = f.readline()
                influencer_node = list((influencer_node.split('\n')[0]).strip().split(' ')) 
                influencer_node.sort()
                correct_output.append(influencer_node)
            else: 
                correct_output.append([0])
        f.close()


def task2_check_files_verbose1(testid, task_info_file, actual_output_file, student_submissions) -> None:
    k, p = None, None 
    print (task_info_file, actual_output_file, student_submissions) 
    logs_dir = os.path.join(scratch_dir, f'a3_logs_{testid}')
    extra_dir = os.path.join(scratch_dir, f'a3_test{testid}_output_extra')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    else:
        for f in os.listdir(logs_dir):
            os.remove(os.path.join(logs_dir, f))    

    with open(task_info_file, 'r') as f:
        line = f.readline().split(',')
        k = int((line[0]).split('=')[1])
        p = int((line[1]).split('=')[1])
        f.close()
        print (f'k = {k} and p = {p}')

    correct_output = list()
    with open(actual_output_file, 'r') as f:
        first_line: str = f.readline()
        if first_line:    
            c: int = int(first_line.split('\n')[0].strip())
            correct_output.append([c])
            components: list = list()
            if c > 0:
                for i in range(0, c):
                    influencer_node = f.readline()
                    influencer_node = int(influencer_node.split('\n')[0].strip())
                    followers = f.readline()
                    followers = list((followers.split('\n')[0]).strip().split(' ')) 
                    followers.sort()
                    correct_output.append([influencer_node])
                    correct_output.append(followers)
            else: 
                correct_output.append([0])
        f.close()


                   
def check_files(test_id: int, task_id: int, verbose: int) -> None:
    print (f'Running for vebose = {verbose}')
    print (f"student outputfies = {os.path.join(scratch_dir, f'test{test_id}_output')}, total := {len(os.listdir(os.path.join(scratch_dir, f'test{test_id}_output')))}")
    
    student_submissions =  list(os.listdir(os.path.join(scratch_dir, f'test{test_id}_output')))
    print (f'Logging submission files: {student_submissions}')
    if '2020CS10358' in student_submissions:
        print("YES\n\n")
        return 
    task_info_path=os.path.join(scratch_dir, f'test{test_id}/task{task_id}_info.txt')
    if verbose == 1:
        check_files_verbose1(testid=test_id, 
                            task_info_file=task_info_path, 
                            actual_output_file=os.path.join(scratch_dir, f'test{test_id}/task{task_id}_output{test_id}_verbose.txt'), 
                            student_submissions=student_submissions)
    else:
        check_files_verbose0(testid=test_id, 
                            task_info_file=task_info_path, 
                            actual_output_file=os.path.join(scratch_dir, f'test{test_id}/task{task_id}_output{test_id}.txt'), 
                            student_submissions=student_submissions)
 

if __name__ == '__main__':
    print (f'''
    1. No-opeartion
    2. Create and save Executables to execs (move from sub to execs)
    3. Make script ?
    4. Run code to make output files ?
    5. Run autograder ?
    6. Run for a specific student ? 
    ''')
    val: int = int(input('Enter choices(1-6):  ' ))

    if val == 1:
        pass
        #create_executables()
    elif val == 2:
        create_executables()
        save_exec()
    elif val == 3:
        test_id = int(input('For which test case ? '))
        task_id = 1
        make_scripts(test_id, os.path.join(scratch_dir, f'test{test_id}/task{task_id}_info.txt'))
    elif val == 4:
        test_id: int = int(input(f'For which test case ?  '))
        i: int = int(input(f'Start: (hint = 0) '))
        j: int = int(input(f'To : (hint = 62) '))
        USER: str = os.getenv('USER').split('/')[-1]
        max_jobs_in_queue: int = 8
        while i < j:
            print (f"status: i = {i} and j = {j}")
            jobs: str = str(subprocess.check_output(['qstat', '-u', USER])).split('pbshpc')
            total_active_jobs: int = max(0, len(jobs) - 2)
            can_insert: int = max_jobs_in_queue - total_active_jobs
            print (f'Total active jobs = {total_active_jobs}')
            print (f'Empty space in the pbs queue : {can_insert}')
            while can_insert > 0:
                print (f'Adding job {i} to the queue')
                run_code(test_id, i, i)
                i += 1
                can_insert -= 1
            print ("Sleep...")
            time.sleep(20)
            print ("Wake...")
                        
        with open(os.path.join(scratch_dir, 'info.txt'), 'w+') as f:
            f.write(f"test_id = {test_id}, i = {i}, j = {j}")
            f.close()

    elif val == 5:
        #test_id: int = int(input('For which test case ? '))
        task_id: int = 1 # int(input('For which task (1/2) ? '))
        #verbose: int = int(input('For verbose setting(0/1)? '))
        all_testcases = [0, 1, 2, 3, 4, 5, 6, 10, 12, 14, 15]
        all_verbose = [1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0]
        #check_files(test_id, task_id, verbose)
        for (test_id, verbose) in zip(all_testcases, all_verbose):
            check_files(test_id, task_id, verbose)

    elif val == 6:
        # students entry number
        entry_no: str = ''  
        print (f'Running for entry number = {entry_no}')
        test_id: list =  [4, 5, 6, 10, 12, 14, 15]
        USER: str = os.getenv('USER').split('/')[-1]
        max_jobs_in_queue = 6
        for test in test_id:
            print (f"Running test{test}")
            while True:
                jobs = str(subprocess.check_output(['qstat', '-u', USER])).split('pbshpc')
                total_active_jobs = max(0, len(jobs) - 2)
                print (f'Total active jobs = {total_active_jobs}')
                can_insert = max_jobs_in_queue - total_active_jobs
                print (f'Empty space in the pbs queue : {can_insert}')
                if can_insert > 0:
                    student_run_code(test, entry_no)
                    break
                print (f'Sleeping for 10 seconds')
                time.sleep(10) 
                print (f'waking..')
               

