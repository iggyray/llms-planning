import math
from dotenv import load_dotenv
import os
from utils import *
from experiments.tot_stepwise import *
from handler_setup import setup_handler
from handler_report import report_handler
from handler_validation import validation_handler
from handler_nodes import node_db

class tot_blocksworld_3:
    def __init__(self, instance_number) -> None:
        load_dotenv()
        self.setup = setup_handler(instance_number)
        self.config = self.setup.get_config()
        self.domain = f'./instances/{self.config["domain_file"]}'
        self.problem = self.setup.get_problem()
        self.instance_dir = os.getenv("BLOCKSWORLD3_INSTANCE_DIR").format(instance_number)
        self.gt_plan, self.depth_limit = self.setup.get_gt_plan()
        self.domain_description = self.setup.get_zero_shot_domain_description()
        self.init_state, self.goal_state = self.setup.get_state_descriptions()
        self.validator = validation_handler(self.config, self.domain, self.problem, instance_number, self.instance_dir)
        self.reporter = report_handler(instance_number, self.domain_description, self.gt_plan)
        init_state, _ = self.setup.get_parsed_states()
        self.node_db = node_db(init_state)
        self.tot_queue = []
        self.prompt_number = None
    
    def update_report(self, prompt_report, llm_plan=None, reset_llm_plan=False):
        updated_nodes = self.node_db.get_all_nodes()
        self.reporter.save_json_v2(self.prompt_number, prompt_report, updated_nodes, llm_plan, reset_llm_plan)

    def get_llm_action_description(self, llm_raw_response):
        pddl_action, _ = text_to_plan(llm_raw_response, self.problem.actions, "llm_plan", self.config)
        return get_action_description(self.config, pddl_action)
    
    def get_formatted_actions_from_llm(self, prompt):
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
    
    def execute(self):
        if self.prompt_number is None:
            cur_node_id = "0" # root node id is '0'
        else:
            cur_node_id = self.tot_queue[0]

        # check if depth limit has been reached
        cur_node_depth = self.node_db.get_cur_node_depth(cur_node_id)
        if cur_node_depth == self.depth_limit:
            print('[INIT PLAN VALIDATOR]')
            llm_plans = []
            for node_id in self.tot_queue:
                llm_plan = self.node_db.get_plan(node_id)
                llm_plans.append(llm_plan)
            self.update_report({},  llm_plans, False)
            self.validator.validate_llm_plans(llm_plans)
            return
            
        # update state
        if cur_node_id != '0':
            self.tot_queue.pop(0)
            self.update_predicate_state_prompt(cur_node_id)
            updated_init_state = self.node_db.get_state_from_id(cur_node_id)
            self.init_state, _ = self.setup.get_state_descriptions(updated_init_state)

        # action generation
        self.action_generation_prompt(cur_node_id, cur_node_depth)

        if len(self.tot_queue) == 0:
            self.validator.report_failed_instance('tot queue empty')
            return
        
        self.execute()
        
        
    def action_generation_prompt(self, node_id, node_depth):
        if self.prompt_number is None:
            self.prompt_number = 1
        else:
            self.prompt_number += 1
        prompt_with_domain = self.domain_description + exp_bfs_init_tot_example + self.init_state + exp_bfs_init_tot_prompt
        reset_llm_plan = self.prompt_number == 1
        report = {
            "prompt_number": self.prompt_number,
            "type": 'TOT',
            "prompt": prompt_with_domain,
        }
        self.update_report(report,  None, reset_llm_plan)
        formatted_actions = self.get_formatted_actions_from_llm(prompt_with_domain)
        child_node_id_list = []
        for formatted_action in formatted_actions:
            new_node_id = self.node_db.add_node(formatted_action, node_id)
            child_node_id_list.append(new_node_id)
        
        formatted_possible_actions_list = list(map(self.node_db.get_action_from_id, child_node_id_list))
        print(f"[TOT] depth: {node_depth} | " + ''.join(formatted_possible_actions_list).replace('\n', '; '))
        report["response"] = formatted_possible_actions_list
        self.update_report(report,  None, reset_llm_plan)

        # add actions to ToT queue
        for node_id in child_node_id_list:
            target_node_action = self.node_db.get_action_from_id(node_id)
            target_action = target_node_action.replace('\n', '')
            gt_plan_actions = self.gt_plan.split('\n')
            if target_action == gt_plan_actions[node_depth]:
                self.tot_queue.append(node_id)
    
    def update_predicate_state_prompt(self, node_id):
        self.prompt_number += 1
        init_state = self.node_db.get_parent_state_from_id(node_id)
        node_action = self.node_db.get_action_from_id(node_id)
        update_state_prompt = self.setup.get_update_state_instruction(init_state, node_action)
        start_delim = '<state>'
        end_delim = '</state>'
        retry_count = 0
        while retry_count < 3:
            response = prompt_llama3_80b(update_state_prompt)
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
            "prompt": update_state_prompt,
            "init_state": init_state,
            "action": node_action,
            "response": updated_state,
        }
        self.update_report(report)
    
if __name__=="__main__":
    target_instances = []
    for index, target_instance_number in enumerate(target_instances, start=1):
        print(f'[INSTANCE NUMBER]: {target_instance_number} || [PROGRESS]: {index} / {len(target_instances)}')
        tot = tot_blocksworld_3(target_instance_number)
        tot.execute()