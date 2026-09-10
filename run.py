from __future__ import annotations
import argparse, json
from pathlib import Path
from app.pipeline import Pipeline, ingest_candidates

MODULES = {"tools","companies","agents","mcp","robots","devices","models","news"}

def main():
    p = argparse.ArgumentParser(description="AIOrbit production runner")
    p.add_argument("--module", required=True, choices=sorted(MODULES))
    p.add_argument("--input")
    p.add_argument("--output")
    p.add_argument("--discover", action="store_true")
    p.add_argument("--workflow", action="store_true",
                   help="Run discovery + independent official URL verification + acceptance gate")
    p.add_argument("--no-secondary", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--fresh-output", action="store_true",
                   help="Replace the workflow output file instead of updating the existing master file")
    args = p.parse_args()

    if args.workflow:
        from app.discovery.workflow import DiscoveryWorkflow
        input_records = None
        input_source = "live_discovery"
        if args.input:
            from app.discovery.workflow import read_input_records
            input_records = read_input_records(args.input)
            input_source = str(args.input)
        result = DiscoveryWorkflow().run(
            args.module,
            limit=args.limit,
            include_secondary=not args.no_secondary,
            input_records=input_records,
            input_source=input_source,
        )
        # A workflow run is persisted as one module-level master file. Re-running
        # the command upserts matching records instead of creating another snapshot.
        from app.discovery.persistent_store import upsert_workflow_file
        out = Path(args.output) if args.output else Path("data/output") / f"{args.module}_master.json"
        result = upsert_workflow_file(out, result, fresh=args.fresh_output)
        print(json.dumps({
            "module": args.module,
            "output": str(out),
            "store": result.get("store", {}),
            "metrics": result.get("metrics", {}),
        }, indent=2, ensure_ascii=False, default=str))
        return

    pipe = Pipeline()
    if args.discover:
        from app.discovery.engine import DiscoveryEngine
        dr = DiscoveryEngine().discover_module(args.module, include_secondary=not args.no_secondary)
        candidates = dr.candidates[:args.limit] if args.limit else dr.candidates
        if args.dry_run:
            print(json.dumps(dr.to_dict(), indent=2, ensure_ascii=False, default=str))
            if args.output:
                out=Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(dr.to_dict(), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            return
        print(f"ingested={len(ingest_candidates(candidates, args.module))}")
    elif args.input:
        print(f"ingested={pipe.ingest(args.module, Path(args.input))}")
    else:
        p.error("provide --input, --discover, or --workflow")

    print(f"verified_or_reviewed={len(pipe.verify(args.module))}")
    print(f"curation_results={len(pipe.curate(args.module))}")
    if args.output:
        print(f"exported={pipe.export(args.module, Path(args.output))}")

if __name__ == "__main__": main()
