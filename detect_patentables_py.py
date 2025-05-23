import os
import ast
import openai
import argparse

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def analyze_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                print(f"\n=== Analyzing {full_path} ===")
                functions = extract_functions_from_file(full_path)
                for name, code in functions:
                    print(f"\n--- Function: {name} ---")
                    try:
                        result = summarize_with_gpt(name, code)
                        print(result)
                    except Exception as e:
                        print(f"Error analyzing function {name}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to Python file or folder")
    args = parser.parse_args()

    if os.path.isdir(args.path):
        analyze_directory(args.path)
    elif args.path.endswith(".py"):
        print(f"\n=== Analyzing {args.path} ===")
        for name, code in extract_functions_from_file(args.path):
            print(f"\n--- Function: {name} ---")
            try:
                result = summarize_with_gpt(name, code)
                print(result)
            except Exception as e:
                print(f"Error analyzing function {name}: {e}")
    else:
        print("Invalid input path. Please provide a .py file or directory.")

if __name__ == "__main__":
    main()
