import json

def convert_to_format(input_file='first_100_prompts.json', output_file='formatted_100_prompts.jsonl', label='SAFE'):
    """
    Convert first 100 prompts to the format: {"text": "...", "label": "..."}

    Args:
        input_file: Path to input JSON file with prompts
        output_file: Path to output JSONL file
        label: Default label for all entries (default: "SAFE")
    """
    # Read the prompts from JSON file
    with open(input_file, 'r') as f:
        prompts = json.load(f)

    # Convert to the desired format
    formatted_data = []
    for prompt in prompts:
        formatted_entry = {
            "text": prompt,
            "label": label
        }
        formatted_data.append(formatted_entry)

    # Save to JSONL file (one JSON object per line)
    with open(output_file, 'w') as f:
        for entry in formatted_data:
            f.write(json.dumps(entry) + '\n')

    print(f"Converted {len(formatted_data)} prompts")
    print(f"Saved to: {output_file}")

    # Show first few examples
    print("\nFirst 3 examples:")
    for i, entry in enumerate(formatted_data[:3], 1):
        print(f"\n{i}. {json.dumps(entry, indent=2)}")

if __name__ == "__main__":
    convert_to_format()
