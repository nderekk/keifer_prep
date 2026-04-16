import json

# 1. Load your API-labeled dataset
with open('datasets/labeled_dataset.json', 'r', encoding='utf-8') as f:
    labeled_data = json.load(f)

# 2. Open a new file in 'write' mode with the .jsonl extension
with open('datasets/training_data.jsonl', 'w', encoding='utf-8') as outfile:
    for item in labeled_data:
        # We only want to train on items that actually succeeded and have labels
        if "ai_labels" in item:
            
            # Reconstruct the exact prompt the AI saw
            prompt_text = f"ΤΙΤΛΟΣ: {item['title']}\nΚΕΙΜΕΝΟ: {item['text']}"
            
            # Convert the JSON labels BACK into a string, because the model 
            # is learning to generate text that *looks* like a JSON object.
            target_text = json.dumps(item["ai_labels"], ensure_ascii=False)
            
            # The standard Instruction-Tuning format
            training_row = {
                "input": prompt_text,
                "output": target_text
            }
            
            # Write it as a single line, followed by a newline character
            json.dump(training_row, outfile, ensure_ascii=False)
            outfile.write('\n')

print("Conversion complete! training_data.jsonl is ready for the GPU.")