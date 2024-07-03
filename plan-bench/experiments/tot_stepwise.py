# from ..utils.llm_utils import prompt_llama3_80b
# python3 -m plan-bench.experiments.tot_stepwise

ground_truth_plan = '(pick-up red block)\n(stack red block orange block)\n(pick-up blue block)\n(stack blue block red block)\n'
domain = '<domain>I am playing with a set of blocks where I need to arrange the blocks into stacks. Here are the actions I can do\n\nPick up a block\nUnstack a block from on top of another block\nPut down a block\nStack a block on top of another block\n\nI have the following restrictions on my actions:\nI can only pick up or unstack one block at a time.\nI can only pick up or unstack a block if my hand is empty.\nI can only pick up a block if the block is on the table and the block is clear. A block is clear if the block has no other blocks on top of it and if the block is not picked up.\nI can only unstack a block from on top of another block if the block I am unstacking was really on top of the other block.\nI can only unstack a block from on top of another block if the block I am unstacking is clear.\nOnce I pick up or unstack a block, I am holding the block.\nI can only put down a block that I am holding.\nI can only stack a block on top of another block if I am holding the block being stacked.\nI can only stack a block on top of another block if the block onto which I am stacking the block is clear.\nOnce I put down or stack a block, my hand becomes empty.\nOnce you stack a block on top of a second block, the second block is no longer clear.</domain>\n\n'
problem = '<initial-state>As initial conditions I have that, the red block is clear, the blue block is clear, the orange block is clear, the hand is empty, the red block is on the table, the blue block is on the table and the orange block is on the table.</initial-state>\n<goal-state>My goal is to have the red block on top of the orange block and the blue block on top of the red block.</goal-state>\n\n'

exp_tot_prompt = '<plan> {} </plan>\n\nConsidering the goal state and the current plan, explain 2 possible actions for step {} then conclude in the last line "The possible actions are: 1. <a> 2. <b>" where a, b are your explained actions.'

exp_tot_prompt_v2 = '<plan> {} </plan>\n\nConsidering the goal state and the current plan, explain up to 2 possible actions for the next action that can progress the plan towards the goal state, then conclude in the last line "The possible actions are: 1. <a> 2. <b> (optional)". The actions you propose must be valid and must contain the keywords described in the <domain> actions (e.g. stack and unstack etc).'

exp_vote_prompt = '<plan> {} </plan>\n\nHere are choices for step {}: {}\n\nDecide which choice is most promising in reaching the goal state. Analyze each choice in detail, then conclude in the last line "The best choice is <>" where <> is the chosen choice.'

exp_vote_prompt_v2 = '<plan> {} </plan>\n\nHere are choices for the next action in the plan: {}\n\nDecide which action is valid and can progress the plan towards the goal state. Analyze each action in detail, then conclude in the last line "The best action is <action>"'

exp_validate_prompt = 'Plan:\n{}\n\nDoes the plan satisfy the goal state? Analyze the plan in detail, then conclude in the last line "The plan <does/ does not> satisfy the goal state".'

exp_validate_prompt_v2 = 'Plan:\n{}\nWhen I execute this plan from the initial state, will I reach the goal state? Analyze the plan in detail, then conclude in the last line "The plan <does/ does not> satisfy the goal state".'

exp_init_tot_prompt = 'What are 2 possible actions for step 1 in reaching the goal state? Explain your actions, then conclude in the last line "The possible actions are: 1. {a} 2. {b}" where a, b are the possible actions.'
# The possible actions are: 1. Pick up the red block 2. Unstack the blue block from on top of another block 3. Pick up the orange block
exp_init_tot_prompt_v2 = 'What are 2 possible actions for step 1 of a plan in reaching the goal state? Explain your actions, then conclude in the last line "The possible actions are: 1. {a} 2. {b}". a and b must be valid actions, and must contain the keywords described in the <domain> actions.'

## BFS
exp_bfs_init_tot_example = '<example-1><initial-state>- The red block is in my hand\n- The blue block is clear\n- The orange block is not clear\n- The blue block is on the table\n- The orange block is on the table\n- the hand is not empty.</initial-state>\nThe possible actions are: 1. Stack the red block on top of the blue block\n2. Stack the red block on top of the orange block\n3. Put down the red block</example-1>\n<example-2><initial-state>- The red block clear\n- The blue block is clear\n- The orange block is not clear\n- The red block is on top of the orange block\n- The blue block is on the table\n- The orange block is on the table\n- the hand is empty.</initial-state>\nThe possible actions are: 1. Unstack the red block from on top of the orange block\n2. Pick up the blue block\n3. Pick up the orange block</example-2>'

exp_bfs_init_tot_prompt = 'Considering the domain and the initial state, propose 3 unique actions that I can do with the blocks. Explain your actions, then conclude in the last line "The possible actions are: 1. {a}\n2. {b}\n3. {c}". Express a, b and c using the keywords described in the <domain> actions, and you must follow the specified output format, including adding \n between actions. Note that if I am holding a block, I can stack it.'

exp_update_state_from_action_prompt = 'I am playing with a set of blocks where I need to arrange the blocks into stacks. Here are the actions I can do\n\nPick up a block\nUnstack a block from on top of another block\nPut down a block\nStack a block on top of another block\n\nI have the following restrictions on my actions:\nI can only pick up or unstack one block at a time.\nI can only pick up or unstack a block if my hand is empty.\nA block is clear as king as there are no blocks stacked on top of it and it is not held in the hand.\nI can only pick up a block if the block is on the table and the block is clear.\nI can only unstack a block (A) from on top of another block (B) if A was really on top of B.\nI can only unstack a block from on top of another block if the block I am unstacking is clear.\nOnce I pick up or unstack a block, I am holding the block.\nI can only put down a block that I am holding.\nI can only stack a block on top of another block if I am holding the block being stacked.\nI can only stack a block on top of another block if the block onto which I am stacking the block is clear.\nOnce I put down or stack a block, my hand becomes empty.\nOnce you stack a block (A) on top of another block (B), A becomes clear but B is no longer clear.\nInitial state: {}\nFrom the initial state, if I {}, what will the resulting state be?\n'

exp_update_state_from_action_answer_template = 'You must return the resulting state in the following format. For each statement, you must choose 1 option from the provided options. "<state>\n- The red block is {clear/ not clear/ held in the hand}\n- The blue block is {clear/ not clear/ held in the hand}\n- The orange block is {clear/ not clear/ held in the hand}\n- The red block is {on top of the blue block/ on top of the orange block/ on the table/ held in the hand}\n- The blue block is {on top of the red block/ on top of the orange block/ on the table/ held in the hand}\n- The orange block is {on top of the red block/ on top of the blue block/ on the table/ held in the hand}\n- the hand {is/ is not} empty\n</state>"'

exp_bfs_validate_prompt = 'When I execute the following plan from the initial state, analyse in detail if the goal state will be satisfied. <plan>{}</plan> For your reference, I expect to reach this state {} when the plan is executed from the initial state. You may use this in your analysis, but note that I may make mistakes. Finally, you must conclude in the last line as follows: "\nThe plan (does/ does not) satisfy the goal state".'

exp_bfs_vote_prompt = 'When I execute the following plan from the initial state, analyse in detail if the plan will progress towards the goal state. <plan>{}</plan> For your reference, I expect to reach this state {} when the plan is executed from the initial state. You may use this in your analysis, but note that I may make mistakes. If progress is being made, you must conclude in the last line "continue the plan". Otherwise you must conclude with "re-evaluate the plan".'

exp_bfs_vote_prompt_v2 = 'From the initial state, is it valid to {} ? Study the domain carefully and if the action is valid, conclude with "\n valid action". If you are unsure about anything, give benefit of doubt and conclude with "\n valid action". Only if you are 100% certain the action is invalid, you may conclude with "\n re-evaluate action". Use this conclusion cautiously.'