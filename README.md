# LSP-RepoGraph

A high-performance, semantic code search tool for AI agents using Pyright LSP server based on RepoGraph.

## Getting Started

To run the demo, follow these steps

- Install requirements with

```bash
pip install -r requirements.txt
```

- Run the demo

```bash
python examples/demo-multilspy-clients.py
```

In the future, I will make this into a python package to simplify the setup.

## TODO

- [x] Implement repograph based on multilspy + jedi

  - To get definition node by name, use `multilspy.SyncLanguageServer.request_workspace_symbol`. This will return the exact file + line + col of the variable definition

        Seems like Jedi also support search by prefix automatically.

  - For reference edge, i.e. to get all references of a definition, use `multilspy.SyncLanguageServer.request_references` on the exact location of definition (file + line + col)

  - For contain edge, we only support "class contains methods", and implement this by analyzing the class code on the fly with ast parsing (using the builtin `ast` library)

    - For the case of "function contains function", we don't support it. It's a rare case, and the inner function won't be referenced outside of the outer function, unless it's returned, in which case we can't find the usage anyway.

            This is an example, where the inner function `bar` is returned by `foo`, and used in `main` function. We won't create a reference edge in the repograph from `main` to `bar`.

            ```python
            def foo():
                def bar():
                    print("bar")
                
                return bar 

            def main():
                myfunc = foo()
                myfunc()
            ```

- [x] Run LSP-RepoGraph on the largest few data points in PyMigBench.

    Size of data point is measured by #python file and LoC

- [x] search symbol for third-party libraries

  - May need to pass environmentPath (path to python binary) to initializationOptions

        This is defined at `/home/eiger/CMU/2025_Spring/11634_Capstone/playground/LSP-RepoGraph/venv/lib/python3.10/site-packages/multilspy/language_servers/jedi_language_server/initialize_params.json`

    This can be done with a scratch file `scratch.py` of this form

    ```python
    from os.path import join
    join
    ```

    and call `textDocument/definition` on line 0 col 0 in `scratch.py`

- [x] Make it into a python package

  - [x] Setup to install from local

  - [x] Pass in environment of target repo, instead of relying on the python interpreter that is used to run lsp-repograph

    When running lsp-repograph against a repo, there are two python environments here

    - lsp-repograph env: the env of lsp-repograph, which mainly contains multilspy.

    - repo env: the env of the repo, which contains whatever is needed to execute code in the repo.

    We need to pass in repo env to jedi-language-server, and exclude the lsp-repograph env (exclusion is also need to avoid conflicts between repo env and lsp-repograph env, say when both uses numpy but in diff versions)

    We need a way to modify the init params passed to jedi-language-server in multilspy

    - [x] Create a custom jedi server by copying from the original jedi server's code

    - [x] Parametrize the custom jedi server with init param

- [x] Modularize the demo into a "repl" subpackage under repograph

- [x] Make the return value in simple-coding-tools typed. Define data classes repr the returned value

  We use the `multilspy_types` directly: find refs methods return dict of type `multilspy_types.Location`, and find def methods return dict of type `multilspy_types.UnifiedSymbolInformation`.

  This significantly helps with providing better prompt to ai agent, because the agent can know what to put in input and what to expect from output

- [ ] make the argument named, such as "find-ws-refs --type "

- [ ] Support searching for "module usage"

- [ ] When returning definition, besides location, we return extra information about the definition.

  Fuck, let's just return def loc + hover text, and nothing else.

  When we find the location of definition with lsp, we use AST to parse the file containing def, and extract additional information

  Different types of symbol (function, class, constant) in different context (workspace, non-workspace) have different extra info.

  - hover info: all symbols

    This can be returned by 'textDocument/hover'

  - signature: function / method / class

    - For function / method, we also include the function / method signature

    - For class, we also include the list of methods

  - range of full def: workspace function / method / class

    For workspace symbol of function / method / class, we also include the range of the full source code of the definition

    We restrict to workspace symbol b/c it makes no sense to provide source code to a third-party library function or a built-in method.

  - source code of full def: workspace function / method / class

    Same logic as range of full def

  Implementation-wise, we define smth like `enrich_definition(loc: Location)`, which takes in def loc, convert the file into AST, and get the needed info.

- [ ] Let user toggle what level of additional def info they want

  - None
  
  - (default) containerName

  - containerName, signature

  - containerName, signature, range of full def

  - containerName, signature, range of full def, content of full def

- [ ] Update how repl print the definition with the additional def info to be more informative

- [ ] implement "contains" relationship for classes

- [ ] Let user specify how many lines before & after the location of ref do they want to see. E.g. I want to see 3 lines before and after the ref loc.

- [ ] Integrate with SWE-Agent as a tool

### TODO Items not planned for Capstone

Mainly due to time limit, some features won't be supported within the scope of Capstone.

- [ ] What about overloaded methods (same method name w/ diff parameters)?

  Overloaded method's definition location won't be returned by `textDocument/definition` with jedi-language-server.

  Ideally, all overloads should be returned.

## Overview

> The sections below are not updated. Just refer to getting started section above.

LSP-RepoGraph provides definition and reference lookups (both by fully-qualified name and by caret location) by leveraging Language Server Protocol (LSP) capabilities instead of text scanning. This approach offers:

- **Semantic accuracy**: Understands Python imports, scoping, inheritance
- **High performance**: Uses Pyright's built-in indexing instead of scanning files
- **Incremental updates**: Automatically handles code changes without rebuilding
- **No false positives**: Won't match strings or comments containing symbol names

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install LSP-RepoGraph
pip install -e .
```

## Quick Start

```python
from lsp_repograph import SimpleCodeTool

# Initialize tool with repository path
tool = SimpleCodeTool("/path/to/your/python/project")

# Find a definition by fully-qualified name
definition = tool.find_def_by_fqn("collections", "deque.popleft")

# Find references by fully-qualified name
references = tool.find_refs_by_fqn("pathlib", "Path.read_text")

# Use a repo-relative location (0-indexed line/character)
definition_from_loc = tool.find_def_by_loc("app/io_utils.py", line=42, character=25)
references_from_loc = tool.find_refs_by_loc("app/io_utils.py", line=42, character=25)

# Cleanup
tool.shutdown()
```

## Interactive Demo

Run the interactive REPL demo:

```bash
cd examples
python demo.py
```

Try these commands:

- `find-def-by-fqn --module collections --qualpath deque.popleft`
- `find-refs-by-fqn --module pathlib --qualpath Path.read_text`
- `find-def-by-loc --rel_path sample_project/main.py --line 12 --character 8`
- `find-refs-by-loc --rel_path sample_project/main.py --line 12 --character 8`

## API Reference

### SimpleCodeTool

Main interface for code search functionality.

#### `find_def_by_fqn(module: str, qualpath: str | None = None, with_hover_msg: bool = True) -> Dict`

Resolve a definition using an importable module and dotted qualpath.

**Returns:**

```python
{
    'absolute_path': '/usr/lib/python3.12/collections/__init__.py',
    'line': 560,            # 0-indexed
    'character': 8,         # 0-indexed
    'hover_text': '... optional markdown hover ...'
}
```

#### `find_refs_by_fqn(module: str, qualpath: str | None = None) -> List[Dict]`

Resolve references for the symbol identified by `<module>:<qualpath>`.

**Returns:**

```python
[
    {
        'absolute_path': '/workspace/app/io_utils.py',
        'line': 42,
        'character': 17
    },
    {
        'absolute_path': '/workspace/tests/test_io.py',
        'line': 10,
        'character': 12
    }
]
```

#### `find_def_by_loc(rel_path: str, line: int, character: int, with_hover_msg: bool = True) -> Dict`

Resolve a definition from a repo-relative file path plus zero-based location.

#### `find_refs_by_loc(rel_path: str, line: int, character: int) -> List[Dict]`

Return references for the symbol under the cursor at the supplied location.

## Architecture

### LSP-First Approach

Unlike text-scanning tools, LSP-RepoGraph uses Pyright's workspace symbol search:

1. **Workspace Symbol Search**: Find definitions using `workspace/symbol` LSP request
2. **Reference Lookup**: For each definition, get references using `textDocument/references`
3. **Result Formatting**: Convert LSP responses to consistent format

### Performance Benefits

| Operation | Text Scanning | LSP-First |
|-----------|---------------|-----------|
| **Cold start** | Scan all files | Use Pyright index |
| **Symbol search** | O(total lines) | O(symbol occurrences) |
| **Incremental updates** | Rescan everything | Automatic |

## Requirements

- Python 3.8+
- Pyright language server (`pip install pyright`)

## Development

```bash
# Clone and install in development mode
git clone <repo>
cd LSP-RepoGraph
pip install -e .

# Run tests
python -m pytest

# Run demo
python examples/demo.py
```

## Limitations

- **Python only**: Currently supports Python projects only
- **Pyright dependency**: Requires Pyright LSP server installation
- **Startup time**: Initial LSP server startup takes ~1-2 seconds

## Comparison with RepoGraph

| Feature | RepGraph | LSP-RepoGraph |
|---------|----------|---------------|
| **Approach** | Graph construction + text search | Pure LSP |
| **Performance** | Slow (full repo scan) | Fast (indexed search) |
| **Accuracy** | Medium (text matching) | High (semantic analysis) |
| **Incremental** | Manual cache management | Automatic |
| **Setup** | Complex (graph construction) | Simple (pip install) |

## License

MIT License
