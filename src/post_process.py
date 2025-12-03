import yaml
import re
from typing import Dict, List
from pathlib import Path

def load_replacements(path: str) -> Dict[str, str]:
    """Load replacements from YAML file with safe defaults."""
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            # Handle None or missing 'replacements' key
            if data is None:
                print(f"Warning: {path} is empty, using empty replacements")
                return {}
            replacements = data.get('replacements', {})
            # Ensure we always return a dict
            return dict(replacements) if replacements else {}
    except FileNotFoundError:
        print(f"Warning: {path} not found, using empty replacements")
        return {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing {path}: {e}, using empty replacements")
        return {}
    except Exception as e:
        print(f"Warning: Unexpected error loading {path}: {e}, using empty replacements")
        return {}

def apply_replacements(text: str, replacements: Dict[str, str]) -> str:
    """Apply case-insensitive regex replacements with word boundaries."""
    result = text
    for old, new in replacements.items():
        # Create case-insensitive pattern with word boundaries
        pattern = r'\b' + re.escape(old) + r'\b'
        result = re.sub(pattern, new, result, flags=re.IGNORECASE)
    return result

def normalize_spacing(text: str) -> str:
    """Clean up extra spaces and fix spacing before punctuation."""
    # Replace multiple spaces with single space
    result = re.sub(r'\s+', ' ', text.strip())

    # Fix spaces before punctuation
    result = re.sub(r'\s+([.,!?;:])', r'\1', result)

    return result

def capitalize_sentences(text: str) -> str:
    """Capitalize after sentence-ending punctuation and first character."""
    # Split text into sentences (split on . ! ? followed by space or end)
    sentences = re.split(r'([.!?]\s*)', text)

    result = []
    capitalize_next = True

    for part in sentences:
        if capitalize_next and part.strip():
            # Capitalize first letter
            part = part[0].upper() + part[1:] if part else part
            capitalize_next = False

        # Set flag for next part if this ends with sentence punctuation
        if part.endswith(('.', '!', '?')):
            capitalize_next = True

        result.append(part)

    return ''.join(result)

def process_mode_a(text: str, replacements: Dict[str, str]) -> str:
    """Apply replacements + normalize spacing only."""
    text = apply_replacements(text, replacements)
    text = normalize_spacing(text)
    return text

def process_mode_b(text: str, replacements: Dict[str, str]) -> str:
    """Mode A + capitalize sentences."""
    text = process_mode_a(text, replacements)
    text = capitalize_sentences(text)
    return text

if __name__ == "__main__":
    # Load replacements using path relative to project root
    # When run from project root: python src/post_process.py
    config_path = Path(__file__).resolve().parent.parent / "config" / "replacements.yaml"
    replacements = load_replacements(str(config_path))
    
    print(f"Loaded {len(replacements)} replacement rules")

    # Test string
    test_text = "i was trading man cue today using run pod and it was great"

    print("\nOriginal:", test_text)
    print("Mode A:", process_mode_a(test_text, replacements))
    print("Mode B:", process_mode_b(test_text, replacements))
