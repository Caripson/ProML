from pathlib import Path

from proml.formatter import format_proml_content


def run():
    path = Path("test_prompts/sentiment_analysis.proml")
    source = path.read_text(encoding="utf-8")
    formatted = format_proml_content(source, filename=str(path))
    assert "META:\n" in formatted
    assert "OUTPUT:\n" in formatted
    assert "json_schema:" in formatted
    assert "ttl: 15m" in formatted
    # Idempotent formatting
    formatted_again = format_proml_content(formatted, filename=str(path))
    assert formatted_again == formatted

    sample = """# leading comment\nMETA:\n  # meta comment\n  id: sample  # inline id comment\n  version: 1.0.0\n  repro: strict\n\nINPUT:\n  value:\n    type: string  # ensure type comment\n    # value comment\n\nOUTPUT:\n  # output comment\n  json_schema:\n    $id: schema:sample\n    version: '2024-01-01'\n    schema:\n      type: object\n  regex: null  # regex comment\n  grammar: null\n\nPOLICY:\n  # policy comment\n  imports: []\n  local:\n    notes: ok\n\nPIPELINE:\n  steps:\n  - id: step1 # step comment\n    uses: module.example@^1.0.0\n    inputs: {}\n    outputs: {}\n    expects: {}\n\nTEST:\n  - name: Simple\n    mock_output:\n      value: ok\n    assert:\n    - type: schema\n"""
    formatted_sample = format_proml_content(sample, filename="sample.proml")
    lines = formatted_sample.splitlines()
    assert lines[0] == "# leading comment"
    assert any("inline id comment" in line for line in lines)
    assert any("ensure type comment" in line for line in lines)


if __name__ == "__main__":
    run()
    print("ok")
