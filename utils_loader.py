# utils_loader.py
import os, pathlib, joblib

MODEL_LOCAL = pathlib.Path("modelo_sintomas_v3.pkl")

def have_model() -> bool:
    return MODEL_LOCAL.exists()

def download_model():
    file_id = os.getenv("MODEL_FILE_ID", "")
    url = os.getenv("https://drive.google.com/file/d/10ri-FwcJAByu5o-dM4JJvz_X4Ep9o0Q_/view?usp=drive_link", "")
    if file_id:
        import gdown
        gdown.download(id=file_id, output=str(MODEL_LOCAL), quiet=False)
    elif url:
        import urllib.request
        urllib.request.urlretrieve(url, MODEL_LOCAL)
    else:
        raise RuntimeError("Defina MODEL_FILE_ID (Drive) ou MODEL_URL.")

def load_model():
    if not have_model():
        raise RuntimeError("Modelo ainda não está disponível localmente.")
    return joblib.load(MODEL_LOCAL)
