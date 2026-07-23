import yaml
import json
import os
from llms import LLMs
from datetime import datetime
from pathlib import Path



def run_benchmark(config_path):
    # 1. Load config
    llms = LLMs()
    with open(config_path, 'r') as f:
        conf = yaml.safe_load(f)

    # CHANGE pull variables from config file
    
    models_to_run = conf['llm']['model']
    runs = conf['number_of_runs']
    selected_topics = conf['topics']
    output_path = conf['file_path_output']
    benchmark_path = conf['file_path_benchmark']
    temp = conf.get("temperature", 0.5)
    max_tokens = conf.get("max_tokens", 8000)

    # CHANGE outer loop for each model
    for model_name in models_to_run:
        if "deepseek" in model_name:
            api_key = conf["api_keys"]["deepseek"]
        elif "gpt" in model_name:
            api_key = conf["api_keys"]["gpt"]
        elif model_name == "gemini":
            api_key = conf["api_keys"]["gemini"]
        elif "claude" in model_name:
            api_key = conf["api_keys"]["claude"]
        else:
            raise ValueError("Unsupported model")
        
        # CHANGE create the specific folder for this model
        model_folder = Path(output_path) / model_name
        model_folder.mkdir(parents=True, exist_ok=True)
        print(f"Saved inside : {model_folder}")

        # 2. Load benchmark
        with open(benchmark_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # CHANGE inner loop to run multiple times for each model
        for run in range(1, runs + 1): 
            all_results = []

            # 3. Loop over multiple benchmarks (topics)
            for benchmark in data.get('topics', []):
                
                # CHANGE only run for selected topics
                topic_id = benchmark['topic_id']
                if selected_topics != 'all' and topic_id not in selected_topics:
                    print(f"\n Skipping topic {topic_id}")
                    continue    
                
                print(f"\n=== Running benchmark: {benchmark['topic_id']} ({benchmark['topic']}) ===")

                topic_results = {
                    "topic_id": topic_id,
                    "topic": benchmark["topic"],
                    "results": []
                }

                # Loop over paragraphs inside each topic
                for p in benchmark.get('paragraphs', []):
                    print(f"\nPrompt: {p['prompt']}")

                    # Step A: Generate story
                    if "deepseek" in model_name:
                        story_answer = llms.deepseek(p['prompt'], model_name, api_key, temp, max_tokens)
                    elif model_name == "gemini":
                        story_answer = llms.gemini(p['prompt'], "gemini-2.0-flash", api_key, temp, max_tokens)
                    elif "gpt" in model_name:
                        story_answer = llms.chatgpt(p['prompt'], model_name, api_key, temp, max_tokens)
                    elif "claude" in model_name:
                        story_answer = llms.claude(p['prompt'], model_name, api_key, temp, max_tokens)
                    paragraph_results = {
                        "paragraph_id": p['paragraph_id'],
                        "title": p.get("title"),
                        "original_prompt": p['prompt'],
                        "llm_story": story_answer,
                        "validation_results": []
                    }

                    # Step B: Validation questions
                    for v_q in p.get('validation_questions', []):
                        validation_prompt = f"Story: {story_answer}\n\nQuestion: {v_q['text']}"

                        if "deepseek" in model_name:
                            v_answer = llms.deepseek(validation_prompt, model_name, api_key, temp, max_tokens)
                        elif model_name == "gemini":
                            v_answer = llms.gemini(validation_prompt, "gemini-2.5-flash-lite", api_key, temp, max_tokens)
                        elif  "claude" in model_name:
                            v_answer = llms.claude(validation_prompt, model_name, api_key, temp, max_tokens)
                        elif "gpt" in model_name:
                            v_answer = llms.chatgpt(validation_prompt, model_name, api_key, temp, max_tokens)

                        paragraph_results["validation_results"].append({
                            "q_id": v_q['qid'],
                            "question": v_q['text'],
                            "answer": v_answer
                        })

                    topic_results["results"].append(paragraph_results)

                all_results.append(topic_results)

            # 4. Output handling
            os.makedirs(output_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_model_name = model_name.replace('-', '_')
            output_filename = f"results_run{run}_{clean_model_name}_{timestamp}.json"
            # CHANGE saved to folder for that file
            full_path = model_folder / output_filename

            output_payload = {
                "model_used": model_name,
                "results": all_results
            }

            with open(full_path, 'w') as f:
                json.dump(output_payload, f, indent=2)

            print(f"\n✅ Success! Results written to {full_path}")


if __name__ == "__main__":
    run_benchmark('conf.yaml') 
