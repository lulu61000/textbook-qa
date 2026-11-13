from src.llm import get_llm
print(get_llm().generate("Say your model name and version and nothing else."))
print("Ready")