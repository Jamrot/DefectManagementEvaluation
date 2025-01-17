import os
import csv
import getroot
import config
import json

def result_collect_1(search_dir):
    save_file = './test.csv'
    results = []
    dirs = os.listdir(search_dir)
    fieldnames = ['filename', 'msg', 'pass']
    for dir in dirs:
        dir = os.path.join(search_dir, dir)
        dirs1 = os.listdir(dir)
        for dir1 in dirs1:
            if dir1=='results':
                file = os.path.join(dir, dir1, config.RESULT_FILENAME)
                if os.path.exists(file):
                    with open(file) as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            results.append(row)
    with open(save_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
        f.flush()

def result_collect(search_dir):
    functional_save_file = os.path.join(search_dir, 'functional-results.csv')
    security_save_file = os.path.join(search_dir, 'security-results.csv')
    fieldnames = ['filename', 'msg', 'pass']
    files = []
    functional_results = []
    security_results = []
    for root, dirs, fs in os.walk(search_dir):
        for file in fs:
            if file == 'functional-result.csv':
                file_path = os.path.join(root, file)
                files.append(file_path)
                with open(file_path) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        functional_results.append(row)
            if file == 'security-result.csv':
                file_path = os.path.join(root, file)
                files.append(file_path)
                with open(file_path) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        security_results.append(row)

    with open(functional_save_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in functional_results:
            writer.writerow(row)
        f.flush()
    
    with open(security_save_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in security_results:
            writer.writerow(row)
        f.flush()
    
    print('functional result save to: {}\nsecurity result save to:{}'.format(functional_save_file, security_save_file))
    return files

def collect_all_result(search_dir):
    result_save_file = os.path.join(search_dir, 'all-results.csv')
    all_result_roots = getroot.get_all_result_roots(search_dir)
    security_results = {}
    functional_results = {}
    # security_filenames = []
    # functional_filenames = []
    
    for result_root in all_result_roots:
        security_result_file = os.path.join(result_root, config.SECURITY_RESULT_FILENAME)
        if os.path.exists(security_result_file):
            with open(security_result_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['filename'] in security_results:
                        print(row['filename'],'duplicate result')
                        continue
                    # security_filenames.append[row['filename']]
                    # security_results[row['filename']] = {}
                    security_results[row['filename']] = row
        
        functional_result_file = os.path.join(result_root, config.FUNCTIONAL_RESULT_FILENAME)
        if os.path.exists(functional_result_file):
            with open(functional_result_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['filename'] in functional_results:
                        print(row['filename'],'duplicate result')
                        continue
                    # functional_filenames.append[row['filename']]
                    functional_results[row['filename']] = row
    
    all_results = []
    all_filenames = []
    for filename in security_results:
        result_security_pass = security_results[filename]['pass']
        security_msg = security_results[filename]['msg']
        if filename in functional_results:
            functional_pass = functional_results[filename]['pass']
            functional_msg = functional_results[filename]['msg']
        else:
            functional_pass = ''
            functional_msg = ''
    
    for filename in functional_results:
        functional_pass = functional_results[filename]['pass']
        functional_msg = functional_results[filename]['msg']
        if filename in security_results:
            result_security_pass = security_results[filename]['pass']
            security_msg = security_results[filename]['msg']
        else:
            result_security_pass = ''
            security_msg = ''
        
        all_filenames.append(filename)
        # functional_msg = ''
        # security_msg = ''
        if 'Error 1\nmake' in security_msg or 'Error 1\\nmake' in security_msg or 'Error 2\nmake' in security_msg or 'Error 2\\nmake' in security_msg or 'ompile' in security_msg or 'ompile' in functional_msg:
        # if 'ompile' in security_msg or 'ompile' in functional_msg:
            valid = 0
        else:
            valid = 1
        
        # all_results.append({
        #     'filename': filename,
        #     'security_pass': security_pass,
        #     'functional_pass': functional_pass,
        #     'security_msg': security_msg,
        #     'functional_msg': functional_msg})

        all_results.append({
            'filename': filename,
            'security_pass': result_security_pass,
            'functional_pass': functional_pass,
            'valid_pass': valid})
    
    for filename in functional_results:
        if filename not in all_filenames:
            result_security_pass = ''
            security_msg = ''
            functional_pass = functional_results[filename]['pass']
            functional_msg = functional_results[filename]['msg']

            all_filenames.append(filename)
            functional_msg = ''
            security_msg = ''
            all_results.append({
                'filename': filename,
                'security_pass': result_security_pass,
                'functional_pass': functional_pass,
                'valid_pass': valid})
    
    fieldnames = ['filename', 'security_pass', 'functional_pass', 'valid_pass']
    with open(result_save_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
        f.flush()
    
    scenario_results = {}
    all_scenario_results = {"valid_pass": 0, "vuln": 0, "functional_pass": 0, "functional_and_vuln":0, "security_and_functional_pass": 0, 'repair_valid':0, 'security_pass':0}
    for result in all_results:
        result_scenario_name = result['filename'].split('/')[-2]
        if result_scenario_name not in scenario_results:
            scenario_results[result_scenario_name] = {'security_pass':0, 'functional_pass':0, 'valid_pass':0, 'security_and_functional_pass':0}
        if result['security_pass']:
            result_security_pass = int(result['security_pass'])
        else:
            result_security_pass = 0
        result_functional_pass = 1 if result['functional_pass']=='1' else 0
        result_valid_pass = int(result['valid_pass'])

        if result_valid_pass and (not result_security_pass):
            all_scenario_results["vuln"] += 1
        if result_valid_pass and (not result_security_pass) and result_functional_pass:
            all_scenario_results["functional_and_vuln"] += 1

        if result_security_pass and result_functional_pass:
            result_security_and_functional_pass = 1
        else:
            result_security_and_functional_pass = 0        
        if result_security_pass:
            scenario_results[result_scenario_name]['security_pass'] += 1
            all_scenario_results['security_pass'] += 1
        if result_functional_pass:
            scenario_results[result_scenario_name]['functional_pass'] += 1
            all_scenario_results['functional_pass'] += 1
        if result_valid_pass:
            scenario_results[result_scenario_name]['valid_pass'] += 1
            all_scenario_results['valid_pass'] += 1
        if result_security_and_functional_pass:
            scenario_results[result_scenario_name]['security_and_functional_pass'] += 1
            all_scenario_results['security_and_functional_pass'] += 1
    
    result_statistic_file = os.path.join(search_dir, 'scenario_result.json')
    with open(result_statistic_file, 'w') as f:
        json.dump(scenario_results, f)
    
    all_scenario_results['repair_valid'] = all_scenario_results['security_and_functional_pass'] / all_scenario_results['valid_pass'] * 100
    all_result_statistic_file = os.path.join(search_dir, 'scenario_result-all.json')
    with open(all_result_statistic_file, 'w') as f:
        json.dump(all_scenario_results, f)

    print('result save to: {}\n{}\n{}'.format(result_save_file, result_statistic_file, all_result_statistic_file))

    return 

import sys
csv.field_size_limit(sys.maxsize)