import langchain
import os

print(f"Langchain file: {langchain.__file__}")
print(f"Langchain dir: {os.path.dirname(langchain.__file__)}")

try:
    import langchain.output_parsers
    print("langchain.output_parsers found")
except ImportError as e:
    print(f"langchain.output_parsers error: {e}")

try:
    from langchain.output_parsers import StructuredOutputParser
    print("StructuredOutputParser found in langchain.output_parsers")
except ImportError as e:
    print(f"StructuredOutputParser error: {e}")
