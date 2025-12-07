import os


def get(name: str, default: str = ""):
    return os.getenv(f"EASY_PATH_{name}", default)


def choose(module_value: str, env_name: str):
    env_val = os.getenv(f"EASY_PATH_{env_name}")
    return env_val if env_val else module_value

