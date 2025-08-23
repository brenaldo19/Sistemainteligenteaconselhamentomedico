# utils_loader.py
from __future__ import annotations
import os
import pathlib
import typing as t

# Dependências: joblib (pra modelos scikit), gdown (opcional)
import joblib

MODEL_DIR = pathlib.Path(os.getenv("MODEL_DIR", "models"))
MODEL_FILE = os.getenv("MODEL_FILE", "model.pkl")
LOCAL_PATH = MODEL_DIR / MODEL_FILE

GDRIVE_ID = os.getenv("GDRIVE_ID")         # ex: "1AbCDeFg..."
MODEL_URL = os.getenv("MODEL_URL")         # ex: "https://huggingface.co/.../model.pkl" ou S3/RAW GitHub

def _download_from_gdrive(file_id: str, dst: pathlib.Path) -> None:
    try:
        import gdown  # já está no teu requirements
    except Exception as e:
        raise RuntimeError(
            "gdown não está instalado para baixar do Google Drive; "
            "instale ou use MODEL_URL."
        ) from e
    url = f"https://drive.google.com/uc?id={file_id}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(url, str(dst), quiet=False)

def _download_from_url(url: str, dst: pathlib.Path) -> None:
    import urllib.request
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dst, "wb") as f:
        f.write(r.read())

def _try_load(path: pathlib.Path):
    # prefer joblib (compatível com scikit-learn). Troque para pickle se precisar.
    return joblib.load(path)

def load_model():
    """
    Estratégia:
    1) Se LOCAL_PATH existir, carrega.
    2) Se não existir:
       - tenta GDRIVE_ID
       - tenta MODEL_URL
    3) Se nada disso, explica como configurar.
    """
    # 1) Local
    if LOCAL_PATH.exists():
        return _try_load(LOCAL_PATH)

    # 2) Fallbacks de download
    if GDRIVE_ID:
        try:
            _download_from_gdrive(GDRIVE_ID, LOCAL_PATH)
            return _try_load(LOCAL_PATH)
        except Exception as e:
            raise RuntimeError(f"Falha ao baixar do Google Drive (id={GDRIVE_ID}): {e}") from e

    if MODEL_URL:
        try:
            _download_from_url(MODEL_URL, LOCAL_PATH)
            return _try_load(LOCAL_PATH)
        except Exception as e:
            raise RuntimeError(f"Falha ao baixar de MODEL_URL ({MODEL_URL}): {e}") from e

    # 3) Ajuda clara
    raise RuntimeError(
        "Modelo não encontrado e nenhuma origem configurada.\n"
        f"Procurei: {LOCAL_PATH}\n\n"
        "Como resolver:\n"
        "  • Opção A: suba o arquivo do modelo no repositório em 'models/model.pkl'\n"
        "  • Opção B: configure uma dessas variáveis de ambiente no Render:\n"
        "      - GDRIVE_ID = <id do arquivo no Google Drive>\n"
        "      - MODEL_URL = <URL direta para o .pkl/.joblib>\n"
        "    (Opcional) MODEL_DIR/ MODEL_FILE para mudar caminho/nome."
    )
