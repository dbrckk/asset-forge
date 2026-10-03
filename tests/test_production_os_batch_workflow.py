from pathlib import Path


WORKFLOW = Path(".github/workflows/production-os-batch.yml").read_text(
    encoding="utf-8"
)


def test_production_os_batch_accepts_repository_dispatch_fallback():
    assert "repository_dispatch:" in WORKFLOW
    assert "types: [production-os-asset-batch]" in WORKFLOW
    assert (
        "github.event.client_payload.correlation_id || inputs.correlation_id"
        in WORKFLOW
    )
    assert "github.event.client_payload.spec_json || inputs.spec_json" in WORKFLOW
    assert "github.event.client_payload.backend || inputs.backend || 'auto'" in WORKFLOW
    assert "github.event.client_payload.model || inputs.model || ''" in WORKFLOW


def test_production_os_batch_normalizes_both_transports_before_execution():
    assert "POS_CORRELATION_ID:" in WORKFLOW
    assert "POS_SPEC_JSON:" in WORKFLOW
    assert "POS_BACKEND:" in WORKFLOW
    assert "POS_MODEL:" in WORKFLOW
    assert 'SPEC_JSON: ${{ env.POS_SPEC_JSON }}' in WORKFLOW
    assert '--backend "$POS_BACKEND"' in WORKFLOW
    assert 'if [ -n "$POS_MODEL" ]; then' in WORKFLOW
    assert 'name: asset-forge-batch-${{ env.POS_CORRELATION_ID }}' in WORKFLOW


def test_production_os_batch_keeps_manual_dispatch_contract():
    assert "workflow_dispatch:" in WORKFLOW
    assert "correlation_id:" in WORKFLOW
    assert "spec_json:" in WORKFLOW
    assert "backend:" in WORKFLOW
    assert "model:" in WORKFLOW
