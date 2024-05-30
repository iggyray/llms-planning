import os
import yaml
import json
from dotenv import load_dotenv
from tarski.io import PDDLReader
from utils import *
from experiments.tot_stepwise import *

# file paths must be configured in env file before execution
# name-main idiom must be configured before execution

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
        file_path = os.getenv("TARGET_LOAD_FILE_PATH")
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
        
        file_path = os.getenv("TARGET_SAVE_FILE_PATH")
        with open(file_path, "w") as f:
            json.dump(self.report, f, indent=4)
    
    def validate_prompt_llama3_80b(self):
        validate_prompt = exp_validate_prompt.format(self.gt_plan)
        prompt_with_domain = self.problem_description + validate_prompt
        response = prompt_llama3_80b(prompt_with_domain)
        validation_line = response.splitlines()[-1].lower()
        print(f'PROGRESS: {self.instance_number}/101')
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

class result_compiler:
    def __init__(self, experiment_number) -> None:
        load_dotenv()
        self.experiment_number = experiment_number
        self.results = self.load_results()
        self.compiled_results = {
            'length_2': {
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "instances": []
            },
            "length_4": {
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "instances": []
            },
            "length_6": {
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "instances": []
            },
            "length_8": {
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "instances": []
            },
        }

    def load_results(self):
        file_path = os.getenv("TARGET_LOAD_FILE_PATH")
        file_path.format(self.experiment_number)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                json_file = json.load(f)
                return json_file["results"]
        
    def save_compiled_results(self):
        os.makedirs(f"results/blocksworld_3/", exist_ok=True)
        file_path = os.getenv("TARGET_SAVE_FILE_PATH")
        file_path.format(self.experiment_number)
        with open(file_path, "w") as f:
            json.dump(self.compiled_results, f, indent=4)
        
    def compile_by_gt_plan_length(self):
        for report in self.results:
            target_key = f"length_{report['gt_plan_length']}"
            self.compiled_results[target_key]["instances"].append(report["instance_number"])
            if report["llm_eval_response"]:
                self.compiled_results[target_key]["passed"] += 1
            else:
                self.compiled_results[target_key]["failed"] += 1
        
        for value in self.compiled_results.values():
            pass_rate = value["passed"] / (value["passed"] + value["failed"])
            value["pass_rate"] = round(pass_rate, 3)
        
        self.save_compiled_results()

class result_compiler_by_instance:
    def __init__(self) -> None:
        load_dotenv()
        self.exp_results = []
        self.load_instance_results_for_experiment(1)
        self.load_instance_results_for_experiment(2)
        self.load_instance_results_for_experiment(3)
        self.compiled_results = { "compiled_results_by_instance_number": [] }

    def load_instance_results_for_experiment(self, experiment_number):
        file_path = os.getenv("TARGET_LOAD_FILE_PATH")
        file_path.format(experiment_number)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                json_file = json.load(f)
                self.exp_results.append(json_file["results"])
    
    def save_compiled_results(self):
        os.makedirs(f"results/blocksworld_3/", exist_ok=True)
        file_path = os.getenv("TARGET_LOAD_FILE_PATH")
        with open(file_path, "w") as f:
            json.dump(self.compiled_results, f, indent=4)
        
    def compile_by_instance_number(self):
        for instance_number in range(1, 102):
            instance_array_index = instance_number - 1
            report = {
                "instance_number": instance_number,
                "gt_plan_length": self.exp_results[0][instance_array_index]["gt_plan_length"],
                "accuracy": 0,
                "results": []
            }
            for exp_number in range(0, 3):
                result = self.exp_results[exp_number][instance_array_index]["llm_eval_response"]
                report["results"].append(result)
                if (result):
                    report["accuracy"] += 0.33
            
            self.compiled_results["compiled_results_by_instance_number"].append(report)
        
        self.save_compiled_results()

if __name__=="__main__":
    pass