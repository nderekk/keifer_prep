import vertexai
from vertexai.generative_models import GenerativeModel
import json
import time
import os

# 1. Initialize the Enterprise Connection
# The SDK automatically finds the credentials you just created in the terminal!
vertexai.init(project=os.getenv("project_key"), location="europe-west4")

# 2. Your Master Prompt (Insert your Taxonomy from Hour 1 here)
system_prompt = """
You are an expert political data scientist analyzing Greek digital media. Read the provided Greek news article and extract the political ideological leaning of the text on a continuous numerical scale from 0.0 to 1.0.

DEFINITIONS & EXPLICIT ANCHORS:
- 0.00 to 0.15: Far-Left
- 0.16 to 0.35: Left
- 0.36 to 0.45: Center-Left
- 0.46 to 0.55: Center (or strictly Neutral/Objective reporting)
- 0.56 to 0.65: Center-Right
- 0.66 to 0.85: Right
- 0.86 to 1.00: Far-Right

INSTRUCTIONS:
Assign a precise decimal value based on the severity of the bias. For example, a moderately right-wing article might be 0.72, while an extreme left-wing article might be 0.05.

STRICT OUTPUT RULES:
You must respond ONLY with a valid, parsable JSON object. Do NOT include markdown formatting, code blocks, explanations, or any trailing text. 

EXAMPLE OUTPUT:
{"bias": 0.72}
"""

model = GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=[system_prompt] # <--- It goes here in Vertex!
)

with open('datasets/final_unlabeled_dataset.json', 'r', encoding='utf-8') as f:
    unlabeled_dataset = json.load(f)
    
test_articles = unlabeled_dataset[:3000]

# 4. The Distillation Loop
OUTPUT_FILE = 'datasets/labeled_dataset.jsonl'
processed_titles = set()

# Load existing progress if the file exists
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                processed_titles.add(item.get("title"))
            except json.JSONDecodeError:
                continue
    print(f"Resuming: {len(processed_titles)} articles already labeled.")

# Filter out articles that have already been processed
test_articles = [item for item in test_articles if item.get("title") not in processed_titles]

for i, item in enumerate(test_articles, 1):
    title = item.get("title", "")
    text = item.get("text", "")
    article_content = f"ΤΙΤΛΟΣ: {title}\nΚΕΙΜΕΝΟ: {text}"
    
    success = False
    
    # Retry loop: Try up to 3 times for a single article
    while not success:
        try:
            response = model.generate_content(
                article_content,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )
            
            parsed_json = json.loads(response.text) 
            item["ai_labels"] = parsed_json
            
            # Append each item immediately to the .jsonl file
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            print(f"Success! Labeled: {title[:30]}...")
            success = True # Breaks the while loop
            
            if i % 10 == 0:
                print(f"--- Progress: {i} new items labeled this session ---")

            time.sleep(1)  # 1 second sleep (approx 60 RPM, adjust if hitting quotas)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10) # Simple backoff

print("Distillation complete. Dataset saved to .jsonl!")

print("Distillation complete. Dataset saved!")