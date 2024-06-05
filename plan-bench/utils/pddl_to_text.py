

import random

def get_sorted(init_atoms):
    return sorted(init_atoms, key=lambda x: x.symbol.name + " " + " ".join([subterm.name for subterm in x.subterms]))

def parse_problem(problem, data, shuffle):
    def parse(init_goal_preds, OBJS):
        TEXT = ""
        predicates = []

        init_goal_preds = list(init_goal_preds)
        for atom in init_goal_preds:
            objs = []
            for subterm in atom.subterms:
                if 'obfuscated' in data["domain_name"]:
                    objs.append(subterm.name.replace('o','object_'))
                elif 'blocksworld' in data['domain_name']:
                    objs.append(OBJS[subterm.name])
                elif 'logistics' in data['domain_name']:
                    obj = subterm.name
                    objs.append(f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}")
                elif 'depots' in data['domain_name']:
                    objs.append(subterm.name)
                # ADD SPECIFIC TRANSLATION FOR EACH DOMAIN HERE
            try:
                pred_string = data['predicates'][atom.symbol.name].format(*objs)
                predicates.append(pred_string)
            except:
                # print("[-]: Predicate not found in predicates dict: {}".format(atom.symbol.name))
                pass
            
        if len(predicates) > 1:
            predicates = [item for item in predicates if item]
            TEXT += ", ".join(predicates[:-1]) + f" and {predicates[-1]}"
        else:
            TEXT += predicates[0]
        return TEXT

    OBJS = data['encoded_objects']

    init_atoms = get_sorted(problem.init.as_atoms())
    goal_preds = get_sorted(problem.goal.subformulas) if hasattr(problem.goal, 'subformulas') else [problem.goal]

    if shuffle:
        random.shuffle(init_atoms)
        random.shuffle(goal_preds)
    # print(shuffle,init_atoms)
    # print(goal_preds)
    # ----------- INIT STATE TO TEXT ----------- #
    INIT = parse(init_atoms, OBJS)

    # ----------- GOAL TO TEXT ----------- #
    GOAL = parse(goal_preds, OBJS)

    return INIT, GOAL


def fill_template_v1(INIT, GOAL, PLAN, data, instruction=False):
    text = ""
    if INIT != "":
        text += "\n[STATEMENT]\n"
        text += f"As initial conditions I have that, {INIT.strip()}."
    if GOAL != "":
        text += f"\nMy goal is to have that {GOAL}."
    if not instruction:
        text += f"\n\nMy plan is as follows:\n\n[PLAN]{PLAN}"
    else:
        text += f"\n\nWhat is the plan to achieve my goal? Just give the actions in the plan."

    # TODO: Add this replacement to the yml file -- Use "Translations" dict in yml
    if 'blocksworld' in data['domain_name']:
        text = text.replace("-", " ").replace("ontable", "on the table")
    return text


def fill_template(INIT, GOAL, PLAN, data, instruction=False):
    text = ""
    if INIT != "" and not instruction:
        text += "\n<example>\n"
    if INIT != "" and instruction:
        text += "\n<problem>\n"
    if INIT != "":
        text += f"As initial conditions I have that, {INIT.strip()}."
    if GOAL != "":
        text += f"\nMy goal is to have that {GOAL}."
    if not instruction:
        text += f"\n\nMy plan is as follows:\n\n<plan>{PLAN}</plan>\n</example>\n"
    else:
        text += f"\n\nWhat is the plan to achieve my goal? Just give the actions in the plan.\n\n</problem>"

    # TODO: Add this replacement to the yml file -- Use "Translations" dict in yml
    if 'blocksworld' in data['domain_name']:
        text = text.replace("-", " ").replace("ontable", "on the table")
    return text

def instance_to_text(problem, get_plan, data, shuffle=False):
    """
    Function to make an instance into human-readable format
    """

    OBJS = data['encoded_objects']

    # ----------- PARSE THE PROBLEM ----------- #
    INIT, GOAL = parse_problem(problem, data, shuffle)

    # ----------- PLAN TO TEXT ----------- #
    PLAN = ""
    plan_file = "sas_plan"
    if get_plan:
        PLAN = "\n"
        with open(plan_file) as f:
            plan = [line.rstrip() for line in f][:-1]

        for action in plan:
            action = action.strip("(").strip(")")
            act_name, objs = action.split(" ")[0], action.split(" ")[1:]
            if 'obfuscated' in data["domain_name"]:
                objs = [j.replace('o','object_') for j in objs]
            elif 'blocksworld' in data['domain_name']:
                objs = [OBJS[obj] for obj in objs]
            elif 'logistics' in data['domain_name']:
                objs = [f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}" for obj in objs]
            #elif 'depots' in data['domain_name']:  no formatting necessary
            # ADD SPECIFIC TRANSLATION FOR EACH DOMAIN HERE
        
            PLAN += data['actions'][act_name].format(*objs) + "\n"

    return INIT, GOAL, PLAN, data









def get_plan_as_text(data, given_plan=None):
    OBJS = data['encoded_objects']
    PLAN = ""
    # print(given_plan)
    if given_plan:
        for action in given_plan:
            act_name, objs = action.split("_")[0], action.split("_")[1:]
            PLAN += "(" + act_name + " " + " ".join(objs) + ")\n"
            # PLAN += data['actions'][act_name].format(*objs) + "\n"
        return PLAN

    plan_file = "sas_plan"
    PLAN = ""
    with open(plan_file) as f:
        plan = [line.rstrip() for line in f][:-1]

    for action in plan:
        action = action.strip("(").strip(")")
        act_name, objs = action.split(" ")[0], action.split(" ")[1:]
        PLAN += "(" + act_name + " " + " ".join(objs) + ")\n"
        # PLAN += data['actions'][act_name].format(*objs) + "\n"
    return PLAN


def get_plan_as_text_v2(data):
    OBJS = data['encoded_objects']
    PLAN = ""

    plan_file = "sas_plan"

    with open(plan_file) as f:
        plan = [line.rstrip() for line in f][:-1]

    for action in plan:
        action = action.strip("(").strip(")")
        act_name, objs = action.split(" ")[0], action.split(" ")[1:]
        objs = [OBJS[obj] for obj in objs]
        PLAN += "(" + act_name + " " + " ".join(objs) + ")\n"

    return PLAN

def get_problem_description(INIT, GOAL, config):
    description = f'<domain>{config["domain_intro"]}</domain>\n\n'
    if INIT != "":
        description += f"<initial-state>As initial conditions I have that, {INIT.strip()}.</initial-state>\n\n"
    if GOAL != "":
        description += f"<goal-state>My goal is to have that {GOAL.strip()}.</goal-state>\n\n"

    if 'blocksworld' in config['domain_name']:
        description = description.replace("-", " ").replace("ontable", "on the table")
    return description

def get_domain_description_with_example(INIT, GOAL, config):
    description = f'<domain>{config["domain_intro"]}</domain>\n<example>\n'
    if INIT != "":
        description += f"<initial-state>As initial conditions I have that, {INIT.strip()}.</initial-state>\n"
    if GOAL != "":
        description += f"<goal-state>My goal is to have that {GOAL.strip()}.</goal-state>\n"
    description += "Here is a valid example plan that will achieve the goal state from the initial state: <plan>\n"
    description += get_gt_plan_description(config)
    description += "</plan>\n</example>"
    return description

def get_problem_description_only(INIT, GOAL, config):
    description = "\n"
    if INIT != "":
        description += f"<initial-state>As initial conditions I have that, {INIT.strip()}.</initial-state>\n"
    if GOAL != "":
        description += f"<goal-state>My goal is to have that {GOAL.strip()}.</goal-state>\n"
    return description

def get_gt_plan_description(config):
    OBJS = config['encoded_objects']
    # ----------- PLAN TO TEXT ----------- #
    PLAN = ""
    plan_file = "sas_plan"

    with open(plan_file) as f:
        plan = [line.rstrip() for line in f][:-1]

    for action in plan:
        action = action.strip("(").strip(")")
        act_name, objs = action.split(" ")[0], action.split(" ")[1:]
        if 'obfuscated' in config["domain_name"]:
            objs = [j.replace('o','object_') for j in objs]
        elif 'blocksworld' in config['domain_name']:
            objs = [OBJS[obj] for obj in objs]
        elif 'logistics' in config['domain_name']:
            objs = [f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}" for obj in objs]
    
        PLAN += config['actions'][act_name].format(*objs) + "\n"

    return PLAN

def get_gt_plan_description_and_length(config):
    OBJS = config['encoded_objects']
    # ----------- PLAN TO TEXT ----------- #
    PLAN = ""
    PLAN_LENGTH = 0
    plan_file = "sas_plan"

    with open(plan_file) as f:
        plan = [line.rstrip() for line in f][:-1]
    PLAN_LENGTH = len(plan)
    for action in plan:
        action = action.strip("(").strip(")")
        act_name, objs = action.split(" ")[0], action.split(" ")[1:]
        if 'obfuscated' in config["domain_name"]:
            objs = [j.replace('o','object_') for j in objs]
        elif 'blocksworld' in config['domain_name']:
            objs = [OBJS[obj] for obj in objs]
        elif 'logistics' in config['domain_name']:
            objs = [f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}" for obj in objs]
    
        PLAN += config['actions'][act_name].format(*objs) + "\n"

    return PLAN, PLAN_LENGTH

def get_action_description(config, action):
    OBJS = config['encoded_objects']
    PLAN = ""
    action = action.strip("(").strip(")\n")
    act_name, objs = action.split(" ")[0], action.split(" ")[1:]
    if 'obfuscated' in config["domain_name"]:
        objs = [j.replace('o','object_') for j in objs]
    elif 'blocksworld' in config['domain_name']:
        objs = [OBJS[obj] for obj in objs]
    elif 'logistics' in config['domain_name']:
        objs = [f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}" for obj in objs]
    PLAN += config['actions'][act_name].format(*objs) + "\n"

    return PLAN

