import subprocess
try:
    import llama_cpp
    print("llama-cpp-python is already installed.")
except ImportError:
    print("llama-cpp-python is NOT installed.")
