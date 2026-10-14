from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/production-os-ai-dev-server-live-e2e.yml"
).read_text(encoding="utf-8")


def test_cross_repo_live_e2e_uses_current_collaborators():
    assert "repository: dbrckk/ai-dev-server" in WORKFLOW
    assert "repository: dbrckk/deadline-zero" in WORKFLOW
    assert 'PYTHONPATH="$GITHUB_WORKSPACE/ai-dev-server/studio"' in WORKFLOW
    assert "from production_os_worker import build_studio_request" in WORKFLOW


def test_cross_repo_live_e2e_requires_real_asset_backend():
    assert "CLOUDFLARE_API_TOKEN" in WORKFLOW
    assert "KAGGLE_API_TOKEN" in WORKFLOW
    assert "POLLINATIONS_API_KEY" in WORKFLOW
    assert "No real Asset Forge image-generation backend is configured." in WORKFLOW
    assert "exit 2" in WORKFLOW
    # Commercial target art cannot fall through to research-licensed or
    # commercially unqualified inference providers after credential selection.
    assert "- name: Require commercial-safe raster model" in WORKFLOW
    assert 'if [ "$SELECTED_BACKEND" != "cloudflare" ]; then' in WORKFLOW
    assert "Cloudflare FLUX.2 Klein 4B route" in WORKFLOW
    assert WORKFLOW.index("- name: Require commercial-safe raster model") < WORKFLOW.index("- name: Install live toolchain")
    # Live generation can be metered: a change/push must NEVER run it.
    assert "  push:\n" not in WORKFLOW
    assert "  workflow_dispatch:\n" in WORKFLOW
    assert "approve_provider_usage:" in WORKFLOW
    assert "default: false" in WORKFLOW
    assert 'APPROVED: ${{ inputs.approve_provider_usage }}' in WORKFLOW
    assert "Explicit provider usage approval is required before generation." in WORKFLOW
    assert WORKFLOW.index("- name: Require explicit live-generation approval") < WORKFLOW.index("- name: Select live generation backend")


def test_cross_repo_live_e2e_generates_and_compiles_target():
    assert "asset-forge fulfill" in WORKFLOW
    assert '--model "@cf/black-forest-labs/flux-2-klein-4b"' in WORKFLOW
    assert "asset-forge validate-production-report" in WORKFLOW
    assert "live-production-pipeline-icon.png" in WORKFLOW
    assert "gradle :core:compileJava :core:test :desktop:compileJava" in WORKFLOW
    assert "deadlineZeroCompileAndTests" in WORKFLOW


def test_cross_repo_live_e2e_persists_evidence():
    assert "assetForgeReportSuccess" in WORKFLOW
    assert "artifactSha256" in WORKFLOW
    assert "production-os-ai-dev-server-asset-forge-live-e2e" in WORKFLOW
    # Prove the completed boundaries accurately: the studio request is local,
    # not evidence of a hosted Production-OS execution or target PR delivery.
    assert '"handoffScope":"local-protocol-adapter-only"' in WORKFLOW
    assert '"hostedProductionOsJobExecuted":False' in WORKFLOW
    assert '"targetRepoPRCreated":False' in WORKFLOW
    assert '"liveGeneration":report.get("success") is True' in WORKFLOW
    assert "No hosted Production-OS job or target GitHub PR was executed" in WORKFLOW


def test_cross_repo_live_e2e_scopes_credentials_and_records_exact_revisions():
    assert WORKFLOW.count("persist-credentials: false") == 3
    pre_generation = WORKFLOW.split("- name: Select live generation backend", 1)[0]
    assert "CLOUDFLARE_API_TOKEN" not in pre_generation
    assert "KAGGLE_API_TOKEN" not in pre_generation
    assert "POLLINATIONS_API_KEY" not in pre_generation
    assert WORKFLOW.count("CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}") == 3
    assert WORKFLOW.count("KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_API_TOKEN }}") == 3
    assert WORKFLOW.count("POLLINATIONS_API_KEY: ${{ secrets.POLLINATIONS_API_KEY }}") == 3
    assert "id: revisions" in WORKFLOW
    assert '"assetForgeSha":os.environ["ASSET_FORGE_SHA"]' in WORKFLOW
    assert '"aiDevServerSha":os.environ["AI_DEV_SERVER_SHA"]' in WORKFLOW
    assert '"deadlineZeroSha":os.environ["DEADLINE_ZERO_SHA"]' in WORKFLOW
    assert "asset-forge/production-os-ai-dev-server-live-e2e/v2" in WORKFLOW

