# utils_loader.py
import os, re, json, time, math
import requests

GITHUB_API = os.getenv("GITHUB_API_URL", "https://api.github.com")

# ---- Helpers ----

def _parse_release_download_url(url: str):
    """
    Aceita URL no formato:
    https://github.com/{owner}/{repo}/releases/download/{tag}/{asset_name}
    Retorna (owner, repo, tag, asset_name) ou None se não casar.
    """
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
    # Trata limites de rate de forma amigável (apenas 1 retry simples)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            wait = max(0, int(reset) - int(time.time())) + 2
            time.sleep(min(wait, 10))  # espera curta
            r = requests.get(url, headers=h, params=params, timeout=timeout)
    r.raise_for_status()
    return r

def _download_github_release_asset_with_token(url: str, dest_path: str, chunk=1024*1024, timeout=90):
    """
    Para repo privado: usa a API do GitHub para:
      1) Ler o release pela tag
      2) Achar o asset pelo nome
      3) Baixar via /releases/assets/{asset_id} com Accept: application/octet-stream
    """
    parsed = _parse_release_download_url(url)
    if not parsed:
        raise RuntimeError("URL de release inválida para modo autenticado (não segue releases/download/{tag}/{asset}).")
    owner, repo, tag, asset_name = parsed

    # 1) Buscar release pela tag
    rel_url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/tags/{tag}"
    rel = _github_get(rel_url).json()

    # 2) Procurar asset pelo nome (case sensitive)
    assets = rel.get("assets", [])
    target = None
    for a in assets:
        if a.get("name") == asset_name:
            target = a
            break
    if not target:
        nomes = [a.get("name") for a in assets]
        raise RuntimeError(
            f"Asset '{asset_name}' não encontrado no release '{tag}'. "
            f"Assets disponíveis: {nomes}"
        )

    asset_id = target.get("id")
    if not asset_id:
        raise RuntimeError("Asset sem id retornado pela API.")

    # 3) Download binário do asset
    asset_url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/assets/{asset_id}"
    headers = {
        "Accept": "application/octet-stream"  # força o binário
    }
    r = _github_get(asset_url, headers=headers, timeout=timeout)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk_bytes in r.iter_content(chunk_size=chunk):
            if chunk_bytes:
                f.write(chunk_bytes)

    if os.path.getsize(dest_path) == 0:
        raise RuntimeError("Arquivo baixado com tamanho 0 (asset).")

def _stream_download_public_or_token(url: str, dest_path: str, chunk=1024*1024, timeout=90):
    """
    Tenta baixar direto do link (com token se existir). Útil como fallback.
    Obs: para private releases o GitHub pode redirecionar e perder Authorization.
    """
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/octet-stream"

    with requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk_bytes in r.iter_content(chunk_size=chunk):
                if chunk_bytes:
                    f.write(chunk_bytes)
    if os.path.getsize(dest_path) == 0:
        raise RuntimeError("Arquivo baixado com tamanho 0 (http).")

def _stream_download(url: str, dest_path: str, chunk=1024*1024, tries=2, timeout=90):
    """
    Estratégia:
      - Se a URL é releases/download/... e há GITHUB_TOKEN -> usa API (privado confiável)
      - Caso falhe, tenta o link direto (com/sem token) como fallback
    """
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
            # curto delay e tenta fallback/segunda tentativa
            time.sleep(1.2)

    raise RuntimeError(f"Falha ao baixar modelo de {url}: {last_err}")

# ---- Ponto de entrada no seu loader atual ----

def _ensure_model_file():
    """
    Ajuste aqui seus candidatos/variáveis. Mantém compatibilidade com MODEL_URL.
    """
    local_dir = "/opt/render/project/src/models"
    os.makedirs(local_dir, exist_ok=True)

    # nome final do arquivo local (ajuste se quiser)
    asset_name = "modelo_sintomas_v3_nolex.pkl"
    local_path = os.path.join(local_dir, asset_name)

    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path

    candidates = [
        os.getenv("MODEL_URL"),  # prioriza o que veio do env
        # exemplo fallback (se você quiser manter um 'latest'):
        # "https://github.com/owner/repo/releases/latest/download/modelo_sintomas_v3_nolex.pkl",
    ]

    last_err = None
    for url in [u for u in candidates if u]:
        try:
            _stream_download(url, local_path)
            return local_path
        except Exception as e:
            last_err = e

    raise RuntimeError(f"Falha ao baixar modelo: {last_err}")
