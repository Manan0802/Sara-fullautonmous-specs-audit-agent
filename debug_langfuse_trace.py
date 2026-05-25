import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

load_dotenv()

# Force background tasks to finish
os.environ["LANGFUSE_DEBUG"] = "True"

print("Starting Langfuse Trace Test...")

@observe()
def nested_generation():
    print("  Executing nested generation...")
    langfuse_context.update_current_observation(
        name="test-generation",
        input="Hello",
        output="World",
        usage={"input_tokens": 10, "output_tokens": 10}
    )
    return "Done"

@observe()
def main_trace():
    print("Starting main trace...")
    langfuse_context.update_current_trace(
        name="Debug Trace",
        metadata={"test": True}
    )
    nested_generation()
    print("Main trace complete.")

if __name__ == "__main__":
    main_trace()
    print("Flushing Langfuse...")
    langfuse_context.flush()
    print("Finished. Check your dashboard for 'Debug Trace'.")
