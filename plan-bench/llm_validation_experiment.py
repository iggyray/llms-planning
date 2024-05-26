import os
import yaml
import json
from dotenv import load_dotenv
from tarski.io import PDDLReader
from utils import *
from experiments.tot_stepwise import *

class llm_validation_experiment:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.config = self.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.instance_number = instance_number
        self.instance_dir = os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
        self.problem_description = self.get_problem_description()
        self.report = self.load_json()
        self.gt_plan = ""
        self.gt_plan_length = 0
        self.get_gt_plan()
        
    
    def get_config(self):
        config_file_path = os.getenv("BLOCKSWORLD3_CONFIG_DIR")
        with open(config_file_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get_problem_description(self):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        self.problem = reader.parse_instance(self.instance_dir)
        INIT, GOAL = parse_problem(self.problem, self.config, False)
        return get_problem_description(INIT, GOAL, self.config)
    
    def get_gt_plan(self):
        fast_downward_path = os.getenv("FAST_DOWNWARD_DIR")
        assert os.path.exists(fast_downward_path)
        cmd = f"{fast_downward_path} {self.domain} {self.instance_dir} --search \"astar(lmcut())\" > /dev/null 2>&1"
        os.system(cmd)
        self.gt_plan, self.gt_plan_length = get_gt_plan_description_and_length(self.config)
    
    def load_json(self):
        file_path = "results/blocksworld_3/llm_validation_experiment.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            return { "results": [] }
        
    def save_json(self, report):
        os.makedirs(f"results/blocksworld_3/", exist_ok=True)

        is_result_exists = len(self.report["results"]) >= self.instance_number
        if (is_result_exists):
            target_instance_index = self.instance_number - 1
            self.report["results"][target_instance_index] = report
        else:
            self.report["results"].append(report)
        
        file_path = "results/blocksworld_3/llm_validation_experiment.json"
        with open(file_path, "w") as f:
            json.dump(self.report, f, indent=4)
    
    def validate_prompt_llama3_80b(self):
        validate_prompt = exp_validate_prompt.format(self.gt_plan)
        prompt_with_domain = self.problem_description + validate_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        validation_line = response.splitlines()[-1].lower()
        print('[VALIDATE] ' + validation_line)
        report = {
            "instance_number": self.instance_number,
            "gt_plan_length": self.gt_plan_length,
            "llm_eval_response": True,
            "validation_line": validation_line,
            "gt_plan": self.gt_plan,
            "full_response": response,
            "prompt": validate_prompt,
        }
        if ("does not" in validation_line):
            report["llm_eval_response"] = False
        self.save_json(report)

if __name__=="__main__":
    for target_instance_number in range(1, 102):
        exp = llm_validation_experiment(target_instance_number)
        exp.validate_prompt_llama3_80b()