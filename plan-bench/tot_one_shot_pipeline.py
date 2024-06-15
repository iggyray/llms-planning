import math
from dotenv import load_dotenv
import os
from utils import *
from experiments.tot_stepwise import *
from handler_setup import setup_handler
from handler_report import report_handler
from handler_validation import validation_handler

class tot_one_shot_pipeline:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        setup = setup_handler(instance_number)
        self.config = setup.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.problem = setup.get_problem()
        self.instance_dir = os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
        self.gt_plan, self.gt_plan_length = setup.get_gt_plan()
        self.problem_description = setup.get_one_shot_problem_description()
        self.validator = validation_handler(self.config, self.domain, self.problem, instance_number, self.instance_dir)
        self.reporter = report_handler(instance_number, self.problem_description, self.gt_plan)
        self.tot_state = self.reporter.load_json()
    
    def update_tot_state(self, prompt_number, prompt_report, next_action=None, reset_llm_plan=False):
        self.reporter.save_json(prompt_number, prompt_report, next_action, reset_llm_plan)
        self.tot_state = self.reporter.load_json()

    def get_llm_action_description(self, llm_raw_response):
        pddl_action, _ = text_to_plan(llm_raw_response, self.problem.actions, "llm_plan", self.config)
        return get_action_description(self.config, pddl_action)
    
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
        reset_llm_plan = True
        self.update_tot_state(prompt_number, report,  None, reset_llm_plan)
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
        self.update_tot_state(prompt_number, report)

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
            self.update_tot_state(prompt_number + 1, vote_report, new_action)
            self.validate_prompt_llama3_80b(prompt_number + 2)

    def vote_prompt_llama3_80b(self, prompt_number):
        tot_prompt_index = prompt_number - 2
        possible_actions = self.tot_state["prompts"][tot_prompt_index]["response"]
        llm_plan = ''.join(self.tot_state["llm_plan"])
        vote_prompt = exp_vote_prompt_v2.format(llm_plan, possible_actions)
        prompt_with_domain = self.problem_description + vote_prompt
        retry_count = 0
        while retry_count < 3:
            try:
                response = prompt_llama3_80b(prompt_with_domain)
                voted_action = response.lower().split("the best action is")[-1].replace('*', '')
                print("[VOTE] " + voted_action)
                new_action = self.get_llm_action_description(voted_action)
                report = {
                    "prompt_number": prompt_number,
                    "type": 'vote',
                    "prompt": vote_prompt,
                    "response": voted_action,
                }
                retry_count += 3 # exit while loop
                self.update_tot_state(prompt_number, report, new_action)
                self.validate_prompt_llama3_80b(prompt_number + 1)
            except Exception:
                retry_count += 1
                if (retry_count == 3):
                    raise Exception
                print('SYNTAX ERROR, RETRYING')

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
        self.update_tot_state(prompt_number, report)

        if ("does not" in validation_line and math.ceil(prompt_number/3) < self.gt_plan_length * 2):
            self.tot_prompt_llama3_80b(prompt_number + 1)
        else:
            self.validator.validate_llm_plan(llm_plan, True)
    
if __name__=="__main__":
    target_instances = []

    try:
        for index, target_instance_number in enumerate(target_instances, start=1):
            print(f'[INSTANCE NUMBER]: {target_instance_number} || [PROGRESS]: {index} / {len(target_instances)}')
            tot = tot_one_shot_pipeline(target_instance_number)
            try:
                tot.init_prompt_llama3_80b()
            except:
                print('SYNTAX ERROR')
                tot.report_failed_instance("syntax error")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")