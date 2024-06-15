from dotenv import load_dotenv
import os
import yaml
from tarski.io import PDDLReader
from utils import *

class setup_handler:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.config = self.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.instance_dir = self.get_instance_dir(instance_number)
        self.instance_number = instance_number
    
    def get_config(self):
        config_file_path = os.getenv("BLOCKSWORLD3_CONFIG_DIR")
        with open(config_file_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get_instance_dir(self, instance_number):
        return os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
    
    def get_problem(self):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        return reader.parse_instance(self.instance_dir)
    
    def get_gt_plan(self):
        fast_downward_path = os.getenv("FAST_DOWNWARD_DIR")
        assert os.path.exists(fast_downward_path)
        cmd = f"{fast_downward_path} {self.domain} {self.instance_dir} --search \"astar(lmcut())\" > /dev/null 2>&1"
        os.system(cmd)
        gt_plan, gt_plan_length = get_gt_plan_description_and_length(self.config)
        return gt_plan, gt_plan_length
    
    def gen_gt_plan(self, instance_dir):
        fast_downward_path = os.getenv("FAST_DOWNWARD_DIR")
        assert os.path.exists(fast_downward_path)
        cmd = f"{fast_downward_path} {self.domain} {instance_dir} --search \"astar(lmcut())\" > /dev/null 2>&1"
        os.system(cmd)
    
    def get_zero_shot_problem_description(self):
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(self.domain)
        cur_problem = reader.parse_instance(self.instance_dir)
        INIT, GOAL = parse_problem(cur_problem, self.config, False)
        return get_problem_description(INIT, GOAL, self.config)
    
    def get_one_shot_problem_description(self):
        reader1 = PDDLReader(raise_on_error=True)
        reader2 = PDDLReader(raise_on_error=True)
        reader1.parse_domain(self.domain)
        reader2.parse_domain(self.domain)

        example_instance_number = self.instance_number + 1
        example_instance_dir = self.get_instance_dir(example_instance_number)
        self.gen_gt_plan(example_instance_dir)
        example_problem = reader1.parse_instance(example_instance_dir)
        EXAMPLE_INIT, EXAMPLE_GOAL = parse_problem(example_problem, self.config, False)
        one_shot_problem_description = get_domain_description_with_example(EXAMPLE_INIT, EXAMPLE_GOAL, self.config)
        
        self.gen_gt_plan(self.instance_dir)
        cur_problem = reader2.parse_instance(self.instance_dir)
        INIT, GOAL = parse_problem(cur_problem, self.config, False)
        one_shot_problem_description += get_problem_description_only(INIT, GOAL, self.config)
        return one_shot_problem_description