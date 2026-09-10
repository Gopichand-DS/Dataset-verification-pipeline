from pathlib import Path
from app.pipeline import Pipeline

p = Pipeline()
p.init_db()
p.ingest("tools", Path("data/input/tools.csv"))
p.verify("tools")
p.curate("tools")
p.export("tools", Path("data/output/tools_curated.csv"))
