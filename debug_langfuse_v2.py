import langfuse
import os
from dotenv import load_dotenv
from langfuse import observe, langfuse_context

print(f"Langfuse Version: {langfuse.__version__}")
print(f"Langfuse File: {langfuse.__file__}")

load_dotenv()

# Test basic trace manually without decorator to see if it works
from langfuse import Langfuse
lf = Langfuse()

print("Sending manual trace...")
trace = lf.trace(name="Manual Trace")
trace.generation(name="Manual Generation", input="hi", output="bye")
print("Flushing manual trace...")
lf.flush()
print("Done.")

@observe()
def test_decorator():
    print("Inside decorated function")
    return "ok"

print("Running decorated function...")
test_decorator()
print("Flushing context...")
langfuse_context.flush()
print("Finished.")
