from __future__ import annotations
from jedi import Project, Script
import os
from pathlib import Path
from typing import List, Dict, Any

import jedi
from jedi.api import Project


def find_references_in_project(
    project_root: str | os.PathLike,
    file_path: str | os.PathLike,
    line: int,
    column: int,
    *,
    added_sys_paths: list[str] | None = None,
    # environment_path: str | None = None,
    include_builtins: bool = False,
) -> List[Dict[str, Any]]:
    """
    Find references for the symbol at (line, column) in file_path using a Jedi Project.

    line:    0-based line index
    column:  0-based column index
    """
    line += 1
    project_root = str(Path(project_root).resolve())
    file_path = str(Path(file_path).resolve())

    # Optional: use a specific Python environment (your venv)
    # env = get_environment(environment_path) if environment_path else None

    project = Project(
        path=project_root,
        smart_sys_path=True,                # let Jedi infer paths from project metadata
        added_sys_path=added_sys_paths or [],  # e.g., ["src"] or absolute paths
        # environment=env
    )

    # Create a Script bound to this file and project
    script = Script(path=file_path, project=project)

    # Ask for references at the given position
    # (line is 1-based; column is 0-based)
    names = script.get_references(line=line, column=column, include_builtins=include_builtins)

    # Normalize the results
    out: List[Dict[str, Any]] = []
    for n in names:
        module_path = n.module_path  # may be None for builtins/stdin
        out.append({
            "name": n.name,
            "is_definition": n.is_definition(),
            "file": str(module_path) if module_path else None,
            "line": n.line,
            "column": n.column,  # still 0-based
        })
    return out

def example_sample_project():
    repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/LSP-RepoGraph/examples/sample_project"
    # repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/twisted_twisted_e31995c9_parent"
    # repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/stackstorm_st2_4022aea9_parent"

    # Example usage
    # file_rel = "core/math_utils.py"
    # file_abs = os.path.join(repo_path, file_rel)

    # # Suppose the caret is on the symbol at line 12, column 6
    # refs = find_references_in_project(
    #     project_root=repo_path,
    #     file_path=file_abs,
    #     line=12,
    #     column=6,
    #     added_sys_paths=["."],            # adjust or remove if not needed
    #     # environment_path="/path/to/venv/bin/python",  # or None
    #     include_builtins=False
    # )

    file_rel = "main.py"
    file_abs = os.path.join(repo_path, file_rel)

    # Suppose the caret is on the symbol at line 12, column 6
    refs = find_references_in_project(
        project_root=repo_path,
        file_path=file_abs,
        line=9,
        column=11,
        added_sys_paths=["."],            # adjust or remove if not needed
        # environment_path="/path/to/venv/bin/python",  # or None
        include_builtins=False
    )


    # Pretty-print
    for r in refs:
        print(
            f"{'[def]' if r['is_definition'] else '[ref]'} "
            f"{r['name']} – {r['file']}:{r['line']}:{r['column']}"
        )

def example_sample_project():
    repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/cloud-custodian_cloud-custodian_12e3e808_parent"

    file_rel = "main.py"
    file_abs = os.path.join(repo_path, file_rel)

    # Suppose the caret is on the symbol at line 12, column 6
    refs = find_references_in_project(
        project_root=repo_path,
        file_path=file_abs,
        line=9,
        column=11,
        added_sys_paths=["."],            # adjust or remove if not needed
        # environment_path="/path/to/venv/bin/python",  # or None
        include_builtins=False
    )


    # Pretty-print
    for r in refs:
        print(
            f"{'[def]' if r['is_definition'] else '[ref]'} "
            f"{r['name']} – {r['file']}:{r['line']}:{r['column']}"
        )


if __name__ == "__main__":

    example_sample_project()