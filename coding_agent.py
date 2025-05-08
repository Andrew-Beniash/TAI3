import os
import dotenv
import litellm
from litellm import completion
import re

# Load API key
dotenv.load_dotenv()
litellm.openai_api_key = os.getenv("OPENAI_API_KEY")

# Helper to extract code block
def extract_code_block(text):
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return code_blocks[0].strip() if code_blocks else text.strip()

# Initialize message history for context preservation
message_history = []

def ask_llm(prompt):
    message_history.append({"role": "user", "content": prompt})
    response = completion(
        model="gpt-4",
        messages=message_history,
    )
    message_history.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
    return response['choices'][0]['message']['content']

def main():
    # Step 1: Ask user what function to generate
    user_request = input("What function would you like to create? Describe its purpose: ")

    print("\n Generating basic function...")
    initial_prompt = f"Write a basic Python function based on this user description: {user_request}"
    basic_response = ask_llm(initial_prompt)
    code_only = extract_code_block(basic_response)
    print(code_only)

    # Step 2: Ask to add documentation
    print("\n Adding documentation...")
    doc_prompt = (
        "Now please add comprehensive documentation to the following Python function. "
        "Include a function description, parameter descriptions, return value description, "
        "example usage, and edge case considerations.\n\n"
        f"{code_only}"
    )
    doc_response = ask_llm(doc_prompt)
    documented_code = extract_code_block(doc_response)
    print(documented_code)

    # Step 3: Ask to add test cases
    print("\n🧪 Adding unit tests using unittest...")
    test_prompt = (
        "Now please write Python unittest test cases for the following function. "
        "Include tests for basic functionality, edge cases, error conditions, and varying input scenarios.\n\n"
        f"{documented_code}"
    )
    test_response = ask_llm(test_prompt)
    test_code = extract_code_block(test_response)
    print(test_code)

    # Save the final code + test to file
    final_filename = "generated_function_with_tests.py"
    with open(final_filename, "w") as f:
        f.write("# === FUNCTION ===\n\n")
        f.write(documented_code + "\n\n")
        f.write("# === TEST CASES ===\n\n")
        f.write(test_code)

    print(f"\n Final code saved to '{final_filename}'")

if __name__ == "__main__":
    main()
