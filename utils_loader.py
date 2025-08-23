# utils_loader.py
import os
import re
import time
import requests
import joblib
import pickle
from pathlib import Path

GITHUB_API = os.getenv("GITHUB_API_URL", "https://api.github.com")

# =========================
# PARTE 1 — DOWNLOAD (privado com token + fallback)
# =========================

def _parse_release_download_url(url: str):
    m = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$", url
    )
    if not m:
        return None
    owner, repo, tag, asset = m.group(1), m.group(2), m.group(3), m.group(4)
    return owner, repo, tag, asset

def _github_get(url, headers=None, params=None, timeout=60):
    h = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    if headers:
        h.update(headers)
    r = requests.get(url, headers=h, params=params, timeout=timeout)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            wait = max(0, int(reset) - int(time.time())) + 2
            time.sleep(min(wait, 10))
            r = requests.get(url, headers=h, params=params, timeout=timeout)
    r.raise_for_status()
    return r

def _download_github_release_asset_with_token(url: str, dest_path: Path, chunk=1024*1024, timeout=90):
    parsed = _parse_release_download_url(url)
    if not parsed:
        raise RuntimeError("URL inválida para modo autenticado (esperado releases/download/{tag}/{asset}).")
    owner, repo, tag, asset_name = parsed

    rel_url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/tags/{tag}"
    rel = _github_get(rel_url).json()

    assets = rel.get("assets", [])
    target = next((a for a in assets if a.get("name") == asset_name), None)
    if not target:
        nomes = [a.get("name") for a in assets]
        raise RuntimeError(f"Asset '{asset_name}' não encontrado no release '{tag}'. Assets: {nomes}")

    asset_id = target.get("id")
    if not asset_id:
        raise RuntimeError("Asset sem id retornado pela API.")

    asset_url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/assets/{asset_id}"
    headers = {"Accept": "application/octet-stream"}
    r = _github_get(asset_url, headers=headers, timeout=timeout)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk_bytes in r.iter_content(chunk_size=chunk):
            if chunk_bytes:
                f.write(chunk_bytes)

    if dest_path.stat().st_size == 0:
        raise RuntimeError("Arquivo baixado com tamanho 0 (asset).")

def _stream_download_public_or_token(url: str, dest_path: Path, chunk=1024*1024, timeout=90):
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/octet-stream"

    with requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk_bytes in r.iter_content(chunk_size=chunk):
                if chunk_bytes:
                    f.write(chunk_bytes)

    if dest_path.stat().st_size == 0:
        raise RuntimeError("Arquivo baixado com tamanho 0 (http).")

def _stream_download(url: str, dest_path: Path, chunk=1024*1024, tries=2, timeout=90):
    last_err = None
    use_api_first = bool(os.getenv("GITHUB_TOKEN")) and _parse_release_download_url(url) is not None

    for attempt in range(tries):
        try:
            if use_api_first and attempt == 0:
                _download_github_release_asset_with_token(url, dest_path, chunk=chunk, timeout=timeout)
                return
            else:
                _stream_download_public_or_token(url, dest_path, chunk=chunk, timeout=timeout)
                return
        except Exception as e:
            last_err = e
            time.sleep(1.2)

    raise RuntimeError(f"Falha ao baixar modelo de {url}: {last_err}")

def _ensure_model_file() -> Path:
    """
    Baixa (se necessário) e retorna o caminho local do arquivo de modelo.
    Usa MODEL_URL do ambiente. Ajuste o nome local se quiser.
    """
    local_dir = Path("/opt/render/project/src/models")
    asset_name = os.getenv("MODEL_FILENAME", "modelo_sintomas_v3_nolex.pkl")
    local_path = local_dir / asset_name

    if local_path.exists() and local_path.stat().st_size > 0:
        return local_path

    candidates = [os.getenv("MODEL_URL")]
    last_err = None
    for url in [u for u in candidates if u]:
        try:
            _stream_download(url, local_path)
            return local_path
        except Exception as e:
            last_err = e

    raise RuntimeError(f"Falha ao baixar modelo: {last_err}")

# =========================
# PARTE 2 — CARREGAMENTO DO MODELO (público)
# =========================

def load_model():
    """
    Função pública que o streamlit_app.py importa.
    - Garante o arquivo local do modelo (baixa se não existir)
    - Tenta carregar com joblib; se falhar, tenta pickle
    """
    model_path = _ensure_model_file()
    # 1) joblib
    try:
        return joblib.load(model_path)
    except Exception:
        pass
    # 2) pickle
    with open(model_path, "rb") as f:
        return pickle.load(f)

__all__ = ["load_model"]
