import sys
import json
import yaml
import re
import textwrap
from functools import reduce
import operator

def get_from_dict(data_dict, map_string):
    """
    Access a nested dictionary value using a JSONPath-like string.
    """
    if map_string.startswith('$.'):
        keys = map_string[2:].split('.')
        try:
            return reduce(operator.getitem, keys, data_dict)
        except (KeyError, TypeError, IndexError):
            return None
    return None

def parse_prompt_file(content):
    """
    A robust line-by-line parser that correctly handles indentation.
    """
    blocks = {}
    current_block_name = None
    current_block_lines = []
    content = content.replace('\r\n', '\n')

    for line in content.split('\n'):
        match = re.match(r'^([A-Z_]+):\s*$', line)
        if match:
            if current_block_name:
                block_body = textwrap.dedent("\n".join(current_block_lines)).strip()
                blocks[current_block_name] = block_body
            current_block_name = match.group(1)
            current_block_lines = []
        elif current_block_name:
            current_block_lines.append(line)

    if current_block_name:
        block_body = textwrap.dedent("\n".join(current_block_lines)).strip()
        blocks[current_block_name] = block_body
        
    return blocks

def run_assertions(assertions, mock_output, context):
    """
    Runs a list of assertions against a mock_output and a given context.
    Context can contain flags like 'is_cache_hit'.
    Returns True if all assertions pass, False otherwise.
    """
    all_passed = True
    for assertion in assertions:
        assertion_type = assertion.get('type')
        
        if assertion_type == 'equals':
            path = assertion.get('path')
            expected_value = assertion.get('value')
            actual_value = get_from_dict(mock_output, path)

            if actual_value == expected_value:
                print(f"  - ASSERT [equals] on {path}: PASS")
            else:
                print(f"  - ASSERT [equals] on {path}: FAIL")
                print(f"    - Expected: {repr(expected_value)}")
                print(f"    - Got: {repr(actual_value)}")
                all_passed = False

        elif assertion_type == 'was_cached':
            expected_value = assertion.get('value')
            is_cache_hit = context.get('is_cache_hit', False)
            if is_cache_hit == expected_value:
                print(f"  - ASSERT [was_cached]: PASS (was_cached={is_cache_hit})")
            else:
                print(f"  - ASSERT [was_cached]: FAIL")
                print(f"    - Expected: {repr(expected_value)}")
                print(f"    - Got: {repr(is_cache_hit)}")
                all_passed = False
        else:
            print(f"  - SKIPPED (unsupported assertion type: {assertion_type})")
            
    return all_passed

def main(filepath):
    print(f"--- Running tests for: {filepath} ---\n")
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        sys.exit(1)

    blocks = parse_prompt_file(content)

    if 'TEST' not in blocks:
        print("No TEST block found in the prompt file.")
        sys.exit(0)

    try:
        test_cases = yaml.safe_load(blocks['TEST'])
        if not isinstance(test_cases, list):
            print("Error: TEST block does not contain a valid list of test cases.")
            sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing TEST block YAML: {e}")
        sys.exit(1)

    total_tests = 0
    passed_count = 0
    failed_count = 0

    for i, test in enumerate(test_cases):
        total_tests += 1
        test_name = test.get('name', f'Test Case #{i+1}')
        print(f"Running test: \"{test_name}\"")

        test_steps = test.get('steps')
        if not test_steps:
            # For backward compatibility, if there are no steps, treat the whole test as a single step.
            # The step name is the test name itself.
            step_clone = test.copy()
            step_clone['name'] = test_name
            test_steps = [step_clone]

        test_failed_in_step = False
        # The cache for a single multi-step test case should be isolated.
        case_cache = {}

        for step in test_steps:
            step_name = step.get('name')
            if step_name and len(test_steps) > 1:
                print(f"  -> Step: {step_name}")

            mock_output = step.get('mock_output')
            assertions = step.get('assert', [])
            step_input = step.get('input')

            if not assertions:
                continue

            context = {}
            is_cache_hit = False
            
            if step_input:
                cache_key = json.dumps(step_input, sort_keys=True)
                if cache_key in case_cache:
                    is_cache_hit = True
                else:
                    is_cache_hit = False
                    if mock_output:
                        case_cache[cache_key] = mock_output
            
            context['is_cache_hit'] = is_cache_hit

            if not run_assertions(assertions, mock_output, context):
                test_failed_in_step = True
                break 

        if test_failed_in_step:
            failed_count += 1
        else:
            passed_count += 1
        print("-" * 20)

    print("\n--- Test Summary ---")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print("--------------------")

    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python proml_test.py <path_to_prompt_file>")
        sys.exit(1)
    main(sys.argv[1])