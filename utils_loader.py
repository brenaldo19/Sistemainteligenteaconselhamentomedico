# utils_loader.py
from __future__ import annotations
import os
import pathlib
import joblib

# Onde o arquivo do modelo fica salvo DURANTE a execução (sem disk persistente)
MODEL_DIR = pathlib.Path(os.getenv("MODEL_DIR", "/tmp/models"))
MODEL_FILE = os.getenv("MODEL_FILE", "model.pkl")
LOCAL_PATH = MODEL_DIR / MODEL_FILE

# ID do arquivo no Google Drive (defina em Settings → Environment do Render)
GDRIVE_ID = os.getenv("GDRIVE_ID")  # ex.: "1AbCDeFgHiJKLmn..."
# Se quiser, pode ter também uma URL direta como fallback (opcional)
MODEL_URL = os.getenv("MODEL_URL")  # ex.: "https://.../model.pkl"

def _download_from_gdrive(file_id: str, dst: pathlib.Path) -> None:
    """
    Baixa do Google Drive usando gdown. Precisa de:
      - pip install gdown
      - arquivo no Drive com permissão de 'Anyone with the link (Viewer)'
    """
    import gdown
    url = f"https://drive.google.com/uc?id={file_id}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(url, str(dst), quiet=False)

def _download_from_url(url: str, dst: pathlib.Path) -> None:
    """
    Fallback opcional via URL direta (o URL deve apontar para o binário, não página HTML).
    """
    import urllib.request
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dst, "wb") as f:
        f.write(r.read())

def _ensure_model_file() -> None:
    """
    Garante que LOCAL_PATH existe. Se não existir, tenta:
      1) GDRIVE_ID (obrigatório no seu caso)
      2) MODEL_URL (fallback opcional)
    """
    if LOCAL_PATH.exists():
        return
    if GDRIVE_ID:
        _download_from_gdrive(GDRIVE_ID, LOCAL_PATH)
        return
    if MODEL_URL:
        _download_from_url(MODEL_URL, LOCAL_PATH)
        return
    raise RuntimeError(
        "Modelo não encontrado e nenhuma origem configurada.\n"
        f"Procurei: {LOCAL_PATH}\n"
        "Defina GDRIVE_ID (Google Drive) OU MODEL_URL (link direto)."
    )

def load_model():
    """
    Baixa se necessário e carrega o modelo com joblib.
    Importante: fixe a mesma versão de scikit-learn usada para salvar o modelo.
    """
    _ensure_model_file()
    return joblib.load(LOCAL_PATH)
