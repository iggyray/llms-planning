# open pddl instance
# open json file (for logging)
# generate starting prompt

from dotenv import load_dotenv
import yaml
import os
from tarski.io import PDDLReader
import json
from utils import *
from experiments.tot_stepwise import *

class tot_pipeline:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.config = self.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.instance_number = instance_number
        self.instance_dir = self.get_instance_dir(instance_number)
        self.problem_description = self.get_problem_description()
        self.problem
        self.tot_state = self.load_json()

    def get_config(self):
        config_file_path = os.getenv("BLOCKSWORLD3_CONFIG_DIR")
        with open(config_file_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get_instance_dir(self, instance_number):
        instance_dir = os.getenv("BLOCKSWORLD3_INSTANCE_DIR")
        return instance_dir.format(instance_number)
    
    def get_gt_plan(self):
        fast_downward_path = os.getenv("FAST_DOWNWARD_DIR")
        assert os.path.exists(fast_downward_path)
        cmd = f"{fast_downward_path} {self.domain} {self.instance_dir} --search \"astar(lmcut())\" > /dev/null 2>&1"
        os.system(cmd)
        return get_gt_plan_description(self.config)
    
    def get_problem_description(self):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        self.problem = reader.parse_instance(self.instance_dir)
        INIT, GOAL = parse_problem(self.problem, self.config, False)
        return get_problem_description(INIT, GOAL, self.config)
    
    def load_json(self):
        file_name = f'instance-{self.instance_number}'
        if os.path.exists(f"prompts/blocksworld_3_tot/" + file_name + ".json"):
            with open(f"prompts/blocksworld_3_tot/" + file_name + ".json", "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "problem_description": self.problem_description,
                                "gt_plan": self.get_gt_plan(),
                                "llm_plan": "",
                                "prompts": [],
                                }
            return structured_output
    
    def save_json(self, prompt_number, prompt_report, updated_plan=None):
        os.makedirs(f"prompts/blocksworld_3_tot/", exist_ok=True)

        is_prompt_report_exists = len(self.tot_state["prompts"]) >= prompt_number
        if (is_prompt_report_exists):
            target_prompt_index = prompt_number - 1
            self.tot_state["prompts"][target_prompt_index] = prompt_report
        else:
            self.tot_state["prompts"].append(prompt_report)

        if (updated_plan is not None):
            self.tot_state["llm_plan"] = updated_plan
        file_name = f'instance-{self.instance_number}'
        with open(f"prompts/blocksworld_3_tot/" + file_name + ".json", "w") as f:
            json.dump(self.tot_state, f, indent=4)

    def get_llm_action_description(self, llm_raw_response):
        pddl_action, _ = text_to_plan(llm_raw_response, self.problem.actions, "llm_plan", self.config)
        return get_action_description(self.config, pddl_action)
    
    def init_prompt_llama3_80b(self):
        prompt_number = 1
        prompt_with_domain = self.problem_description + exp_init_tot_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        possible_actions = response.split("The possible actions are: ")[-1]
        report = {
            "prompt_number": prompt_number,
            "prompt": exp_init_tot_prompt,
            "response": possible_actions
        }
        print("[INIT] " + possible_actions)
        self.save_json(prompt_number, report)
        self.vote_prompt_llama3_80b(prompt_number + 1)

    def tot_prompt_llama3_80b(self, prompt_number):
        prompt = exp_tot_prompt.format(self.tot_state["llm_plan"], "2")
        prompt_with_domain = self.problem_description + prompt
        response = prompt_llama3_80b(prompt_with_domain)
        possible_actions = response.split("The possible actions are: ")[-1]
        report = {
            "prompt_number": prompt_number,
            "prompt": prompt,
            "response": possible_actions
        }
        print("[TOT] " + possible_actions)
        self.save_json(prompt_number, report)
        self.vote_prompt_llama3_80b(prompt_number + 1)

    def vote_prompt_llama3_80b(self, prompt_number):
        tot_prompt_index = prompt_number - 2
        possible_actions = self.tot_state["prompts"][tot_prompt_index]["response"]
        vote_prompt = exp_vote_prompt.format(possible_actions)
        prompt_with_domain = self.problem_description + vote_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        voted_action = response.lower().split("the best choice is")[-1]
        print("[VOTE] " + voted_action)
        updated_plan = self.tot_state["llm_plan"] + self.get_llm_action_description(voted_action)
        report = {
            "prompt_number": prompt_number,
            "prompt": vote_prompt,
            "response": voted_action,
        }
        self.save_json(prompt_number, report, updated_plan)
        self.validate_prompt_llama3_80b(prompt_number + 1)

    def validate_prompt_llama3_80b(self, prompt_number):
        validate_prompt = exp_validate_prompt.format(self.tot_state["llm_plan"])
        prompt_with_domain = self.problem_description + validate_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        validation_line = response.splitlines()[-1].lower()
        print('[VALIDATE] ' + validation_line)
        report = {
            "prompt_number": prompt_number,
            "prompt": validate_prompt,
            "response": validation_line,
        }
        self.save_json(prompt_number, report)

        if ("does not" in validation_line):
            self.tot_prompt_llama3_80b(prompt_number + 1)
        else:
            return
    
if __name__=="__main__":
    target_instance_number = 1
    tot = tot_pipeline(target_instance_number)
    tot.init_prompt_llama3_80b()
