# Evaluating the efficacy of Tree of Thought prompting on LLM planning performance

We explore the application of the [Tree of Thought](https://arxiv.org/abs/2305.10601) prompting framework in the utilization of Large Language Models (LLM) as automated planners. The reasoning capabilities of LLMs are being leveraged to solve an increasing array of tasks in the present day. Yet, researchers have found little success in utilizing LLMs for planning tasks. This is because LLMs are not fine tuned to execute exploration and strategic lookahead which are key to solving planning problems. To overcome these challenges, we adopt Yao et. al's Tree of Thought (ToT) framework. ToT breaks down the planning problem into simpler intermediate steps that when repeated, enables the LLM to pursue multiple reasoning paths and explore the search space of the planning problem. We investigate how the use of ToT prompting affects the capability of the LLM to generate correct plans specifically for blocksworld planning problems. Our research is driven by Kambhampati et al.'s [PlanBench](https://arxiv.org/abs/2206.10498), which enables us to autonomously measure the planning capability of LLMs via empirical evaluation.

## Setup

1. Install `PlanBench` [dependencies](./plan-bench/README.md).
2. Git clone & set up [downward](https://github.com/aibasel/downward/blob/main/BUILD.md) in `./planner_tools`
3. Git clone & set up [VAL](https://github.com/KCL-Planning/VAL) in `./planner_tools`
4. Define environment variables

```
BLOCKSWORLD3_CONFIG_DIR=""
VAL_PATH_FROM_PLAN_BENCH_DIR=""
GROQ_API_KEY=""
BLOCKSWORLD3_INSTANCE_DIR=""
FAST_DOWNWARD_DIR=""
BASE_PIPELINE_TASK_NAME=""

# prompt report
DFS_PROMPT_REPORT_FILE_PATH=""
BFS_PROMPT_REPORT_FILE_PATH=""

# validation report
VALIDATION_REPORT_FILE_NAME=""
VALIDATION_REPORT_FILE_DIR=""
```

5. Define test instances in the [ToT pipeline](./plan-bench/pipeline_tot.py)
6. Run the ToT pipeline from the `plan-bench` directory

```sh
python3 pipeline_tot.py
```
