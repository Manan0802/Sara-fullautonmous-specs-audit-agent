import langfuse
from langfuse import observe

print("Top Level Exports:")
print(dir(langfuse))

try:
    from langfuse.decorators import langfuse_context
    print("SUCCESS: langfuse_context in langfuse.decorators")
except ImportError:
    print("FAILURE: langfuse_context NOT in langfuse.decorators")

try:
    from langfuse import langfuse_context
    print("SUCCESS: langfuse_context in langfuse")
except ImportError:
    print("FAILURE: langfuse_context NOT in langfuse")
