import os
import ast
import json
import argparse
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_functions_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append((node.name, ast.get_source_segment(source, node)))
    return functions

def summarize_with_gpt(function_name, code):
    prompt = f"""
You are a software patent analyst. Analyze the following Python function and:
1. Explain what it does in simple terms.
2. Assess whether the logic could be patentable (novel, clever, or non-obvious).
3. Suggest a short search query for patent lookup.

Function: {function_name}
Code:
{code}

Respond with:
- Summary
- Patentability (yes/no/maybe) + brief reasoning
- Suggested search phrase
"""
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def analyze_file(filepath):
    results = []
    print(f"\n=== Analyzing {filepath} ===")
    for name, code in extract_functions_from_file(filepath):
        print(f"\n--- Function: {name} ---")
        try:
            result_text = summarize_with_gpt(name, code)
            print(result_text)
            results.append({
                "file": filepath,
                "function": name,
                "code": code,
                "analysis": result_text
            })
        except Exception as e:
            print(f"Error analyzing function {name}: {e}")
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to Python file or folder")
    parser.add_argument("--out", default="patent_analysis.json", help="Output JSON file name")
    args = parser.parse_args()

    all_results = []

    if os.path.isdir(args.path):
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    all_results.extend(analyze_file(full_path))
    elif args.path.endswith(".py"):
        all_results.extend(analyze_file(args.path))
    else:
        print("Invalid input path. Please provide a .py file or directory.")
        return

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({
            "analyzed_at": datetime.utcnow().isoformat(),
            "results": all_results
        }, f, indent=2)

    print(f"\nAll results saved to {args.out}")

if __name__ == "__main__":
    main()
