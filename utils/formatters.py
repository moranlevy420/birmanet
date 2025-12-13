"""
Formatting utilities for dates, numbers, and display values.
"""

from typing import List, Optional


def format_period(period: int) -> str:
    """
    Format a period integer (YYYYMM) to human-readable string.
    
    Args:
        period: Integer in YYYYMM format (e.g., 202401)
        
    Returns:
        Formatted string (e.g., "Jan 2024")
    """
    year = period // 100
    month = period % 100
    months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    if 1 <= month <= 12:
        return f"{months[month-1]} {year}"
    return str(period)


def get_short_unique_name(name: str, all_names: List[str]) -> str:
    """
    Get the shortest unique identifier for a fund name.
    
    Args:
        name: Full fund name
        all_names: List of all fund names to compare against
        
    Returns:
        Shortest unique prefix/identifier
    """
    # Handle non-string names
    if not isinstance(name, str):
        return str(name)[:15] if name else "Unknown"
    
    # Filter all_names to only strings
    all_names = [n for n in all_names if isinstance(n, str)]
    
    words = name.split()
    if not words:
        return name[:15]
    
    # Try first word only
    first_word = words[0]
    matches = [n for n in all_names if n.split()[0] == first_word]
    if len(matches) == 1:
        return first_word
    
    # Try first + last word (with ... in between)
    if len(words) >= 2:
        last_word = words[-1]
        first_last = f"{first_word} ... {last_word}"
        matches = [n for n in all_names if n.split()[0] == first_word and n.split()[-1] == last_word]
        if len(matches) == 1:
            return first_last
    
    # Try first 2 words
    if len(words) >= 2:
        two_words = ' '.join(words[:2])
        matches = [n for n in all_names if n.startswith(two_words)]
        if len(matches) == 1:
            return two_words
    
    # Try first 2 + last word
    if len(words) >= 3:
        first_two_last = f"{words[0]} {words[1]} ... {words[-1]}"
        matches = [
            n for n in all_names 
            if ' '.join(n.split()[:2]) == ' '.join(words[:2]) and n.split()[-1] == words[-1]
        ]
        if len(matches) == 1:
            return first_two_last
    
    # Fallback: first 3 words or full name if short
    result = ' '.join(words[:3])
    return result if len(result) <= 25 else result[:22] + '..'


def format_number(value: float, decimals: int = 2, prefix: str = "", suffix: str = "") -> str:
    """
    Format a number with optional prefix and suffix.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        prefix: Prefix string (e.g., "$")
        suffix: Suffix string (e.g., "%")
        
    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"
    return f"{prefix}{value:,.{decimals}f}{suffix}"

