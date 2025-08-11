import streamlit as st
from utils import normalizar, score_para_cor, max_cor

FLUXOS = {}  # Catálogo principal

def calcular_cor_final(cores, sintomas, sistemas_sintomas):
    ordem_cores = ["verde", "amarelo", "laranja", "vermelho"]
    cor_base = max(cores, key=lambda c: ordem_cores.index(c))
    contador_por_sistema = {}
    for sistema, lista in sistemas_sintomas.items():
        sintomas_sistema = [s.lower() for s in lista]
        contador = sum(1 for s in sintomas if s.lower() in sintomas_sistema)
        contador_por_sistema[sistema] = contador

    reforco = 0
    for sistema, qtd in contador_por_sistema.items():
        if sistema in ["neurológico", "cardíaco"]:
            if qtd >= 3:
                reforco = max(reforco, 2)
            elif qtd == 2:
                reforco = max(reforco, 1)
        elif qtd >= 3:
            reforco = max(reforco, 1)

    idx = ordem_cores.index(cor_base)
    cor_final = ordem_cores[min(idx + reforco, len(ordem_cores) - 1)]
    return cor_final

def coletar_respostas_fluxo(sintoma_label):
    chave = normalizar(sintoma_label)
    cfg = FLUXOS.get(chave)
    if not cfg:
        return None
    if "fluxo_respostas" not in st.session_state:
        st.session_state["fluxo_respostas"] = {}
    if chave not in st.session_state["fluxo_respostas"]:
        st.session_state["fluxo_respostas"][chave] = {}

    respostas = st.session_state["fluxo_respostas"][chave]

    for p in cfg["perguntas"]:
        pid, label, tipo, opcoes = p["id"], p["label"], p["tipo"], p["opcoes"]
        if tipo == "radio":
            escolha = st.radio(label, list(opcoes.keys()), key=f"{chave}_{pid}")
            respostas[pid] = escolha
        elif tipo == "checkbox":
            marcados = []
            for k in opcoes.keys():
                if st.checkbox(k, key=f"{chave}_{pid}_{normalizar(k)}"):
                    marcados.append(k)
            respostas[pid] = marcados
        elif tipo == "multiselect":
            escolha = st.multiselect(label, list(opcoes.keys()), key=f"{chave}_{pid}")
            respostas[pid] = escolha
        else:
            st.warning(f"Tipo de pergunta não suportado: {tipo}")

    return respostas

def pontuar_fluxo(sintoma_label, respostas):
    chave = normalizar(sintoma_label)
    cfg = FLUXOS[chave]
    score = 0.0
    for p in cfg["perguntas"]:
        pid, tipo, opcoes = p["id"], p["tipo"], p["opcoes"]
        r = respostas.get(pid)
        if r is None:
            continue
        if tipo == "radio":
            score += opcoes.get(r, 0.0)
        elif tipo in ("checkbox", "multiselect"):
            score += sum(opcoes.get(x, 0.0) for x in (r or []))

    cor_base = score_para_cor(score, cfg["mapeamento_cor"])
    min_cor = None
    for regra in cfg.get("regras_excecao", []):
        cond = regra["se"]
        ok = True
        for k, v in cond.items():
            resp = respostas.get(k)
            if isinstance(v, list):
                if not resp or (isinstance(resp, list) and not any(x in resp for x in v)):
                    ok = False
            else:
                if resp != v:
                    ok = False
        if ok:
            cand = regra["min_cor"]
            min_cor = cand if not min_cor else max_cor(min_cor, cand)
    cor_final = max_cor(cor_base, min_cor) if min_cor else cor_base
    return cor_final, score

def labels_fluxos():
    return [cfg.get("label", k.replace("_", " ").title()) for k, cfg in FLUXOS.items()]

def eh_fluxo(label):
    return normalizar(label) in FLUXOS

