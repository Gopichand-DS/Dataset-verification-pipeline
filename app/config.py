from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"
OUTPUT = DATA / "output"
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA / 'aiorbit.db'}")
MIN_SCORE = float(os.getenv("MIN_QUALITY_SCORE", "70"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))

for p in (DATA, RAW, OUTPUT):
    p.mkdir(parents=True, exist_ok=True)
