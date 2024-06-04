from prompt_generation import PromptGenerator
from response_evaluation import ResponseEvaluator
from response_generation import ResponseGenerator
from dotenv import load_dotenv
import os
import argparse

if __name__=="__main__":
    '''
    the is a simplification of the llm_plan_pipeline, specifically used for prompting llama3-80b on the blocksworld_3 domain
    '''
    load_dotenv()
    config_file = os.getenv("BLOCKSWORLD3_CONFIG_DIR")
    task_name = os.getenv("BASE_PIPELINE_TASK_NAME")
    engine = "llama3-80b"

    parser = argparse.ArgumentParser()
    parser.add_argument('--gen_prompt', type=str, default="False")
    parser.add_argument('--get_response', type=str, default="True")
    parser.add_argument('--eval_response', type=str, default="True")
    args = parser.parse_args()
    gen_prompt = eval(args.gen_prompt)
    get_response = eval(args.get_response)
    eval_response = eval(args.eval_response)
    
    if gen_prompt:
        prompt_generator = PromptGenerator(config_file, False, False, 42)
        all_instances = range(1, 101)
        for instance in all_instances:
            prompt_generator.task_1_plan_generation_v2(instance)
    
    if get_response:
        response_generator = ResponseGenerator(config_file, engine, False, False)
        target_instances = []
        response_generator.get_responses_v2(task_name, target_instances)
    
    if eval_response:
        response_evaluator = ResponseEvaluator(config_file, engine, [], False)
        response_evaluator.evaluate_plan(task_name)