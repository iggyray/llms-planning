import os
import json
from dotenv import load_dotenv
from utils import *

class validation_handler:
    def __init__(self, config, domain, problem, instance_number, instance_dir) -> None:
        load_dotenv()
        self.config = config
        self.domain = domain
        self.problem = problem
        self.instance_number = instance_number
        self.instance_dir = instance_dir
        self.file_dir = os.getenv("VALIDATION_REPORT_FILE_DIR")
        self.file_name = os.getenv("VALIDATION_REPORT_FILE_NAME")
    
    def validate_llm_plan(self, llm_plan, gen_report=False):
        text_to_plan(llm_plan, self.problem.actions, "llm_plan", self.config) # save plan to plan file
        result = validate_plan(self.domain, self.instance_dir, 'llm_plan')
        print('[PLAN VALID]: ' + str(result))
        if not gen_report:
            return
        if (result):
            self.report_passed_instance()
        else:
            self.report_failed_instance("invalid plan")
    
    def report_passed_instance(self):
        instance_report = {
            "instance_number": self.instance_number,
            "pass": True,
        }
        validation_report = self.load_validation_report_json()
        validation_report["results"].append(instance_report)
        self.save_validation_report_json(validation_report)
    
    def report_failed_instance(self, error_message):
        instance_report = {
            "instance_number": self.instance_number,
            "pass": False,
            "details": error_message
        }
        validation_report = self.load_validation_report_json()
        validation_report["results"].append(instance_report)
        self.save_validation_report_json(validation_report)
    
    def load_validation_report_json(self):
        file_path = self.file_dir + self.file_name
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            structured_output = {
                                "results": [],
                                }
            return structured_output
        
    def save_validation_report_json(self, updated_report):
        os.makedirs(self.file_dir, exist_ok=True)
        file_path = self.file_dir + self.file_name
        with open(file_path, "w") as f:
            json.dump(updated_report, f, indent=4)