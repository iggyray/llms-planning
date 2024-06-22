import os
import json
from dotenv import load_dotenv

class report_handler:
    def __init__(self, instance_number, problem_description, gt_plan) -> None:
        load_dotenv()
        self.file_path = os.getenv("DFS_PROMPT_REPORT_FILE_PATH")
        self.file_path_v2 = os.getenv("BFS_PROMPT_REPORT_FILE_PATH")
        self.instance_number = instance_number
        self.problem_description = problem_description
        self.gt_plan = gt_plan

    def load_json(self):
        file_name = f'{self.file_path}instance-{self.instance_number}.json'
        if os.path.exists(file_name):
            with open(file_name, "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "problem_description": self.problem_description,
                                "gt_plan": self.gt_plan,
                                "llm_plan": [],
                                "prompts": [],
                                }
            return structured_output
    
    def save_json(self, prompt_number, prompt_report, next_action=None, reset_llm_plan=False):
        os.makedirs(self.file_path, exist_ok=True)
        report = self.load_json()
        is_prompt_report_exists = len(report["prompts"]) >= prompt_number

        if (is_prompt_report_exists):
            target_prompt_index = prompt_number - 1
            report["prompts"][target_prompt_index] = prompt_report
        else:
            report["prompts"].append(prompt_report)
        
        if (next_action is not None):
            report["llm_plan"].append(next_action)
        
        if (reset_llm_plan):
            report["llm_plan"] = []
        
        file_name = f'{self.file_path}instance-{self.instance_number}.json'
        with open(file_name, "w") as f:
            json.dump(report, f, indent=4)
        
    def load_json_v2(self):
        file_name = f'{self.file_path_v2}instance-{self.instance_number}.json'
        if os.path.exists(file_name):
            with open(file_name, "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "problem_description": self.problem_description,
                                "gt_plan": self.gt_plan,
                                "llm_plan": '',
                                "nodes": {},
                                "prompts": [],
                                }
            return structured_output
    
    def save_json_v2(self, prompt_number, prompt_report, nodes, llm_plan=None, reset_llm_plan=False):
        os.makedirs(self.file_path_v2, exist_ok=True)
        report = self.load_json_v2()
        is_prompt_report_exists = len(report["prompts"]) >= prompt_number

        if (is_prompt_report_exists):
            target_prompt_index = prompt_number - 1
            report["prompts"][target_prompt_index] = prompt_report
        else:
            report["prompts"].append(prompt_report)
        
        if (llm_plan is not None):
            report["llm_plan"] = llm_plan
        
        if (reset_llm_plan):
            report["llm_plan"] = []
        
        report["nodes"] = nodes
        
        file_name = f'{self.file_path_v2}instance-{self.instance_number}.json'
        with open(file_name, "w") as f:
            json.dump(report, f, indent=4)