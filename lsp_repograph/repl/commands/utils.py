from typing import Dict, Any


def read_file_line(file_path: str, line_number: int) -> str:
    """Read a specific line from a file (0-indexed)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if 0 <= line_number < len(lines):
                return lines[line_number].rstrip()
    except Exception as e:
        return f"<Error reading file: {e}>"
    return "<Line not found>"


def format_reference_with_content(ref: Dict[str, Any], repo_path: str = "") -> str:
    """Format a reference with its source line content"""
    # Extract file path (prefer absolutePath, fallback to relativePath)
    if 'absolutePath' not in ref:
        return str(ref)  # Fallback to raw output
    file_path = ref['absolutePath']
    
    # Extract line/column info
    range_info = ref.get('range', {})
    start = range_info.get('start', {})
    line_num = start.get('line', 0)  # 0-indexed
    col_num = start.get('character', 0)
    
    # Read the actual line content
    line_content = read_file_line(file_path, line_num)
    
    # Format output
    return f"{file_path}:{line_num + 1}:{col_num + 1}: {line_content}"