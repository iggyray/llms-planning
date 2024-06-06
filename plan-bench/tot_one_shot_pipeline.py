import math
from dotenv import load_dotenv
import yaml
import os
from tarski.io import PDDLReader
import json
from utils import *
from experiments.tot_stepwise import *

class tot_one_shot_pipeline:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.config = self.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.instance_number = instance_number
        self.instance_dir = self.get_instance_dir(instance_number)
        self.gt_plan = ""
        self.gt_plan_length = 0
        self.problem_description = ""
        self.get_problem_description_with_example()
        self.tot_state = self.load_json()

    def get_config(self):
        config_file_path = os.getenv("BLOCKSWORLD3_CONFIG_DIR")
        with open(config_file_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get_instance_dir(self, instance_number):
        return os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
    
    def get_gt_plan(self, instance_dir):
        fast_downward_path = os.getenv("FAST_DOWNWARD_DIR")
        assert os.path.exists(fast_downward_path)
        cmd = f"{fast_downward_path} {self.domain} {instance_dir} --search \"astar(lmcut())\" > /dev/null 2>&1"
        os.system(cmd)
        self.gt_plan, self.gt_plan_length = get_gt_plan_description_and_length(self.config)
    
    def get_problem_description_with_example(self):
        self.problem_description = self.get_example_problem_description()
        self.get_gt_plan(self.instance_dir)
        self.problem_description += self.get_cur_problem_states()
    
    def get_cur_problem_states(self):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        self.problem = reader.parse_instance(self.instance_dir)
        INIT, GOAL = parse_problem(self.problem, self.config, False)
        return get_problem_description_only(INIT, GOAL, self.config)
    
    def get_example_problem_description(self):
        example_instance_number = self.instance_number + 1
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        example_instance_dir = self.get_instance_dir(example_instance_number)
        self.get_gt_plan(example_instance_dir)
        example_problem = reader.parse_instance(example_instance_dir)
        INIT, GOAL = parse_problem(example_problem, self.config, False)
        return get_domain_description_with_example(INIT, GOAL, self.config)
    
    def load_json(self):
        file_name = f'instance-{self.instance_number}'
        if os.path.exists(f"prompts/blocksworld_3_tot_one_shot/" + file_name + ".json"):
            with open(f"prompts/blocksworld_3_tot_one_shot/" + file_name + ".json", "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "problem_description": self.problem_description,
                                "gt_plan": self.gt_plan,
                                "llm_plan": [],
                                "prompts": [],
                                }
            return structured_output
    
    def save_json(self, prompt_number, prompt_report, next_action=None):
        os.makedirs(f"prompts/blocksworld_3_tot_one_shot/", exist_ok=True)

        is_prompt_report_exists = len(self.tot_state["prompts"]) >= prompt_number
        if (is_prompt_report_exists):
            target_prompt_index = prompt_number - 1
            self.tot_state["prompts"][target_prompt_index] = prompt_report
        else:
            self.tot_state["prompts"].append(prompt_report)

        if (next_action is not None):
            self.tot_state["llm_plan"].append(next_action)
        file_name = f'instance-{self.instance_number}'
        with open(f"prompts/blocksworld_3_tot_one_shot/" + file_name + ".json", "w") as f:
            json.dump(self.tot_state, f, indent=4)

    def get_llm_action_description(self, llm_raw_response):
        pddl_action, _ = text_to_plan(llm_raw_response, self.problem.actions, "llm_plan", self.config)
        return get_action_description(self.config, pddl_action)
    
    def load_validation_report_json(self):
        file_name = os.getenv("TOT_ONE_SHOT_VALIDATION_REPORT_FILE_NAME")
        if os.path.exists(f"results/blocksworld_3/" + file_name):
            with open(f"results/blocksworld_3/" + file_name, "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "results": [],
                                }
            return structured_output
        
    def save_validation_report_json(self, updated_report):
        os.makedirs("results/blocksworld_3/", exist_ok=True)
        file_name = os.getenv("TOT_ONE_SHOT_VALIDATION_REPORT_FILE_NAME")
        with open(f"results/blocksworld_3/" + file_name, "w") as f:
            json.dump(updated_report, f, indent=4)
    
    def validate_llm_plan(self):
        llm_plan = ''.join(self.tot_state["llm_plan"])
        text_to_plan(llm_plan, self.problem.actions, "llm_plan", self.config) # save plan to plan file
        result = validate_plan(self.domain, self.instance_dir, 'llm_plan')
        print('[PLAN VALID]: ' + str(result))
        if (result):
            self.report_passed_instance()
        else:
            self.report_failed_instance("invalid plan")

    def report_failed_instance(self, error_message):
        instance_report = {
            "instance_number": self.instance_number,
            "pass": False,
            "details": error_message
        }
        validation_report = self.load_validation_report_json()
        validation_report["results"].append(instance_report)
        self.save_validation_report_json(validation_report)
    
    def report_passed_instance(self):
        instance_report = {
            "instance_number": self.instance_number,
            "pass": True,
        }
        validation_report = self.load_validation_report_json()
        validation_report["results"].append(instance_report)
        self.save_validation_report_json(validation_report)
    
    def init_prompt_llama3_80b(self):
        prompt_number = 1
        prompt_with_domain = self.problem_description + exp_init_tot_prompt_v2
        response = prompt_llama3_80b(prompt_with_domain)
        possible_actions = response.split("The possible actions are: ")[-1]
        report = {
            "prompt_number": prompt_number,
            "prompt": exp_init_tot_prompt,
            "response": possible_actions
        }
        print("[INIT] " + possible_actions)
        self.save_json(prompt_number, report,  '')
        self.vote_prompt_llama3_80b(prompt_number + 1)

    def tot_prompt_llama3_80b(self, prompt_number):
        llm_plan = ''.join(self.tot_state["llm_plan"])
        prompt = exp_tot_prompt_v2.format(llm_plan)
        prompt_with_domain = self.problem_description + prompt
        response = prompt_llama3_80b(prompt_with_domain)
        possible_actions = response.split("The possible actions are: ")[-1]
        report = {
            "prompt_number": prompt_number,
            "type": 'TOT',
            "prompt": prompt,
            "response": possible_actions
        }
        print("[TOT] " + possible_actions)
        self.save_json(prompt_number, report)

        if ('2' in possible_actions):
            self.vote_prompt_llama3_80b(prompt_number + 1)
        else:
            vote_report = {
            "prompt_number": prompt_number + 1,
            "type": 'skipped vote',
            "prompt": 'NO PROMPT AS ONLY 1 OPTION WAS PROVIDED',
            "response": possible_actions,
            }
            new_action = self.get_llm_action_description(possible_actions)
            self.save_json(prompt_number + 1, vote_report, new_action)
            self.validate_prompt_llama3_80b(prompt_number + 2)

    def vote_prompt_llama3_80b(self, prompt_number):
        tot_prompt_index = prompt_number - 2
        possible_actions = self.tot_state["prompts"][tot_prompt_index]["response"]
        vote_prompt = exp_vote_prompt_v2.format(self.tot_state["llm_plan"], possible_actions)
        prompt_with_domain = self.problem_description + vote_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        voted_action = response.lower().split("the best action is")[-1].replace('*', '')
        print("[VOTE] " + voted_action)
        updated_plan = self.tot_state["llm_plan"] + self.get_llm_action_description(voted_action)
        report = {
            "prompt_number": prompt_number,
            "type": 'vote',
            "prompt": vote_prompt,
            "response": voted_action,
        }
        self.save_json(prompt_number, report, updated_plan)
        self.validate_prompt_llama3_80b(prompt_number + 1)

    def validate_prompt_llama3_80b(self, prompt_number):
        llm_plan = ''.join(self.tot_state["llm_plan"])
        validate_prompt = exp_validate_prompt_v2.format(llm_plan)
        prompt_with_domain = self.problem_description + validate_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        validation_line = response.splitlines()[-1].lower()
        print('[VALIDATE] ' + validation_line)
        report = {
            "prompt_number": prompt_number,
            "type": 'validate',
            "prompt": validate_prompt,
            "response": validation_line,
        }
        self.save_json(prompt_number, report)

        if ("does not" in validation_line and math.ceil(prompt_number/3) < self.gt_plan_length * 2):
            self.tot_prompt_llama3_80b(prompt_number + 1)
        else:
            return
    
if __name__=="__main__":
    target_instances = []

    try:
        for index, target_instance_number in enumerate(target_instances, start=1):
            print(f'[INSTANCE NUMBER]: {target_instance_number} || [PROGRESS]: {index} / {len(target_instances)}')
            tot = tot_one_shot_pipeline(target_instance_number)
            try:
                tot.init_prompt_llama3_80b()
                tot.validate_llm_plan()
            except:
                print('SYNTAX ERROR')
                tot.report_failed_instance("syntax error")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")