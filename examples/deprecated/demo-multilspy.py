from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from pprint import pprint
import time
import urllib
import os

def uri_to_path(uri: str) -> str:
    """
    Converts a file URI to a local filesystem path.
    Handles platform-specific considerations for Windows.
    """
    parsed_uri = urllib.parse.urlparse(uri)
    if parsed_uri.scheme != 'file':
        raise ValueError("Provided URI is not a 'file' scheme URI.")

    path = urllib.parse.unquote(parsed_uri.path)

    # Handle Windows-specific paths starting with an extra slash
    if os.name == 'nt' and path.startswith('/'):
        # On Windows, `file:///C:/path` becomes `/C:/path` after unquoting.
        # We need to remove the leading slash for a valid Windows path.
        path = path[1:]
        # Also, convert forward slashes to backslashes for Windows
        path = path.replace('/', '\\')

    return path


...
config = MultilspyConfig.from_dict({
    "code_language": "python",
    "trace_lsp_communication": True
}) # Also supports "python", "rust", "csharp", "typescript", "javascript", "go", "dart", "ruby"
logger = MultilspyLogger()

# repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/LSP-RepoGraph/examples/openshot-qt"
repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/LSP-RepoGraph/examples/sample_project"
# repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/twisted_twisted_e31995c9_parent"
# repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/stackstorm_st2_4022aea9_parent"

lsp = SyncLanguageServer.create(config, logger, repo_path)
print(f"Repo at {repo_path}")
with lsp.start_server():
    # while input() != "exit":
    result = lsp.request_workspace_symbol('math_utils.AdvancedCalculator')
    print("request_workspace_symbol: ")
    pprint(result)
    file_path = uri_to_path(
        result[0]['location']['uri']
    )
    print()

    start_line = result[0]['location']['range']['start']['line']
    start_col = result[0]['location']['range']['start']['character']
    result = lsp.request_definition(
        file_path, start_line, start_col
    )

    print("request_definition: ")
    pprint(result)
    result = lsp.request_references(
        file_path, start_line, start_col
    )
    print()

    print("request_references: ")
    pprint(result)
    print()

    # result = lsp.request_definition(
    #     "math_utils.py", # Filename of location where request is being made
    #     13, # line number of symbol for which request is being made
    #     7 # column number of symbol for which request is being made
    # )

    # result = lsp.request_document_symbols(
    #     "test_calculator.py"
    # )
    # result = lsp.request_definition(
    #     "test_calculator.py", # Filename of location where request is being made
    #     12, # line number of symbol for which request is being made
    #     20 # column number of symbol for which request is being made
    # )

    # Sample
    # result = lsp.request_references(
    #     "test_calculator.py",
    #     28,
    #     18
    # )
    # result = lsp.request_workspace_symbol('AdvancedCalculator')
    # result = lsp.request_workspace_symbol('Calculator.multiply')
    # result = lsp.request_references(
    #     "math_utils.py",
    #     # 4, 4
    #     # 24, 8
    #     12, 6
    # )
    # result = lsp.request_references(
    #     "main.py",
    #     9, 11
    # )



    # # openshot-qt 
    # result = lsp.request_references(
    #     "src/classes/metrics.py",
    #     90,
    #     4
    # )
    # result = lsp.request_workspace_symbol('track_metric_screen')

    # twisted
    # result = lsp.request_workspace_symbol('twisted.tap.socks.Options')
    # result = lsp.request_workspace_symbol('installReactor')
    # result = lsp.request_definition(
    #     'twisted/application/app.py',
        # 17, 29
        # 24, 41
    # )
    # result = lsp.request_references(
    #     'twisted/application/app.py',
    #     17, 29
    # )

    # # stackstore
    # result = lsp.request_workspace_symbol('get_version_string')
    # or search by prefix
    # result = lsp.request_workspace_symbol('get_version_')

    # pprint(result)