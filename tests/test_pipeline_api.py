
from pathlib import Path

from app.pipeline import Pipeline


def test_pipeline_exposes_end_to_end_api():
    assert hasattr(Pipeline(), "ingest")
    assert hasattr(Pipeline(), "verify")
    assert hasattr(Pipeline(), "curate")
    assert hasattr(Pipeline(), "export")


def test_public_adapter_does_not_require_tenacity():
    from app.adapters.webpage import WebPageAdapter
    assert WebPageAdapter().retries >= 1
