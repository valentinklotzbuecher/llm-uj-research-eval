"""
Prompt builder utilities for composing system prompts from components.
"""
from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent
COMPONENTS_DIR = PROMPTS_DIR / "components"


def load_component(filename: str) -> str:
    """
    Load a component file from the components/ directory.

    Args:
        filename: Name of the file in components/ (e.g., "base_guidelines.txt")

    Returns:
        Content of the component file as a string

    Raises:
        FileNotFoundError: If component file doesn't exist
    """
    filepath = COMPONENTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Component not found: {filepath}")
    return filepath.read_text().strip()


def build_prompt(
    guidelines: str = "base_guidelines.txt",
    calibration: str = "calibration_instructions.txt",
    schema: str = "schema_instructions.txt",
    preamble: str = "",
    postamble: str = "",
    custom_components: Optional[dict[str, str]] = None
) -> str:
    """
    Compose a complete system prompt from components.

    Args:
        guidelines: Filename in components/ or full text string
        calibration: Filename in components/ or full text string
        schema: Filename in components/ or full text string
        preamble: Text to prepend before all components
        postamble: Text to append after all components
        custom_components: Dict of custom sections to include

    Returns:
        Complete system prompt string

    Example:
        >>> prompt = build_prompt(
        ...     preamble="You are an expert evaluator.",
        ...     postamble="Return strict JSON only."
        ... )
    """
    parts = []

    # Add preamble
    if preamble:
        parts.append(preamble.strip())

    # Add main components (load from file if filename, else use as-is)
    for component in [guidelines, calibration, schema]:
        if component.endswith('.txt'):
            # It's a filename
            try:
                parts.append(load_component(component))
            except FileNotFoundError:
                # Maybe it doesn't exist yet, skip
                pass
        elif component:
            # It's full text
            parts.append(component.strip())

    # Add custom components
    if custom_components:
        for key, value in custom_components.items():
            parts.append(value.strip())

    # Add postamble
    if postamble:
        parts.append(postamble.strip())

    # Join with double newlines
    return "\n\n".join(parts)


def substitute(template: str, replacements: dict[str, str]) -> str:
    """
    Perform placeholder substitution in template strings.

    Args:
        template: String with {placeholders}
        replacements: Dict mapping placeholder names to values

    Returns:
        Template with all placeholders replaced

    Example:
        >>> template = "Assess on a {scale} scale from {min} to {max}."
        >>> substitute(template, {"scale": "percentile", "min": "0", "max": "100"})
        'Assess on a percentile scale from 0 to 100.'
    """
    result = template
    for key, value in replacements.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, value)
    return result


def compare_prompts(prompt_a: str, prompt_b: str, context: int = 3) -> list[str]:
    """
    Compare two prompts and return differences.

    Args:
        prompt_a: First prompt
        prompt_b: Second prompt
        context: Number of context lines around differences

    Returns:
        List of diff lines
    """
    import difflib

    diff = difflib.unified_diff(
        prompt_a.splitlines(keepends=True),
        prompt_b.splitlines(keepends=True),
        lineterm='',
        n=context
    )
    return list(diff)
