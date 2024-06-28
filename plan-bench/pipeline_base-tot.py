import math
from dotenv import load_dotenv
import os
from utils import *
from experiments.tot_stepwise import *
from handler_setup import setup_handler
from handler_report import report_handler
from handler_validation import validation_handler
from handler_nodes import node_db

class base_tot_bfs_pipeline:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.setup = setup_handler(instance_number)
        self.config = self.setup.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.problem = self.setup.get_problem()
        self.instance_dir = os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
        self.gt_plan, self.depth_limit = self.setup.get_gt_plan()
        self.problem_description = self.setup.get_one_shot_problem_description(True)
        self.validator = validation_handler(self.config, self.domain, self.problem, instance_number, self.instance_dir)
        self.reporter = report_handler(instance_number, self.problem_description, self.gt_plan)
        init_state, _ = self.setup.get_parsed_states()
        self.node_db = node_db(init_state)
        self.cur_node_id = "0"
        self.tot_queue = []
        self.prompt_number = None
        self.cur_depth = 0
    
    def update_tot_state(self, prompt_report, llm_plan=None, reset_llm_plan=False):
        updated_nodes = self.node_db.get_all_nodes()
        self.reporter.save_json_v2(self.prompt_number, prompt_report, updated_nodes, llm_plan, reset_llm_plan)

    def get_llm_action_description(self, llm_raw_response):
        pddl_action, _ = text_to_plan(llm_raw_response, self.problem.actions, "llm_plan", self.config)
        return get_action_description(self.config, pddl_action)
    
    def get_formatted_actions_from_tot_response(self, prompt):
        retry_count = 0
        while retry_count < 3:
            formatted_action_list = []
            try:
                response = prompt_llama3_80b(prompt)
                possible_actions = response.lower().split("the possible actions are:")[-1]
                possible_actions_list = possible_actions.split('\n')
                
                for action in possible_actions_list:
                    if action.strip() == '':
                        continue
                    formatted_action = self.get_llm_action_description(action)
                    formatted_action_list.append(formatted_action)
                return formatted_action_list
            except:
                if (len(formatted_action_list) > 0):
                    return formatted_action_list
                print('[RETRY TOT]')
                print(response)
                retry_count += 1
                if (retry_count == 3):
                    self.validator.report_failed_instance('failed to get formatted action from tot response')
                    raise Exception('failed to get formatted action from tot response')
    
    def tot_prompt(self):
        if self.prompt_number is None:
            self.prompt_number = 1
        else:
            self.prompt_number += 1
            self.cur_node_id = self.tot_queue[0]
            self.tot_queue.pop(0)
            updated_init_state = self.node_db.get_state_from_id(self.cur_node_id)
            self.problem_description = self.setup.get_updated_one_shot_problem_description(updated_init_state, True)

        cur_node_depth = self.node_db.get_cur_node_depth(self.cur_node_id)
        if cur_node_depth == self.depth_limit: # all nodes in depth_limit have been generated, no need TOT
            llm_plans = []
            for node_id in node_id_list:
                llm_plan = self.node_db.get_plan(node_id)
                llm_plans.append(llm_plan)
            self.update_tot_state(report,  llm_plans, reset_llm_plan)
            self.validator.validate_llm_plans(llm_plans)
            return
        
        prompt_with_domain = self.problem_description + exp_bfs_init_tot_prompt
        reset_llm_plan = self.prompt_number == 1
        report = {
            "prompt_number": self.prompt_number,
            "type": 'TOT',
            "prompt": prompt_with_domain,
        }
        self.update_tot_state(report,  None, reset_llm_plan)
        formatted_actions = self.get_formatted_actions_from_tot_response(prompt_with_domain)
        node_id_list = []
        for formatted_action in formatted_actions:
            new_node_id = self.node_db.add_node(formatted_action, self.cur_node_id)
            node_id_list.append(new_node_id)
        
        formatted_possible_actions_list = list(map(self.node_db.get_action_from_id, node_id_list))
        print("[TOT] " + ''.join(formatted_possible_actions_list))
        report["response"] = formatted_possible_actions_list
        self.update_tot_state(report,  None, reset_llm_plan)
        
        for node_id in node_id_list:
                self.validate_action_prompt(node_id)
                if node_id in self.tot_queue:
                    self.get_updated_state_from_action_prompt(node_id)

        if len(self.tot_queue) > 0:
            self.tot_prompt()
        else:
            self.validator.report_failed_instance('tot queue empty')
            return
    
    def get_updated_state_from_action_prompt(self, node_id):
        self.prompt_number += 1
        init_state = self.node_db.get_parent_state_from_id(node_id)
        node_action = self.node_db.get_action_from_id(node_id)
        get_state_prompt = self.setup.get_update_state_instruction(init_state, node_action)
        start_delim = '<state>'
        end_delim = '</state>'
        retry_count = 0
        while retry_count < 3:
            response = prompt_llama3_80b(get_state_prompt)
            if start_delim in response:
                break
            else:
                print("[RETRY STATE UPDATE]")
                retry_count += 1
        else:
            raise Exception('update state prompt exceeded retries')
        start_index = response.find(start_delim) + len(start_delim)
        end_index = response.find(end_delim, start_index)
        updated_state = response[start_index:end_index]
        self.node_db.update_node_state(node_id, updated_state)
        print('[STATE UPDATE] success')
        report = {
            "prompt_number": self.prompt_number,
            "type": 'state',
            "prompt": get_state_prompt,
            "response": updated_state,
        }
        self.update_tot_state(report)
    
    def validate_action_prompt(self, node_id):
        self.prompt_number += 1
        node_action = self.node_db.get_action_from_id(node_id)
        # latest_state = self.node_db.get_state_from_id(node_id)
        vote_prompt = exp_bfs_vote_prompt_v2.format(node_action)
        prompt_with_domain = self.problem_description + vote_prompt
        retry_count = 0
        while retry_count < 3:
            response = prompt_llama3_80b(prompt_with_domain)
            vote_line = response.splitlines()[-1].lower()
            if ("continue the plan" in vote_line or "re-evaluate the plan" in vote_line):
                break
            else:
                print('[RETRY VOTE]')
                retry_count += 1
        else:
            raise Exception('vote prompt exceeded retries')
        print('[VOTE] ' + vote_line)
        report = {
            "prompt_number": self.prompt_number,
            "type": 'vote',
            "prompt": vote_prompt,
            "response": vote_line,
        }
        self.update_tot_state(report)
        if ("re-evaluate the plan" in vote_line):
            return
        self.tot_queue.append(node_id)
    
if __name__=="__main__":
    target_instances = [
      8
    ]
    for index, target_instance_number in enumerate(target_instances, start=1):
        print(f'[INSTANCE NUMBER]: {target_instance_number} || [PROGRESS]: {index} / {len(target_instances)}')
        tot = base_tot_bfs_pipeline(target_instance_number)
        tot.tot_prompt()