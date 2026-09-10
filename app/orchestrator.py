from pathlib import Path
from app.pipeline import Pipeline

MODULES = ("tools", "companies", "agents", "mcp", "robots", "devices", "models", "news")

def run_dataset(module, input_file, output_file):
    if module not in MODULES:
        raise ValueError(f"Unsupported module: {module}")
    p = Pipeline()
    p.init_db()
    p.ingest(module, Path(input_file))
    p.verify(module)
    p.curate(module)
    p.export(module, Path(output_file))
