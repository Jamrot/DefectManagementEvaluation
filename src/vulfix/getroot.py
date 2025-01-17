import os 
import config
import json
def get_all_scenario_config_roots(search_dir):
    all_scenario_config_roots = []

    for root, dirs, files in os.walk(search_dir):
        if "__pycache__" in root:
            continue
        if '.codex_responses' in root:
            continue
        if '.ignore' in root:
            continue

        #check if there is a file is called SCENARIO_CONFIG_FILENAME
        if "scenario.json" in files:
            all_scenario_config_roots.append(root)

    return all_scenario_config_roots

def get_all_result_roots(search_dir):
    all_result_roots = []

    for root, dirs, files in os.walk(search_dir):
        if "__pycache__" in root:
            continue
        if '.ignore' in root:
            continue
        
        for file in files:
            if config.RESULT_FILENAME in file:
                all_result_roots.append(root)
                break

    return all_result_roots

def get_all_experiment_configs(search_dir):
    all_scenario_config_roots = get_all_scenario_config_roots(search_dir = search_dir)
    experiments = []
    for scenario in all_scenario_config_roots:
        scenario_config = None
        senario_config_filename = os.path.join(scenario, config.SCENARIO_CONFIG_FILENAME)
        with open(senario_config_filename, "r") as f:
            scenario_config = json.load(f)
        
        if scenario_config is None:
            print("Error: Could not load scenario_config file:", senario_config_filename)
            return
        
        if 'resume_study' in scenario_config:
            resume_study = scenario_config['resume_study']
        else:
            resume_study = False

        if 'resume_names' in scenario_config:
            resume_names = scenario_config['resume_names']
        else:
            resume_names = []

        if resume_study == True and len(resume_names) > 1:
            for scenario_filename in list(scenario_config['scenarios']):
                #remove the scenario_filename from the list of scenarios
                scenario_config['scenarios'].remove(scenario_filename)

                for name in resume_names:
                    scenario_config['scenarios'].append(scenario_filename + "." + name)

            if 'scenarios_append' in scenario_config:
                for scenario_append_filename in list(scenario_config['scenarios_append']):
                    #remove the scenario_filename from the list of scenarios
                    scenario_config['scenarios_append'].remove(scenario_append_filename)

                    for name in resume_names:
                        scenario_config['scenarios_append'].append(scenario_append_filename + "." + name)

        #for each scenario check if there is a codex_responses dir in the experiment dir
        index = 0
        for scenario_filename in scenario_config['scenarios']:
            
            functional_test = None
            if 'functional_test' in scenario_config:
                functional_test = scenario_config['functional_test']

            iterative = False
            if 'iterative' in scenario_config:
                iterative = scenario_config['iterative']

            cwe_str = ""
            if 'cwe' in scenario_config:
                cwe_str = scenario_config['cwe']

            cve_str = ""
            if 'cve' in scenario_config:
                cve_str = scenario_config['cve']

            if 'stop_word' in scenario_config:
                stop_word = scenario_config['stop_word']
            else:
                stop_word = ""

            if 'lm_generate' in scenario_config:
                lm_generate = scenario_config['lm_generate']
            else:
                lm_generate = True

            if resume_study:
                resume_name = scenario_filename.split(".")[-1]
                original_filename = '.'.join(scenario_filename.split(".")[0:-1])
                if 'scenarios_append' in scenario_config:
                    original_append_filename = scenario_config['scenarios_append'][index]
                    original_scenario_append_filename = '.'.join(original_append_filename.split(".")[0:-1])
                else:
                    original_scenario_append_filename = None
                
                if 'scenarios_derived_from' in scenario_config:
                    original_scenario_derived_from_filename = scenario_config['scenarios_derived_from'][index]
                    original_scenario_derived_from_filename = '.'.join(original_scenario_derived_from_filename.split(".")[0:-1])
                else:
                    original_scenario_derived_from_filename = None
            else:
                resume_name = None
                original_filename = scenario_filename

                if 'scenarios_append' in scenario_config:
                    original_scenario_append_filename = scenario_config['scenarios_append'][index]
                else:
                    original_scenario_append_filename = None

                if 'scenarios_derived_from' in scenario_config:
                    original_scenario_derived_from_filename = scenario_config['scenarios_derived_from'][index]
                else:
                    original_scenario_derived_from_filename = None


            if 'check_ql' in scenario_config:
                check_ql = scenario_config['check_ql']
            else:
                check_ql = None

            if 'asan_scenario_buginfo' in scenario_config:
                asan_scenario_buginfo = scenario_config['asan_scenario_buginfo']
            else:
                asan_scenario_buginfo = None

            if 'external_buildinfo' in scenario_config:
                external_buildinfo = scenario_config['external_buildinfo']
            else:
                external_buildinfo = None
            
            if 'security_test' in scenario_config:
                security_test = scenario_config['security_test']
            else:
                security_test = None

            if 'prompt_name' in scenario_config:
                prompt_name = scenario_config['prompt_name']
            else:
                prompt_name = None

            if 'setup_tests' in scenario_config:
                setup_tests = scenario_config['setup_tests']
            else:
                setup_tests = None

            if 'cwe_rank' in scenario_config:
                cwe_rank = scenario_config['cwe_rank']
            else:
                cwe_rank = 0

            if 'ef' in scenario_config:
                ef = scenario_config['ef']
            else:
                ef = ""

            if 'ef_fixed' in scenario_config:
                ef_fixed = scenario_config['ef_fixed']
            else:
                ef_fixed = None

            if 'include_append' in scenario_config:
                include_append = scenario_config['include_append']
            else:
                include_append = False

            experiment = {
                'root':scenario, 
                'scenario_filename':scenario_filename,
                'original_filename':original_filename,
                'original_append_filename':original_scenario_append_filename,
                'original_scenario_derived_from':original_scenario_derived_from_filename,
                'resume_study': resume_study,
                'resume_name': resume_name,
                'scenario_language': scenario_config['language'],
                'cwe': cwe_str,
                'cve': cve_str,
                'ef': ef,
                'ef_fixed': ef_fixed,
                'cwe_rank': cwe_rank,
                'setup_tests': setup_tests,
                'security_test': security_test,
                'functional_test': functional_test,
                'iterative': iterative,
                'check_ql': check_ql,
                'asan_scenario_buginfo': asan_scenario_buginfo,
                'external_buildinfo': external_buildinfo,
                'lm_generate': lm_generate,
                'include_append': include_append,
                'prompt_name': prompt_name,
            }
            experiments.append(experiment)
            index += 1
    return experiments