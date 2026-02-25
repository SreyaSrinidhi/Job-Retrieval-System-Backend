from pathlib import Path

#easily get the prompty
def load_prompt_text(filename: str) -> str:
    # .../app hopfuly WHY NO WORK oh work
    base_dir = Path(__file__).resolve().parents[1]  
    prompt_path = base_dir / "prompts" / filename

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")