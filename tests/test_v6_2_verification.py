from app.discovery.verification_gate import VerificationResult

def test_verification_result_serializes():
    r = VerificationResult(
        url="https://example.com",
        status="verified",
        http_status=200,
        title="Example Domain",
        evidence={"content_type": "text/html"},
    )
    data = r.to_dict()
    assert data["title"] == "Example Domain"
    assert data["status"] == "verified"
