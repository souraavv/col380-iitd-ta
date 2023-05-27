import os
import subprocess
import shutil
import pandas as pd
import time 
from pprint import pprint

'''
-- Instructions to run 

To run this script, just make the subA3 part and add your code there
and also put testcases inside testcasesA3 rest other will get created

Directory structure
---------------------
|-scratch
  |-execsA3
    | <Entry_no>_a3
  |-scriptA3
    | test-<id>
        | .pbs file
  |-testcasesA3
    | test<id>
        | all_test files
  |-subA3
    | <Name>_<Entry_no>_A3
        | code files
        | make
        | other..


module load compiler/gcc/9.1/openmpi/4.0.2
module load compiler/intel/2019u5/intelpython3
python3 auto3.py 

- Option 2 will make your executable 
- Option 3 will make your script (check configuration files to set up the same values as used during testing)
- Option 6, to run your code, remember to pass your entry number in format 2020CSXXXX and test_id on which you want to test.

'''

home_dir: str = os.path.expanduser('~')
scratch_dir: str = os.path.join(home_dir, 'scratch')
execs_dir: str = os.path.join(scratch_dir, 'execsA3')
sub_dir: str = os.path.join(scratch_dir, 'subA3')
script_dir: str = os.path.join(scratch_dir, 'scriptA3')
test_dir: str = os.path.join(scratch_dir, 'testcasesA3')
students:list = []

a_id = 'a3'

def prereq() -> None:
    if not os.path.exists(sub_dir):
        print ('No submission directory found!')
        return    
    #  Fill all the students who submitted
    global students
    if os.path.exists(execs_dir):
        for f in os.listdir(execs_dir):
            students.append(f.split('_')[0])
        students.sort()


def create_executables() -> None:
    for folder in os.listdir(sub_dir):
        print (f'Creating exectuable for {folder}')
        if os.path.isdir(os.path.join(sub_dir, folder)):
            path: str = os.path.join(sub_dir, folder)
            executable_path: str = os.path.join(sub_dir, folder, a_id)
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
            source_path: str = os.path.join(sub_dir, folder, a_id)
            if not os.path.exists(source_path):
                continue
            destination_path: str = os.path.join(execs_dir, f'{student_entry_no}_{a_id}')
            print (source_path, destination_path)
            if os.path.exists(destination_path):
                print (f'Removing already existing files at {destination_path}')
                os.remove(destination_path)
            shutil.copy(source_path, destination_path)

    print (f'Populating students list...')
    global students
    if os.path.exists(execs_dir):
        for f in os.listdir(execs_dir):
            students.append(f.split('_')[0])
        students.sort()
        print (f'There are total {len(students)} students')
        pprint (students)


def generate_pbs_script(
		test_id, student_id, 
		executable_location, 
		nodes, cpus, ompthread, walltime, 
		taskid, input_path, 
		header_path, 
		output_path, extra_output_path,
        verbose, startk, endk, p) -> None:
    print (f''' test_id = {test_id}, student_id = {student_id}, 
                executable_location = {executable_location}, 
                nodes = {nodes}, cpus = {cpus}, 
                walltime={walltime}, taskid = {taskid},
                input_path = {input_path}, 
                header_path = {header_path}, 
                output_path = {output_path}
                verbose = {verbose}
                extra_output_path = {extra_output_path}
                startk = {startk}, endk= {endk}, p = {p}
	''')
    pbs_script = \
f'''
#!/bin/bash
#PBS -N {student_id}-run
#PBS -l select={nodes}:ncpus={cpus}:mpiprocs=1:ompthreads={ompthread}
#PBS -l place=scatter
#PBS -l walltime={walltime}
#PBS -o {extra_output_path}/{student_id}_output.out
#PBS -e {extra_output_path}/{student_id}_error.err

module purge
module load compiler/gcc/9.1/openmpi/4.0.2

echo "============ NODES ASSIGNED FOR JOB ================="
echo $PBS_JOBID
cat $PBS_NODEFILE
echo "============== WORKING DIRECTORY ================"
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
    header_path: str = os.path.join(test_dir, f'test{id}/test-header-{id}.dat')
    input_path: str = os.path.join(test_dir, f'test{id}/test-input-{id}.gra')
    print (f'Scripts will be stored at {script_path} and executables will be picked from {execs_dir}')
    print (f'input path = {input_path}, header_path = {header_path}')
    if not os.path.exists(script_path):
        os.makedirs(script_path)
 
    for f in os.listdir(script_path):
        print (f'Removing old scripts')
        os.remove(os.path.join(script_path, f))
    nodes: int = int(input("Enter nodes: "))
    cpus: int = int(input("Enter cpus: "))
    ompthreads: int = int(input("ompthreads: "))  
    walltime: int = input("Enter walltime: ")
    verbose: int = int(input("verbose: "))

    with open(os.path.join(script_path, f'conf.txt'), 'w+') as f:
        f.write(f'''
        Configuration setup within scripts, for test case {id} 
            1. nodes = {nodes}, 
            2. cpus = {cpus}, 
            3. walltime = {walltime}, 
            4. taskid = {task_id}, 
            5. verbose = {verbose},
            6. ompthreads = {ompthreads}
        ''')
        f.close()

    print (f'cpus = {cpus}, ompthreads = {ompthreads}, nodes = {nodes}, walltime = {walltime}, taskid = {task_id} and verbose = {verbose}')
    
    valid: str = input("Validate info ? (y/n)")
    if valid.lower() == 'n':
        return
    startk, endk, p = -1, -1, -1
    if task_id == 1:
        with open(task_info_file, 'r') as f:
            line: str = f.readline().split(',')
            startk: int = int((line[0]).split('=')[1])
            endk: int = int((line[1]).split('=')[1])
            print (f'startk = {startk} and endk = {endk}')
            f.close()

    elif task_id == 2:
        with open(task_info_file, 'r') as f:
            line = f.readline().split(',')
            endk = int((line[0]).split('=')[1])
            p = int((line[1]).split('=')[1])
            startk = endk
            f.close()
            print (f'endk = {endk} and p = {p}')
        

    for student_id in students:
        print (student_id)
        output_path: str = os.path.join(test_dir, f'test{id}_output/{student_id}.txt')   
        extra_output_path: str = os.path.join(test_dir, f'test{test_id}_output_extra') 
        student_executable_path: str = os.path.join(execs_dir, f'{student_id}_{a_id}')
        generate_pbs_script(test_id=id, 
                student_id=student_id, 
			    nodes=nodes, 
			    cpus=cpus, 
                ompthread=ompthreads,
			    walltime=walltime,
                taskid=task_id, 
			    input_path=input_path,
                header_path=header_path, 
                output_path=output_path, 
                extra_output_path=extra_output_path,
                verbose=verbose, 
                startk=startk, 
                endk=endk, 
			    p=p, 
			    executable_location=student_executable_path)
        

#Run code for a specific student on all the test cases...

def student_run_code(test_id: int, student_id: str = "") -> None:
    
    output_path: str = os.path.join(test_dir, f'test{test_id}_output')
    err_out_path: str = os.path.join(test_dir, f'test{test_id}_output_extra')
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
    output_path: str = os.path.join(test_dir, f'test{test_id}_output')
    err_out_path: str = os.path.join(test_dir, f'test{test_id}_output_extra')
    scripts_path: str = os.path.join(script_dir, f'test-{test_id}')
   
    print (f'\toutput path = {output_path}\n\terr and output logs = {err_out_path}\n\tscripts path = {scripts_path}\n')
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
        print ("--"*30, "\n", f"Entry no: {entry_no}")
        if os.path.exists(extra_error_file):
            print (f'Removing already existing extra output files {entry_no}')
            os.remove(extra_error_file)
            os.remove(extra_output_file)
        if os.path.exists(student_output_file):
            os.remove(student_output_file) # Removing in case if student is appending to these file
        print (f'Running at {path}')
        subprocess.run(['nohup', 'qsub', '-P', 'col380', '-q', 'standard', path])


def convert_time_to_seconds(time_str: str) -> float:
    # could have avoided if used time -p 
    store: dict = dict()
    t: str = str()
    for c in time_str:
        if c.isalpha():
            store[c] = t
            t = ""
        else:
            t += c
    total_seconds: float = 0.0
    conversion = {'h': 3600, 'm': 60, 's': 1}
    for unit, t in store.items():
        total_seconds += float(t) * conversion[unit]

    return total_seconds


def task1_check_files_verbose0(testid, task_info_file, actual_output_file: str, student_submissions) -> None:
    correct_output: dict = dict()
    start_k = None 
    end_k = None
    range_k = None
    actual_output_file = actual_output_file.replace('_verbose', '')
    logs_dir: str = os.path.join(test_dir, f'logs_{testid}') 
    extra_dir: str = os.path.join(test_dir, f'test{testid}_output_extra') 
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
        print (f'start_k = {start_k} and end_k = {end_k}')
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
    print (f'TOTAL SUBMISSION WHICH GENERATED OUTPUT: {len(student_submissions)}')
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
            with open(os.path.join(test_dir, f'test{test_id}_output/{student_file}'), 'r') as f:
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

def task1_check_files_verbose1(testid, task_info_file, actual_output_file: str, student_submissions) -> None:
    print (f'Check file verbose = 1 called')
    correct_output = dict()
    start_k = None 
    end_k = None
    print (task_info_file, actual_output_file, student_submissions) 
    logs_dir = os.path.join(test_dir, f'logs_{testid}')
    extra_dir = os.path.join(f'test{testid}_output_extra')
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


    for (idx, student_file) in enumerate(student_submissions):
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
            with open(os.path.join(scratch_dir, f'test{test_id}_output/{student_file}'), 'r') as f:
                print (f'{scratch_dir}/test{test_id}_output/{student_file}')
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
            logs: list = list()
            # Every code will get an entry to the for loop, regardless of what they what was content in their file(or even file is empty)
            for k, (studentSayKGroupPresent, numberOfGroupsByStudent, studentGroups) in student_output.items():
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
                
            if correct_count == range_k: # NOTE: If correct for all the value of k, then only time will be consider else not
                e_no = entry_no.split('.')[0]
                print (f'For entry number: {e_no}_error.err')
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
    logs_dir: str = os.path.join(test_dir, f'task2_logs_{testid}')
    extra_dir: str = os.path.join(test_dir, f'test{testid}_output_extra')
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

    correct_output: dict = dict()
    # Two possibility dict{influencer_id: followers list} or dict{'no-influencer' == True}

    with open(actual_output_file, 'r') as f:
        first_line: str = f.readline()
        if first_line:    
            c: int = int(first_line.split('\n')[0].strip())
            correct_output['influencer_count'] = c
            if c > 0:
                influencers = f.readline()
                influencers = influencers.strip().split(' ')
                influencers = [int(influencer) for influencer in influencers]
                influencers.sort()
                correct_output['influencers'] = influencers
        f.close()

    entry_numbers: list = list()
    for student_file in student_submissions:
        entry_no: str = student_file.split('/')[-1]
        entry_numbers.append(entry_no)

    time_df: dict = {"Entry_number": entry_numbers}
    time_df: pd.DataFrame = pd.DataFrame(time_df)
    time_df.set_index('Entry_number', inplace=True)
    run_time: str = 'Runtime(in sec)'
    verdict: str = f'Verdict: GroupSize={k}, and p = {p}'
    time_df[run_time] = 'NA'
    time_df[verdict] = 'WA'

    def getLogMessage(log, k, p,
		      studentSayInfluencers='', 
              actualInfluencers='',  
	    ) -> str:
        formatted = f'{"=" * 70}\n\tFOR k = {k}, p = {p} \n{"=" * 70}\n' 
        log_message = ""
        if log == 'correct-influencers':
            log_message = f'''Fully correct solution, influencers matching..'''
        if log == 'incorrect':
            log_message = f''' Incorrect solution, expected {actualInfluencers}, got {studentSayInfluencers} '''
        if log == 'partial-correct-influencers':
            log_message = f''' Partial correct solution, you are telling correct number of influencer nodes, but not all of them are in the solution (either partial or more)''' 
        return formatted + log_message
 
    for student_file in student_submissions:
        #print (f'\n\n {student_file} \n\n')
        with open(task_info_file, 'r') as f:
            line = f.readline().split(',')
            k = int((line[0]).split('=')[1])
            p = int((line[1]).split('=')[1])
            f.close()
            print (f'k = {k} and p = {p}')

        entry_no: str = student_file.split('/')[-1]
        student_output: dict = dict()
        #print ("Student path" + os.path.join(test_dir, f'test{testid}_output', student_file))
        try:
            with open(os.path.join(test_dir, f'test{testid}_output', student_file), 'r') as f:
                first_line: str = f.readline()
                if not first_line:
                    continue
                if first_line:    
                    c: int = int(first_line.strip())
                    student_output['influencer_count'] = c
                    if c > 0:
                        influencers = f.readline()
                        if not influencers:
                            continue
                        influencers = influencers.strip().split(' ')
                        influencers = [int(influencer) for influencer in influencers]
                        influencers.sort()
                        student_output['influencers'] = influencers
                f.close()

            fully_correct: bool = False
            partial_correct: bool = False
            logs: list = list()
            # If there are no influencers
            if correct_output['influencer_count'] == 0:
                if (correct_output['influencer_count'] == student_output['influencer_count']):
                    fully_correct: bool = True
                    logs.append(getLogMessage(log='correct-influencers', k = k, p = p))
                else:
                    logs.append(getLogMessage(log='incorrect', k = k, p = p,
                                studentSayInfluencers=student_output['influencer_count'], 
                                actualInfluencers=correct_output['influencer_count']))
            else:
                # No marks for telling the correct count of influencers, only when influencers are correct.
                #print(correct_output['influencer_count'], student_output['influencer_count'])
                #print (f"Count = {correct_output['influencer_count']} and {student_output['influencer_count']}")
                if (correct_output['influencer_count'] == student_output['influencer_count']):
                    partial_correct = True
                    studentSayInfluencers = student_output['influencers']
                    actualInfluencers = correct_output['influencers']
                    #print (len(studentSayInfluencers), len(actualInfluencers))
                    #print (studentSayInfluencers == actualInfluencers)
                    fully_correct = (studentSayInfluencers == actualInfluencers)
                    if fully_correct:
                        logs.append(getLogMessage(log='correct-influencers', k = k, p = p))
                    else:
                        logs.append(getLogMessage(log='partial-correct-influencers', k = k, p = p))
                else: # if they are not equal
                    logs.append(getLogMessage(log='incorrect', k = k, p = p,
                                studentSayInfluencers=student_output['influencer_count'], 
                                actualInfluencers=correct_output['influencer_count']))                     
                
            time_df.loc[entry_no, verdict] = 'WA'
            time_df.loc[entry_no, run_time] = 'Invalid'


            if partial_correct:
                time_df.loc[entry_no, verdict] = 'PC'
            if fully_correct:
                e_no = entry_no.split('.')[0]
                time_df.loc[entry_no, verdict] = 'AC'
                with open(os.path.join(extra_dir, f'{e_no}_error.err'), 'r') as f:
                    lines = f.readlines()
                    print (f'\n\n For entry number = {e_no}')
                    for line in lines:
                        if 'real' in line:
                            real_time = convert_time_to_seconds(line.split(' ')[-1].split('real')[1].strip())
                            print (f'Real time: {real_time}')
                            time_df.loc[entry_no, run_time] = real_time



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

    time_df.to_csv(os.path.join(logs_dir, f'time_test_{testid}.csv'))
 
def task2_check_files_verbose1(testid, task_info_file, actual_output_file, student_submissions) -> None:
    k, p = None, None 
    print (task_info_file, actual_output_file, student_submissions) 
    logs_dir: str = os.path.join(test_dir, f'task2_logs_{testid}')
    extra_dir: str = os.path.join(test_dir, f'test{testid}_output_extra')
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

    correct_output: dict = dict()
    # Two possibility dict{influencer_id: followers list} or dict{'no-influencer' == True}
    with open(actual_output_file, 'r') as f:
        first_line: str = f.readline()
        if first_line:    
            c: int = int(first_line.split('\n')[0].strip())
            correct_output['influencer_count'] = c
            if c > 0:
                for _ in range(0, c):
                    influencer_node = f.readline()
                    if not influencer_node:
                        print ('Something bad with the actual file..')
                    influencer_node = int(influencer_node.split('\n')[0].strip())
                    followers = f.readline()
                    followers = followers.strip().split(' ')
                    followers = [int(f) for f in followers]
                    followers.sort()
                    correct_output[influencer_node] = followers
        f.close()

    entry_numbers: list = list()
    for student_file in student_submissions:
        entry_no: str = student_file.split('/')[-1]
        entry_numbers.append(entry_no)

    time_df: dict = {"Entry_number": entry_numbers}
    time_df: pd.DataFrame = pd.DataFrame(time_df)
    time_df.set_index('Entry_number', inplace=True)
    run_time: str = 'Runtime(in sec)'
    verdict: str = f'Verdict: GroupSize={k}, and p = {p}'
    time_df[run_time] = 'NA'
    time_df[verdict] = 'WA'

    def getLogMessage(log, k, p,
		      studentSayInfluencers='', 
              actualInfluencers='',  
	    ) -> str:
        formatted = f'{"=" * 70}\n\tFOR k = {k}, p = {p} \n{"=" * 70}\n' 
        log_message = ""
        if log == 'correct-influencers':
            log_message = f'''Partial correct solution:: All influencers are mentioned correct, but their 
                              follower are not matching... '''
        if log == 'correct-influencers-and-followers':
            log_message = f'''Correct Solution:: Both influencers and followers of that influencer matches\n'''
        if log == 'incorrect':
            log_message = f''' Incorrect solution, expected {actualInfluencers}, got {studentSayInfluencers} '''

        return formatted + log_message
    
    print (f'TOTAL SUBMISSIONS WHICH PRODUCES OUTPUT: {len(student_submissions)}')

    for (idx, student_file) in enumerate(student_submissions):
        print (f'Running student {idx}')
        with open(task_info_file, 'r') as f:
            line = f.readline().split(',')
            k = int((line[0]).split('=')[1])
            p = int((line[1]).split('=')[1])
            f.close()
            print (f'k = {k} and p = {p}')

        entry_no: str = student_file.split('/')[-1]
        student_output: dict = dict()
        print ("Student path" + os.path.join(test_dir, f'test{testid}_output', student_file))
        try:
            with open(os.path.join(test_dir, f'test{testid}_output', student_file), 'r') as f:
                
                first_line: str = f.readline()
                if not first_line:
                    continue
                if first_line:    
                    c: int = int(first_line.strip())
                    student_output['influencer_count'] = c
                    if c > 0:
                        for _ in range(0, c):
                            influencer_node = f.readline()
                            if not influencer_node:
                                continue 
                            influencer_node = int(influencer_node.strip())
                            followers = f.readline()
                            if not followers:
                                continue
                            followers = followers.strip().split(' ') 
                            followers = [int(f) for f in followers]
                            followers.sort()
                            student_output[influencer_node] = followers
                f.close()

            correct_cnt: int = 0
            fully_correct: bool = False
            partial_correct: bool = False
            logs: list = list()
            # If there are no influencers
            if correct_output['influencer_count'] == 0:
                if (correct_output['influencer_count'] == student_output['influencer_count']):
                    fully_correct: bool = True
                    logs.append(getLogMessage(log='correct-influencers-and-followers', k = k, p = p))
                else:
                    logs.append(getLogMessage(log='incorrect', k = k, p = p,
                                studentSayInfluencers=student_output['influencer_count'], 
                                actualInfluencers=correct_output['influencer_count']))
            else:
                # No marks for telling the correct count of influencers, only when influencers are correct.
                if (correct_output['influencer_count'] == student_output['influencer_count']):
                    studentSayInfluencers = list(student_output.keys())
                    studentSayInfluencers.remove('influencer_count')
                    studentSayInfluencers.sort()
                    
                    actualInfluencers = list(correct_output.keys())
                    actualInfluencers.remove('influencer_count')
                    actualInfluencers.sort()

                    partial_correct = (studentSayInfluencers == actualInfluencers)
                    # only when same influencers are present in both..
                    for influencer_node, followers in correct_output.items():
                        if influencer_node == 'influencer_count':
                            continue
                        if (influencer_node in student_output) and (student_output[influencer_node] == followers): # if followers matches
                            correct_cnt += 1
                    # Keeping it simple, since 50% marks already for correct influencers..
                    # so even followers are incorrect for one of the influencer it is considered as incorrect
                    if correct_cnt == correct_output['influencer_count']: 
                        fully_correct: bool = True
                        logs.append(getLogMessage(log='correct-influencers-and-followers', k = k, p = p))
                    elif partial_correct:
                        logs.append(getLogMessage(log='correct-influencers', k = k, p = p))

                else: # if they are not equal
                    logs.append(getLogMessage(log='incorrect', k = k, p = p,
                                studentSayInfluencers=student_output['influencer_count'], 
                                actualInfluencers=correct_output['influencer_count']))                     

            print (f'Correct count = {correct_cnt}, Fully correct = {fully_correct}, partial_correct = {partial_correct}')

            time_df.loc[entry_no, verdict] = 'WA'
            time_df.loc[entry_no, run_time] = 'Invalid'
        
            if partial_correct:
                time_df.loc[entry_no, verdict] = 'PC'
            if fully_correct:
                e_no = entry_no.split('.')[0]
                time_df.loc[entry_no, verdict] = 'AC'
                with open(os.path.join(extra_dir, f'{e_no}_error.err'), 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'real' in line:
                            real_time = convert_time_to_seconds(line.split(' ')[-1].split('real')[1].strip())
                            print (f'Real time: {real_time}')
                            time_df.loc[entry_no, run_time] = real_time

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

    time_df.to_csv(os.path.join(logs_dir, f'time_test_{testid}.csv'))
  
def check_files(test_id: int, task_id: int, verbose: int) -> None:
    print (f'Running for vebose = {verbose}, test_id = {test_id}')
    print (f"student output files = {os.path.join(scratch_dir, f'test{test_id}_output')}, total := {len(os.listdir(os.path.join(scratch_dir, f'test{test_id}_output')))}")
    student_submissions =  list(os.listdir(os.path.join(test_dir, f'test{test_id}_output')))
    print (f'Logging submission files: {student_submissions}')
    #ready = input("Provide confirmation ? (y/n) ")
    #if ready == 'n':
    #    return

    print (f'Running for test = {test_id}, task id = {task_id}, verbose = {verbose} ') 

    task_info_file = os.path.join(test_dir, f'test{test_id}/task{task_id}_info.txt')
    verbose_actual_output_file = os.path.join(test_dir, f'test{test_id}/task{task_id}_output{test_id}_verbose.txt')
    actual_output_file = os.path.join(test_dir, f'test{test_id}/task{task_id}_output{test_id}.txt')
    
    print (f'''
                Task info file : {task_info_file}, 
                Actual verbose file : {verbose_actual_output_file},
                Actual without verbose file : {actual_output_file}
    ''')

    if verbose == 1:
        if task_id == 1:
            task1_check_files_verbose1(testid = test_id, 
				        task_info_file=task_info_file, 
                  		actual_output_file=verbose_actual_output_file, 
                  		student_submissions=student_submissions)
        elif task_id == 2:
            task2_check_files_verbose1(testid = test_id, 
                       task_info_file=task_info_file, 
				       actual_output_file=verbose_actual_output_file,
 				       student_submissions=student_submissions)
    elif verbose == 0:
        if task_id == 1:
            task1_check_files_verbose0(testid = test_id, 
				       task_info_file=task_info_file, 
				       actual_output_file=actual_output_file, 
				       student_submissions=student_submissions)
        elif task_id == 2:
            task2_check_files_verbose0(testid = test_id, 
				       task_info_file=task_info_file,
				       actual_output_file=actual_output_file, 
				       student_submissions=student_submissions)


if __name__ == '__main__':
    print (f'''
        1. No-op
        2. Crate and save executables to {execs_dir} (move from sub to execs)
        3. Make script ?
        4. Run code to make output files ?
        5. Run autograder ?
        6. Run for a specific student ? 
    ''')
    
    prereq()

    val: int = int(input('Enter choices(1-6):  ' ))
    if val == 1: 
        # create_executables()
        pass 
    if val == 2:
        create_executables()
        save_exec()

    elif val == 3:
        test_id = int(input('For which test case ? '))
        task_id = int(input('What is task id (1/2) ? '))
        make_scripts(test_id, os.path.join(test_dir, f'test{test_id}/task{task_id}_info.txt'))
    elif val == 4:
        test_id: int = int(input(f'For which test case ?: '))
        i: int = int(input(f'Start from: '))
        j: int = int(input(f'To : '))
        USER: str = os.getenv('USER').split('/')[-1]
        max_jobs_in_queue: int = 5
        while i < j:
            print (f"status: i = {i} and j = {j}")
            jobs: str = str(subprocess.check_output(['qstat', '-u', USER])).split('pbshpc')
            total_active_jobs: int = max(0, len(jobs) - 2)
            can_insert: int = max_jobs_in_queue - total_active_jobs
            print (f'Total active jobs = {total_active_jobs}')
            print (f'Empty space in the pbs queue : {can_insert}')
            while can_insert > 0 and i < j:
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
        conf = [(0, 2, 1), (1, 2, 1), (5, 2, 1), (10, 2, 1), (11, 2, 0), (12, 2, 0)]
        for (test_id, task_id, verbose) in conf:
        #test_id: int = int(input('For which test case ? '))
        #task_id: int = int(input('For which task (1/2) ? '))
        #verbose: int = int(input('For verbose setting(0/1)? '))
            print (f'\n\n\n === Autograder running for test{test_id} ==== ')
            time.sleep(3)
            check_files(test_id, task_id, verbose)

    # for the purpose of demo, on individual student run
    elif val == 6:
        entries = list() 
        print (f" Running for \n {entries} ")
        confirm = input("Confirm (y / n) ? ")
  
        test_id: list = [12]
        #print (f'Running for entry number = {entry_no} and testcases : {test_id}')
        USER: str = os.getenv('USER').split('/')[-1]
        max_jobs_in_queue = 5
        for test in test_id:
           print (f"\n\n============= Running for Test-case-{test} ============== \n")
           for entry_no in entries:
                print (f"\n\n ========= Running for entry number: {entry_no} ===========")
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
                    time.sleep(15) 
                    print (f'waking..')
           print (f' ============= Finsihed running test case - {test} ================ \n\n')
               
    else:
        raise Exception("Invalid option entered")
