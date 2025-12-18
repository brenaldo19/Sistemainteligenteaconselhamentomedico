# utils_loader.py
import os, time, requests
from pathlib import Path
import joblib, pickle

GITHUB_API = os.getenv("GITHUB_API_URL", "https://api.github.com")

def _gh_headers(extra=None):
    h = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token: h["Authorization"] = f"Bearer {token}"
    if extra: h.update(extra)
    return h

def _gh_get(url, headers=None, timeout=60):
    r = requests.get(url, headers=_gh_headers(headers), timeout=timeout)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            wait = max(0, int(reset) - int(time.time())) + 1
            time.sleep(min(wait, 10))
            r = requests.get(url, headers=_gh_headers(headers), timeout=timeout)
    r.raise_for_status()
    return r

def _find_asset(owner: str, repo: str, tag: str, asset_name: str):
    # tag = "latest" ou uma tag específica
    url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest" if tag == "latest" \
          else f"{GITHUB_API}/repos/{owner}/{repo}/releases/tags/{tag}"
    rel = _gh_get(url).json()
    for a in rel.get("assets", []):
        if a.get("name") == asset_name:
            return a   # tem .id, .name, etc.
    disp = [a.get("name") for a in rel.get("assets", [])]
    raise RuntimeError(f"Asset '{asset_name}' não encontrado na tag '{tag}'. Disponíveis: {disp}")

def _download_asset(owner: str, repo: str, asset_id: int, dest: Path):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/assets/{asset_id}"
    r = _gh_get(url, headers={"Accept": "application/octet-stream"})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk: f.write(chunk)
    if dest.stat().st_size == 0:
        raise RuntimeError("Arquivo baixado com tamanho 0.")
import os

os.environ["MODEL_OWNER"] = "nome_do_dono"
os.environ["MODEL_REPO"] = "nome_do_repo"
os.environ["MODEL_ASSET"] = "arquivo_do_modelo"

def _ensure_model_file() -> Path:
    owner = os.getenv("MODEL_OWNER")
    repo  = os.getenv("MODEL_REPO")
    tag   = os.getenv("MODEL_TAG", "latest")
    asset = os.getenv("MODEL_ASSET")  # nome EXATO do arquivo no release
    if not all([owner, repo, asset]):
        raise RuntimeError("Defina MODEL_OWNER, MODEL_REPO e MODEL_ASSET (e opcional MODEL_TAG).")

    local_dir = Path("/opt/render/project/src/models")
    local_name = os.getenv("MODEL_FILENAME", asset)
    local_path = local_dir / local_name
    if local_path.exists() and local_path.stat().st_size > 0:
        return local_path

    a = _find_asset(owner, repo, tag, asset)
    _download_asset(owner, repo, a["id"], local_path)
    return local_path

def load_model():
    model_path = _ensure_model_file()
    try:
        return joblib.load(model_path)
    except Exception:
        with open(model_path, "rb") as f:
            return pickle.load(f)
