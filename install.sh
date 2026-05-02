#!/usr/bin/env bash
# MCTS Research Explorer — Installation Wizard
# Supports: Linux, WSL (Windows Subsystem for Linux), Termux (Android)
set -e

REPO="mcts-research-explorer"
PKG="mcts-explorer"
CONFIG_DIR="$HOME/.config/mcts-explorer"

# ── Platform Detection ─────────────────────────────────────────────────────
detect_platform() {
    if [ -n "${TERMUX_VERSION:-}" ] || [ -d "/data/data/com.termux" ]; then
        echo "termux"
    elif grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
    elif [ "$(uname -s)" = "Darwin" ]; then
        echo "macos"
    else
        echo "linux"
    fi
}

# ── Color Output ───────────────────────────────────────────────────────────
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${BLUE}[•]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Banner ─────────────────────────────────────────────────────────────────
echo -e "${BLUE}"
cat << 'EOF'
  __  __  ____ _____ ____    _____            _
 |  \/  |/ ___|_   _/ ___|  | ____|_  ___ __ | | ___  _ __ ___ _ __
 | |\/| | |     | | \___ \  |  _| \ \/ / '_ \| |/ _ \| '__/ _ \ '__|
 | |  | | |___  | |  ___) | | |___ >  <| |_) | | (_) | | |  __/ |
 |_|  |_|\____| |_| |____/  |_____/_/\_\ .__/|_|\___/|_|  \___|_|
                                         |_|
EOF
echo -e "${NC}"
echo "  MCTS-guided research query exploration"
echo "  Platform: $(detect_platform)"
echo ""

PLATFORM=$(detect_platform)

# ── Step 1: System Dependencies ────────────────────────────────────────────
info "Step 1: Checking system dependencies..."

case "$PLATFORM" in
    termux)
        # No sudo on Termux
        if ! command -v python3 &>/dev/null; then
            info "Installing Python via pkg..."
            pkg install -y python git
        fi
        if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
            pkg install -y python-pip
        fi
        ;;
    macos)
        if ! command -v python3 &>/dev/null; then
            error "Python 3.8+ required. Install via: brew install python3"
        fi
        ;;
    linux|wsl)
        if ! command -v python3 &>/dev/null; then
            info "Installing Python..."
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip python3-venv
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-pip
            elif command -v pacman &>/dev/null; then
                sudo pacman -Sy --noconfirm python python-pip
            else
                error "No supported package manager. Install Python 3.8+ manually."
            fi
        fi
        ;;
esac

PY=$(command -v python3 || command -v python)
PY_VER=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
success "Python $PY_VER found"

# ── Step 2: Virtual Environment ────────────────────────────────────────────
info "Step 2: Creating virtual environment..."

if [ "$PLATFORM" = "termux" ]; then
    # Termux: pip install --user (no venv issues)
    pip3 install --user -e . 2>/dev/null || $PY -m pip install --user -e .
    success "Installed (--user mode for Termux)"
else
    if [ ! -d ".venv" ]; then
        $PY -m venv .venv
        success "Created .venv"
    else
        info ".venv already exists"
    fi
    source .venv/bin/activate

    info "Installing $PKG..."
    pip install -e . -q
    success "$PKG installed in .venv"
fi

# ── Step 3: Optional Tools ─────────────────────────────────────────────────
info "Step 3: Optional tools (press Enter to skip any)"
echo ""
echo "  These tools enhance search_fn implementations but are NOT required:"
echo ""

install_tool() {
    local name="$1" cmd="$2" termux_pkg="$3" apt_pkg="$4" brew_pkg="$5"
    read -r -p "  Install $name ($cmd)? [y/N] " ans
    if [[ "$ans" =~ ^[Yy] ]]; then
        case "$PLATFORM" in
            termux) pkg install -y "$termux_pkg" && success "$name installed" ;;
            macos)  brew install "$brew_pkg" && success "$name installed" ;;
            *)      sudo apt-get install -y "$apt_pkg" 2>/dev/null \
                    || pip install "$name" 2>/dev/null \
                    || warn "Could not install $name automatically — see TOOLS.md" ;;
        esac
    fi
}

echo "  [httpx] Async HTTP client for search_fn implementations"
read -r -p "  Install httpx? [y/N] " ans_httpx
if [[ "$ans_httpx" =~ ^[Yy] ]]; then
    if [ "$PLATFORM" = "termux" ]; then pip3 install --user httpx
    else pip install httpx -q && success "httpx installed"
    fi
fi

echo "  [ddgr] DuckDuckGo CLI — zero-browser search (great default search_fn)"
install_tool "ddgr" "ddgr" "ddgr" "ddgr" "ddgr"

echo ""

# ── Step 4: Credential Configuration (MOSA Wizard) ────────────────────────
info "Step 4: Optional search provider API keys"
echo ""
echo "  mcts-explorer is search-provider-agnostic. Configure optional keys"
echo "  for built-in search_fn helpers. Leave blank to skip."
echo ""

mkdir -p "$CONFIG_DIR"
ENV_FILE="$CONFIG_DIR/config.env"

write_env() {
    local key="$1" value="$2"
    if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

read -r -p "  SearXNG base URL (e.g. http://localhost:8080) [skip]: " SEARXNG_URL
[ -n "$SEARXNG_URL" ] && write_env "SEARXNG_URL" "$SEARXNG_URL"

read -r -p "  Brave Search API key [skip]: " BRAVE_KEY
[ -n "$BRAVE_KEY" ] && write_env "BRAVE_SEARCH_API_KEY" "$BRAVE_KEY"

read -r -p "  Tavily API key [skip]: " TAVILY_KEY
[ -n "$TAVILY_KEY" ] && write_env "TAVILY_API_KEY" "$TAVILY_KEY"

if [ -s "$ENV_FILE" ]; then
    success "Credentials saved to $ENV_FILE (mode 600)"
    echo "  Load in Python: from dotenv import load_dotenv; load_dotenv('$ENV_FILE')"
else
    rm -f "$ENV_FILE"
    info "No credentials configured — using search_fn without keys"
fi

# ── Step 5: Verify Installation ────────────────────────────────────────────
info "Step 5: Verifying installation..."

if $PY -c "from mcts_explorer import MCTSResearchExplorer; print('OK')" 2>/dev/null; then
    success "mcts-explorer imports successfully"
else
    error "Import verification failed. Check output above."
fi

# ── Complete ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "  Quick start:"
if [ "$PLATFORM" = "termux" ]; then
    echo "    python3 examples/demo.py"
else
    echo "    source .venv/bin/activate"
    echo "    python examples/demo.py"
fi
echo ""
echo "  See README.md for integration examples."
echo ""
