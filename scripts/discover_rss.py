import argparse
from app.adapters.registry import build_rss_adapters

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    args = parser.parse_args()

    adapters = build_rss_adapters(args.module)
    for adapter in adapters:
        for item in adapter.discover():
            print(item)

if __name__ == "__main__":
    main()
