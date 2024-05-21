# from ..utils.llm_utils import prompt_llama3_80b

# python3 -m plan-bench.experiments.tot_stepwise

ground_truth_plan = '(pick-up red block)\n(stack red block orange block)\n(pick-up blue block)\n(stack blue block red block)\n'
domain = '<domain>I am playing with a set of blocks where I need to arrange the blocks into stacks. Here are the actions I can do\n\nPick up a block\nUnstack a block from on top of another block\nPut down a block\nStack a block on top of another block\n\nI have the following restrictions on my actions:\nI can only pick up or unstack one block at a time.\nI can only pick up or unstack a block if my hand is empty.\nI can only pick up a block if the block is on the table and the block is clear. A block is clear if the block has no other blocks on top of it and if the block is not picked up.\nI can only unstack a block from on top of another block if the block I am unstacking was really on top of the other block.\nI can only unstack a block from on top of another block if the block I am unstacking is clear.\nOnce I pick up or unstack a block, I am holding the block.\nI can only put down a block that I am holding.\nI can only stack a block on top of another block if I am holding the block being stacked.\nI can only stack a block on top of another block if the block onto which I am stacking the block is clear.\nOnce I put down or stack a block, my hand becomes empty.\nOnce you stack a block on top of a second block, the second block is no longer clear.</domain>\n\n'
problem = '<initial-state>As initial conditions I have that, the red block is clear, the blue block is clear, the orange block is clear, the hand is empty, the red block is on the table, the blue block is on the table and the orange block is on the table.</initial-state>\n<goal-state>My goal is to have the red block on top of the orange block and the blue block on top of the red block.</goal-state>\n\n'

exp_tot_prompt = '<plan> {} </plan>\n\nConsidering the goal state and the current plan, explain 2 possible actions for step {} then conclude in the last line "The possible actions are: 1. <a> 2. <b>" where a, b are your explained actions.'

exp_vote_prompt = '<plan> {} </plan>\n\nHere are choices for step {}: {}\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is <>" where <> is the chosen choice.'

exp_validate_prompt = 'Plan:\n{}\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan <does/ does not> satisfy the goal state".'

exp_init_tot_prompt = 'What are 2 possible actions for step 1 in reaching the goal state? Explain your actions, then conclude in the last line "The possible actions are: 1. {a} 2. {b}" where a, b are the possible actions.'
# The possible actions are: 1. Pick up the red block 2. Unstack the blue block from on top of another block 3. Pick up the orange block

vote_prompt_1 = 'Here are choices for the 1st step:\n1. Pick up the red block\n2. Unstack the blue block from on top of another block\n3. Pick up the orange block\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is {s}" where s is the chosen choice.'
# The best choice is 1. Pick up the red block

validate_prompt_1 = 'Plan:\n1. Pick up the red block\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan {does/ does not} satisfy the goal state".'

tot_prompt_2 = 'Plan:\n1. Pick up the red block\n\nConsidering the goal state and the current plan, explain 3 possible actions then conclude in the last line "The possible actions are: 1. {a} 2. {b} 3. {c}" where a, b, c are your explained actions.'
# The possible actions are: 1. Put down the red block 2. Stack the red block on top of the orange block 3. Unstack a block from on top of another block

vote_prompt_2 = 'Plan:\n1. Pick up the red block\n\nHere are choices for step 2:\n1. Put down the red block\n2. Stack the red block on top of the orange block\n3. Unstack a block from on top of another block\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is {s}" where s is the chosen choice.'
# The best choice is 2. Stack the red block on top of the orange block

validate_prompt_2 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan {does/ does not} satisfy the goal state".'

tot_prompt_3 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n\nConsidering the goal state and the current plan, explain 3 possible actions then conclude in the last line "The possible actions are: 1. {a} 2. {b} 3. {c}" where a, b, c are your explained actions.'
# The possible actions are: 1. Unstack the red block from the orange block; 2. Pick up the blue block; 3. Stack the blue block on top of the red block.

vote_prompt_3 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n\nHere are choices for step3 :\n1. Unstack the red block from the orange block\n2. Pick up the blue block\n3. Stack the blue block on top of the red block.\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is {s}" where s is the chosen choice.'
# The best choice is 2: Pick up the blue block.

validate_prompt_3 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n3. Pick up the blue block\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan {does/ does not} satisfy the goal state".'

tot_prompt_4 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n3. Pick up the blue block\n\nConsidering the goal state and the current plan, explain 3 possible next actions to take then conclude in the last line "The possible actions are: 1. {a} 2. {b} 3. {c}" where a, b, c are your explained actions.'
# The possible actions are: 1. Put down the blue block 2. Stack the blue block on top of the red block 3. Unstack the orange block from under the red block

vote_prompt_4 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n3. Pick up the blue block\n\nHere are choices for step 4:\n1. Put down the blue block\n2. Stack the blue block on top of the red block\n3. Unstack the orange block from under the red block\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is {s}" where s is the chosen choice.'
# The best choice is 2. Stack the blue block on top of the red block

validate_prompt_4 = 'Plan:\n1. Pick up the red block\n2. Stack the red block on top of the orange block\n3. Pick up the blue block\n4. Stack the blue block on top of the red block\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan {does/ does not} satisfy the goal state".'

# if __name__ == "__main__":
#     response = prompt_llama3(domain + problem + tot_prompt_1)
#     print(response)