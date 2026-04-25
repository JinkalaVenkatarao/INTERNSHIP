#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  Real Estate Price Prediction — Local Setup Script
#  Usage: bash scripts/setup_local.sh
# ══════════════════════════════════════════════════════════════════════════════
set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log()  { echo -e "${GREEN}[SETUP]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}   $*"; }
die()  { echo -e "${RED}[ERROR]${NC}  $*"; exit 1; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
log "Project root: $PROJECT_ROOT"

# ── 1. Python version check ──────────────────────────────────────────────────
log "Checking Python version …"
python3 -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'" \
  || die "Python 3.10+ is required. Please upgrade."
log "Python OK: $(python3 --version)"

# ── 2. Virtual environment ────────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
  log "Creating virtual environment …"
  python3 -m venv .venv
fi
source .venv/bin/activate
log "Virtual environment: activated"

# ── 3. Install dependencies ──────────────────────────────────────────────────
log "Installing Python dependencies …"
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Dependencies installed"

# ── 4. Train ML model ─────────────────────────────────────────────────────────
log "Training ML model (this may take 1–2 minutes) …"
export PYTHONPATH="$PROJECT_ROOT"
python ml-pipeline/training/train.py
log "Model trained and saved"

# ── 5. Run test suite ─────────────────────────────────────────────────────────
log "Running test suite …"
export PROJECT_ROOT="$PROJECT_ROOT"
python -m pytest tests/ -v --tb=short -q
log "All tests passed ✅"

# ── 6. Start API server ───────────────────────────────────────────────────────
log "Starting FastAPI server …"
echo ""
echo "══════════════════════════════════════════════════════"
echo "  🏠 Real Estate Price Prediction API"
echo "  API:      http://localhost:8000"
echo "  Docs:     http://localhost:8000/api/docs"
echo "  Health:   http://localhost:8000/api/v1/health"
echo "  Frontend: Open frontend/src/index.html in browser"
echo "══════════════════════════════════════════════════════"
echo ""
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
