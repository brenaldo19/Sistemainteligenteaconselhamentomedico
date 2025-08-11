import unicodedata
import re

ORDEM_CORES = ["verde", "amarelo", "laranja", "vermelho"]

def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    t = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    t = t.strip().lower()
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^a-z0-9_]", "", t)
    return t

def max_cor(*cores):
    idx = [ORDEM_CORES.index(c) for c in cores if c in ORDEM_CORES]
    return ORDEM_CORES[max(idx)] if idx else "verde"

def score_para_cor(score, tabela):
    # tabela: [(limiar, "cor"), ...]
    tabela_ord = sorted(tabela, key=lambda x: x[0], reverse=True)
    for limiar, cor in tabela_ord:
        if score >= limiar:
            return cor
    return "verde"

def aumentar_cor_em_1_nivel(cor_atual):
    try:
        i = ORDEM_CORES.index(cor_atual)
        return ORDEM_CORES[min(i + 1, len(ORDEM_CORES)-1)]
    except ValueError:
        return cor_atual

def calcular_imc(altura, peso):
    try:
        return round(peso / (altura ** 2), 1)
    except Exception:
        return None

def classificar_imc(imc):
    if imc is None:
        return "Inválido"
    if imc < 18.5:
        return "Desnutrido"
    if imc >= 30:
        return "Obeso"
    return "Normal"
