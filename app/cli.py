import argparse
from pathlib import Path
from app.pipeline import Pipeline
from app.orchestrator import run_dataset

def main():
    p = argparse.ArgumentParser(description="AIOrbit Curator")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db")

    x = sub.add_parser("ingest")
    x.add_argument("--module", required=True)
    x.add_argument("--file", required=True)

    v = sub.add_parser("verify")
    v.add_argument("--module", required=True)

    c = sub.add_parser("curate")
    c.add_argument("--module", required=True)

    e = sub.add_parser("export")
    e.add_argument("--module", required=True)
    e.add_argument("--output", required=True)

    r = sub.add_parser("run")
    r.add_argument("--module", required=True)
    r.add_argument("--file", required=True)
    r.add_argument("--output", required=True)

    args = p.parse_args()

    if args.cmd == "run":
        run_dataset(args.module, args.file, args.output)
        return

    pipeline = Pipeline()
    if args.cmd == "init-db":
        pipeline.init_db()
    elif args.cmd == "ingest":
        pipeline.ingest(args.module, Path(args.file))
    elif args.cmd == "verify":
        pipeline.verify(args.module)
    elif args.cmd == "curate":
        pipeline.curate(args.module)
    elif args.cmd == "export":
        pipeline.export(args.module, Path(args.output))

if __name__ == "__main__":
    main()
