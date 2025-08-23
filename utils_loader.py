# utils_loader.py
from __future__ import annotations
import os
import pathlib
import time
import hashlib
from typing import Optional

import joblib
import requests  # já está no seu requirements.txt

# Onde salvar durante a execução (FS efêmero)
MODEL_DIR = pathlib.Path(os.getenv("MODEL_DIR", "/tmp/models"))
MODEL_FILE = os.getenv("MODEL_FILE", "model.pkl")
LOCAL_PATH = MODEL_DIR / MODEL_FILE

# Origem direta (GitHub Releases / HuggingFace / S3 etc.)
MODEL_URL = os.getenv("MODEL_URL", "").strip()

# Opcional: verificação de integridade
MODEL_SHA256 = os.getenv("MODEL_SHA256", "").lower().strip()  # hash do arquivo (64 hex)

# Tuning de download
CHUNK_SIZE = 4 * 1024 * 1024   # 4 MB por chunk (bom pra 225 MB)
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0  # segundos (exponencial)


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_sha256(path: pathlib.Path, expected: str) -> None:
    if not expected:
        return
    got = _sha256_file(path)
    if got != expected:
        path.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA256 inválido do modelo.\nEsperado: {expected}\nObtido:  {got}"
        )


def _stream_download(url: str, dst: pathlib.Path) -> None:
    """
    Baixa em streaming com retries. Funciona com GitHub Releases (redireciona p/ S3).
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", "0")) or None
                downloaded = 0
                # grava em arquivo temporário e renomeia no final (atomicidade)
                tmp = dst.with_suffix(dst.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                tmp.replace(dst)
            return
        except Exception as e:
            last_err = e
            if attempt == MAX_RETRIES:
                break
            time.sleep(RETRY_BACKOFF * (2 ** (attempt - 1)))
    raise RuntimeError(f"Falha ao baixar modelo de {url}: {last_err}")


def _ensure_model_file() -> None:
    """
    1) Se já existe em disco, usa (opcionalmente checa SHA-256).
    2) Senão, baixa de MODEL_URL e verifica (se hash fornecido).
    """
    if LOCAL_PATH.exists():
        _verify_sha256(LOCAL_PATH, MODEL_SHA256)
        return

    if not MODEL_URL:
        raise RuntimeError(
            "Modelo não encontrado e MODEL_URL não configurado.\n"
            f"Procurei: {LOCAL_PATH}\n"
            "Defina a env MODEL_URL com link DIRETO para o .pkl/.joblib (GitHub Releases, S3, etc.).\n"
            "Opcional: defina MODEL_SHA256 para verificação de integridade."
        )

    _stream_download(MODEL_URL, LOCAL_PATH)
    _verify_sha256(LOCAL_PATH, MODEL_SHA256)


def load_model():
    """
    Baixa (se necessário) e carrega com joblib.
    Garanta que a versão de scikit-learn no requirements é compatível com a usada ao salvar.
    """
    _ensure_model_file()
    return joblib.load(LOCAL_PATH)
