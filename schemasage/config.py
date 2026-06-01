from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DEMO_DB_PATH = ROOT_DIR / "data" / "demo" / "schemasage.sqlite3"

GENERATOR_BACKEND = os.getenv("SCHEMASAGE_GENERATOR_BACKEND", "rules").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
LORA_BASE_MODEL = os.getenv("LORA_BASE_MODEL", "Qwen/Qwen2.5-Coder-0.5B-Instruct")
LORA_ADAPTER_PATH = os.getenv(
    "LORA_ADAPTER_PATH",
    str(ROOT_DIR / "artifacts" / "lora" / "schemasage-qwen-0.5b-adapter"),
)
