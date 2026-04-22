import json
import argparse
import sys
from statistics import mean

def load_data(path):
    """Loads data from either a JSON (list) or JSONL file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.startswith('['):
                return json.loads(content)
            else:
                # Assume JSONL
                return [json.loads(line) for line in content.split('\n') if line.strip()]
    except Exception as e:
        print(f"Error loading {path}: {e}")
        sys.exit(1)

def extract_biases(data):
    """Maps URL to bias score, handling potential nesting or stringified JSON."""
    biases = {}
    for entry in data:
        # Use URL as primary key, fallback to title
        key = entry.get('url') or entry.get('title')
        if not key:
            continue
        
        labels = entry.get('ai_labels', {})
        # Handle case where ai_labels might be a stringified JSON (from legacy formats)
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except:
                continue
        
        bias = labels.get('bias')
        if bias is not None:
            try:
                biases[key] = float(bias)
            except ValueError:
                continue
    return biases

def calculate_mae(biases1, biases2):
    """Calculates Mean Absolute Error between two bias maps."""
    common_keys = set(biases1.keys()) & set(biases2.keys())
    
    if not common_keys:
        return None, 0
    
    errors = []
    for key in common_keys:
        err = abs(biases1[key] - biases2[key])
        errors.append(err)
    
    return mean(errors), len(common_keys)

def main():
    parser = argparse.ArgumentParser(description="Calculate MAE between two bias labeling sources.")
    parser.add_argument("file1", help="Path to the first JSON/JSONL file (e.g., Gemini labels)")
    parser.add_argument("file2", help="Path to the second JSON/JSONL file (e.g., Human/GPT labels)")
    args = parser.parse_args()

    print(f"Loading Source 1: {args.file1}...")
    data1 = load_data(args.file1)
    print(f"Loading Source 2: {args.file2}...")
    data2 = load_data(args.file2)

    biases1 = extract_biases(data1)
    biases2 = extract_biases(data2)

    mae, count = calculate_mae(biases1, biases2)

    print("\n" + "="*40)
    print("🏆 GROUND TRUTH VALIDATION DASHBOARD 🏆")
    print("="*40)
    print(f"Source A: {args.file1} ({len(biases1)} samples)")
    print(f"Source B: {args.file2} ({len(biases2)} samples)")
    print("-" * 40)
    
    if mae is None:
        print("❌ ERROR: No matching articles found between sources.")
        print("Ensure 'url' or 'title' fields match exactly.")
    else:
        print(f"Matched Articles: {count}")
        print(f"Mean Absolute Error (MAE): {mae:.4f}")
        print("-" * 40)
        
        # Interpret result based on 0-1 scale
        if mae < 0.05:
            print("STATUS: OUTSTANDING. High consensus between sources.")
        elif mae < 0.12:
            print("STATUS: GOOD. Minor deviations in bias scoring.")
        elif mae < 0.20:
            print("STATUS: ACCEPTABLE. Broad alignment, but lacks precision.")
        else:
            print("STATUS: DISCREPANCY. Significant difference in bias perception.")
    
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
