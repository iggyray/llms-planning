import subprocess

def prompt_llama2(query):
    shellCommand = f"ollama run llama2 '{query}'"
    result = subprocess.run(shellCommand, shell=True, text=True, capture_output=True)

    if result.returncode == 0:
        return result.stdout
    else:
        return result.stderr
    
def prompt_llama3(query):
    shellCommand = f"ollama run llama3 '{query}'"
    result = subprocess.run(shellCommand, shell=True, text=True, capture_output=True)

    if result.returncode == 0:
        return result.stdout
    else:
        return result.stderr

def send_query(query, engine, max_tokens, model=None, stop="[STATEMENT]"):
    if engine == "llama2":
        if model:
            try:
                response = prompt_llama2(query)
            except Exception as e:
                print("failed to query llama2 with ollama")
            return response
    elif engine == "llama3":
        if model:
            try:
                response = prompt_llama3(query)
            except Exception as e:
                print("failed to query llama3 with ollama")
            return response
    else:
        print("invalid engine")
        return ""