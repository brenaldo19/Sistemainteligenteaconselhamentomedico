import streamlit as st
import time
import random
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent))
# Se seus módulos estão dentro de /src, descomente a linha abaixo:
# sys.path.append(str(Path(__file__).resolve().parent / "src"))

from dicionario import dic
from utils import calcular_imc, classificar_imc, normalizar, aumentar_cor_em_1_nivel
from dados_sintomas import sistemas_sintomas, sintoma_para_sistema
from logica import (
    gerar_sistemas_afetados_por_fatores,
    sistemas_afetados_secundariamente,
    verificar_se_deve_subir_cor,
    classificar_combinacao,
    calcular_ajuste_por_fatores_conservador,
)
from fluxos import FLUXOS, coletar_respostas_fluxo, pontuar_fluxo, labels_fluxos, eh_fluxo
# app.py (trecho)
import streamlit as st
from utils_loader import load_model

@st.cache_resource
def bootstrap():
    return load_model()

model = bootstrap()


# ---------------- Session state inicial ----------------
# Estado inicial unificado
VALORES_INICIAIS = {
    # fluxo do aconselhamento
    "etapa": 1,
    "etapa_2": False,
    "etapa_3": False,
    "congelar_inputs": False,
    "sintomas_escolhidos": [],
    # fluxo dos autotestes
    "tentativa": 1,
    "resultados": [],
    "testando": False,
    "ready": False,
    "start_time": None,
}
for k, v in VALORES_INICIAIS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- Cabeçalho e avisos ----------------
st.title("Sistema Inteligente de Aconselhamento Médico")
st.markdown("**Atenção**: este sistema oferece aconselhamento inicial e não substitui atendimento médico.")
st.markdown("Leia o manual para entender todas as funcionalidades e utilizar melhor o sistema.")
st.markdown("---")

from pathlib import Path

# ---------------- Manual (toggle) ----------------
manual_aberto = st.toggle("Manual do sistema – clique para abrir/fechar", value=False)
if manual_aberto:
    manual_path = Path(__file__).resolve().parent / "src" / "textos" / "manual.md"
    try:
        st.markdown(manual_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        st.info(f"Manual não encontrado no caminho: {manual_path}")


# ===================== A PARTIR DAQUI, SUA INTERFACE EXISTENTE =====================
# Mantenha o restante do seu layout, formulários e fluxo de etapas aqui.
# Use as funções importadas acima (sem redefinir utilitários/dados/lógica no app).
#
# Exemplos de uso (se já tinha estes trechos, mantenha-os no lugar apropriado):
#
# with st.form("form_dados_iniciais"):
#     idade = st.number_input("Idade", 0, 120, step=1)
#     altura = st.number_input("Altura (m)", 0.5, 2.5, step=0.01)
#     peso = st.number_input("Peso (kg)", 10.0, 300.0, step=0.1)
#     gravida = st.selectbox("Está grávida?", ["Não", "Sim"])
#     condicoes = st.text_input("Condições pré-existentes (separadas por vírgula)")
#     enviado = st.form_submit_button("Salvar dados")
#
# if enviado:
#     imc = calcular_imc(altura, peso)
#     imc_class = classificar_imc(imc)
#     condicoes_brutas = [c.strip() for c in condicoes.split(",")] if condicoes else []
#     sistemas_afetados = gerar_sistemas_afetados_por_fatores(idade, imc_class, gravida, condicoes_brutas)
#     st.session_state["fatores_sistemas"] = sistemas_afetados
#     st.success(f"Sistemas afetados por fatores: {', '.join(sistemas_afetados) or 'Nenhum'}")
#
# Depois, siga com:
# - Seleção de sintomas (usando 'sistemas_sintomas' e/ou seu próprio UI),
# - Detalhamento por sintoma,
# - Cálculo de cores individuais e combinação (classificar_combinacao),
# - Ajuste conservador (calcular_ajuste_por_fatores_conservador),
# - Mensagens de saída.

# ==== IMPORTS DO PROJETO ====
# Dicionário de sintomas
from dicionario import dic
# Todos os renders dos autotestes
from src.ui.autotestes import *

st.set_page_config(page_title="Sistema de Triagem", layout="centered")

# --- ESTADO INICIAL (mínimo necessário) ---
st.session_state.setdefault("etapa", 1)

# ===== MENU LATERAL =====
# ===== MENU LATERAL (libera Autotestes só a partir da Etapa 2) =====
ETAPA_ATUAL = int(st.session_state.get("etapa", 1))

base_opcoes = ["Nenhuma", "Dicionário de sintomas"]
if ETAPA_ATUAL >= 2:
    base_opcoes.append("Autotestes para apuração de sintoma")

# preserva escolha válida; se usuário voltar da etapa 2 para 1, força "Nenhuma"
opcao_atual = st.session_state.get("sidebar_opcao", "Nenhuma")
if opcao_atual == "Autotestes para apuração de sintoma" and ETAPA_ATUAL < 2:
    opcao_atual = "Nenhuma"

opcao = st.sidebar.selectbox(
    "Escolha uma opção",
    base_opcoes,
    index=base_opcoes.index(opcao_atual) if opcao_atual in base_opcoes else 0,
    key="sidebar_opcao"
)

subteste = None

# Guardrail extra: se tentar burlar via estado, bloqueia aqui
if opcao == "Autotestes para apuração de sintoma" and ETAPA_ATUAL < 2:
    st.sidebar.warning("Autotestes são liberados apenas após concluir a Etapa 1.")
    opcao = "Nenhuma"

# ===== Catálogo de autotestes (somente nomes e agrupamentos) =====
sistemas_autotestes = {
    "🧠 Neurológico": [
        "Tempo de Reação",
        "Memória Curta",
        "Reflexo Seletivo",
        "Coordenação Fina",
        "Toque Rápido (10s)",
        "Equilíbrio",
        "Humor e Ansiedade",
        "Humor na última semana",
    ],
    "👁️ Sensorial": [
        "Visão",
        "Campo Visual",
        "Percepção de Cores",
        "Audição (Frequências Altas e Baixas)",
        "Audição (Detecção de Som)",
    ],
    "💓 Cardíaco": ["Cardíaco", "Recuperação Cardíaca", "Palpitações"],
    "🫁 Respiratório": ["Respiração", "Apneia Simples", "Sopro Sustentado", "Contagem em uma Respiração"],
    "🧬 Vascular / Circulatório": ["Enchimento Capilar", "Varizes"],
    "🦵 Musculoesquelético": ["Força da Mão", "Subir Escada com Uma Perna", "Levantar do Chão"],
    "🚽 Digestivo / Intestinal": ["Digestão", "Ritmo Intestinal"],
    "💧 Urinário e Hidratação": ["Urinário", "Hidratação", "Cor da Urina"],
    "🧴 Cutâneo": ["Pele e Coceira"],
    "☕ Energia e Vitalidade": ["Energia Matinal", "Variação de Peso (Últimos 30 Dias)"],
    "🩺 Testes de apuração de sintomas específicos": [
        # Alertas/neurológico/obstétrico
        "Icterícia Neonatal",
        # Respiratório/Circulatório
        "Diferenciar Falta de Ar e Dificuldade Respiratória",
        "Hipotensão",
        # Infecciosos/metabólicos/termo-regulação
        "Calafrios",
        "Hipoglicemia",
        "Hiperglicemia",
        # Neuro/sono/cognição
        "Perda de Memória",
        "Insônia",
        "Tremores ou movimentos involuntários",
        "Alterações na fala",
        # Olhos/pele/geral
        "Dor ou olho vermelho",
        "Alterações visuais súbitas",
        # Mama/testículo
        "Secreção Mamilar (fora da amamentação)",
        "Nódulo na Mama",
        "Nódulo Testicular",
        # Ginecológico
        "Menstruação Excessiva",
        "Ausência de Menstruação",
        # Digestivo
        # Check-list físico
        "Palpação de Linfonodos (Check-list)",
    ],
}

# ===== Router (nome -> função render_*) =====
router = {
    # Neurológico
    "Tempo de Reação": render_tempo_de_reacao,
    "Memória Curta": render_memoria_curta,
    "Reflexo Seletivo": render_reflexo_seletivo,
    "Coordenação Fina": render_coordenacao_fina,
    "Toque Rápido (10s)": render_toque_rapido_10s,
    "Equilíbrio": render_equilibrio,
    "Humor e Ansiedade": render_humor_ansiedade,
    "Humor na última semana": render_humor_ultima_semana,

    # Sensorial
    "Visão": render_visao_contraste,
    "Campo Visual": render_campo_visual,
    "Percepção de Cores": render_percepcao_cores,
    "Audição (Frequências Altas e Baixas)": render_audicao_frequencias,
    "Audição (Detecção de Som)": render_audicao_deteccao_de_som,

    # Cardíaco
    "Cardíaco": render_cardiaco,
    "Recuperação Cardíaca": render_recuperacao_cardiaca,
    "Palpitações": render_palpitacoes,

    # Respiratório
    "Respiração": render_respiracao,
    "Apneia Simples": render_apneia_simples,
    "Sopro Sustentado": render_sopro_sustentado,
    "Contagem em uma Respiração": render_contagem_em_uma_respiracao,

    # Vascular / Circulatório
    "Enchimento Capilar": render_enchimento_capilar,
    "Varizes": render_varizes,

    # Musculoesquelético
    "Força da Mão": render_forca_da_mao,
    "Subir Escada com Uma Perna": render_subir_escada_uma_perna,
    "Levantar do Chão": render_levantar_do_chao,

    # Digestivo / Intestinal
    "Digestão": render_digestao,
    "Ritmo Intestinal": render_ritmo_intestinal,

    # Urinário e Hidratação
    "Urinário": render_urinario,
    "Hidratação": render_hidratacao,
    "Cor da Urina": render_cor_da_urina,

    # Cutâneo
    "Pele e Coceira": render_pele_e_coceira,

    # Energia e Vitalidade
    "Energia Matinal": render_energia_matinal,
    "Variação de Peso (Últimos 30 Dias)": render_variacao_peso_30d,

    # Específicos
    "Icterícia Neonatal": render_ictericia_neonatal,

    "Diferenciar Falta de Ar e Dificuldade Respiratória": render_diferenciar_falta_de_ar,
    "Hipotensão": render_hipotensao,

    "Calafrios": render_calafrios,
    "Hipoglicemia": render_hipoglicemia,
    "Hiperglicemia": render_hiperglicemia,

    "Perda de Memória": render_perda_memoria,
    "Insônia": render_insonia,
    "Tremores ou movimentos involuntários": render_tremores,
    "Alterações na fala": render_alteracoes_fala,

    "Dor ou olho vermelho": render_dor_olho_vermelho,

    "Nódulo na Mama": render_nodulo_mama,
    "Nódulo Testicular": render_nodulo_testicular,
    "Secreção Mamilar (fora da amamentação)": render_secrecao_mamilar,


    "Menstruação Excessiva": render_menstruacao_excessiva,
    "Ausência de Menstruação": render_ausencia_menstruacao,

    "Dificuldade para engolir": render_dificuldade_engolir,
    "Diferenciação entre sangramento retal e gastrointestinal": render_diferenciar_sangramento_ret_gi,

    "Palpação de Linfonodos (Check-list)": render_linfonodos,
}

# ===== DICIONÁRIO DE SINTOMAS =====
if opcao == "Dicionário de sintomas":
    sintoma_selecionado = st.selectbox("Escolha um sintoma:", list(dic.keys()))
    st.subheader(f"🔎 {sintoma_selecionado}")
    st.markdown(f"**Definição Clínica:** {dic[sintoma_selecionado]['definicao']}")
    st.markdown(f"**Explicação Popular:** {dic[sintoma_selecionado]['popular']}")
    st.markdown(f"**Nome Clínico:** {dic[sintoma_selecionado]['clinico']}")
    st.markdown("**Variações do Sintoma:**")
    for subtitulo, explicacao in dic[sintoma_selecionado]["termos"].items():
        st.markdown(f"- **{subtitulo}:** {explicacao}")

# ===== AUTOTESTES (HUB) =====
elif opcao == "Autotestes para apuração de sintoma":
    st.title("📋 Autotestes para apuração de sintoma de Saúde")
    st.caption("Esses testes são apenas indicativos e não substituem avaliação médica.")

    sistema_escolhido = st.selectbox("🔍 Escolha o sistema:", list(sistemas_autotestes.keys()))
    subteste = st.radio("🧪 Escolha o teste específico:", sistemas_autotestes[sistema_escolhido])

    func = router.get(subteste)
    if func is None:
        st.error("Teste ainda não implementado. Me diga o nome que eu te mando o render_* correspondente.")
    else:
        func()
# app.py
import streamlit as st
from utils_loader import have_model, download_model, load_model

st.set_page_config(page_title="Classificação de Sintomas", layout="centered")
st.title("Classificação de Sintomas")

# Estado do modelo na sessão
if "model_ready" not in st.session_state:
    st.session_state.model_ready = have_model()

# Bloco para baixar o modelo (se necessário)
if not st.session_state.model_ready:
    st.warning("O modelo ainda não foi baixado no servidor.")
    if st.button("Baixar modelo agora"):
        with st.spinner("Baixando o modelo do Drive..."):
            try:
                download_model()
                st.session_state.model_ready = True
                st.success("Modelo baixado com sucesso!")
            except Exception as e:
                st.error(f"Falha ao baixar: {e}")

# Inputs
use_free_text = st.sidebar.checkbox("Usar texto livre", value=False)
free_text = st.sidebar.text_area("Descreva os sintomas", height=140) if use_free_text else ""
texto_principal = st.text_area("Entrada principal", height=140)

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("Analisar")
with col2:
    limpar = st.button("Limpar")

if limpar:
    st.session_state.model_ready = have_model()
    st.experimental_rerun()

def predict_labels_generic(model, texts, thr_default=0.35):
    if hasattr(model, "predict_labels"):
        return model.predict_labels(texts)
    try:
        proba = model.predict_proba(texts)
        classes_ = None
        if hasattr(model, "named_steps") and "clf" in model.named_steps:
            classes_ = getattr(model.named_steps["clf"], "classes_", None)
        if classes_ is None:
            classes_ = getattr(model, "classes_", None)
        if classes_ is None:
            raise AttributeError("Sem classes_")
        out = []
        for row in proba:
            picked = [classes_[i] for i, p in enumerate(row) if float(p) >= thr_default]
            out.append(picked)
        return out
    except Exception:
        pass
    y = model.predict(texts)
    classes_ = None
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        classes_ = getattr(model.named_steps["clf"], "classes_", None)
    if classes_ is None:
        classes_ = getattr(model, "classes_", None)
    if classes_ is None:
        return [y[0] if len(y)==1 else y]
    out = []
    for row in y:
        labels = [classes_[i] for i, v in enumerate(row) if v == 1]
        out.append(labels)
    return out

if analisar:
    entrada = free_text if use_free_text else texto_principal
    if not entrada.strip():
        st.warning("Digite algo para analisar.")
    else:
        if not st.session_state.model_ready:
            st.error("Baixe o modelo primeiro (botão acima).")
        else:
            try:
                model = load_model()
                labels = predict_labels_generic(model, [entrada])[0]
                if labels:
                    st.success("Sintomas detectados:")
                    st.write(", ".join(map(str, labels)))
                else:
                    st.info("Nenhum sintoma atingiu o limiar mínimo.")
            except Exception as e:
                st.error(f"Erro ao carregar/predizer: {e}")

# =============================
# ETAPA 1 – FORMULÁRIO INICIAL
# =============================
if st.session_state.etapa == 1:
    st.header("1. Formulário Inicial – Dados Clínicos")

    nome = st.text_input("Nome completo", key="nome_input", disabled=st.session_state.congelar_inputs)
    idade = st.number_input("Idade", 0, 120, step=1, key="idade_input", disabled=st.session_state.congelar_inputs)
    altura = st.number_input("Altura (em metros)", 0.5, 2.5, step=0.01, key="altura_input", disabled=st.session_state.congelar_inputs)
    peso = st.number_input("Peso (em kg)", 10.0, 300.0, step=0.1, key="peso_input", disabled=st.session_state.congelar_inputs)
    sexo = st.selectbox("Sexo biológico", ["", "Masculino", "Feminino", "Outro"], key="sexo_input", disabled=st.session_state.congelar_inputs)

    # Gravidez
    if sexo == "Feminino":
        gravidez_input = st.radio("Está grávida?", ["Sim", "Não"], key="gravidez_radio", disabled=st.session_state.congelar_inputs)
    else:
        gravidez_input = "Não"

    # Doenças pré-existentes
    doenca_preexistente = st.radio("Possui alguma doença pré-existente?", ["Sim", "Não"], key="doenca_radio", disabled=st.session_state.congelar_inputs)
    grupo_doenca = []

    if doenca_preexistente == "Sim":
        grupos_opcoes = sorted([
            "Autoimune", "Cardíaco", "Cutâneo", "Diabetes", "Endócrino",
            "Gastrointestinal", "Hematológico", "Hepático", "Infeccioso",
            "Mamário", "Musculoesquelético", "Neurológico", "Oftalmológico",
            "Otorrino", "Psiquiátrico", "Reprodutor masculino", "Respiratório", "Urinário"
        ])
        grupo_doenca = st.multiselect("A quais grupos a doença pertence?", grupos_opcoes, key="grupo_multiselect", disabled=st.session_state.congelar_inputs)

    # CONTINUAR
    if st.button("Continuar para os sintomas", key="continuar_sintomas_etapa1"):
        preenchido = all([
            nome.strip(), idade, altura, peso, sexo,
            (gravidez_input if sexo == "Feminino" else True),
            (doenca_preexistente == "Não" or grupo_doenca)
        ])

        if preenchido:
            st.session_state["nome"] = nome
            st.session_state["idade"] = idade
            st.session_state["altura"] = altura
            st.session_state["peso"] = peso
            st.session_state["sexo"] = sexo
            st.session_state["gravida"] = gravidez_input
            st.session_state["imc"] = calcular_imc(altura, peso)
            st.session_state["classificacao_imc"] = classificar_imc(st.session_state["imc"])
            st.session_state["grupos_risco_refinados"] = grupo_doenca
            st.session_state["etapa"] = 2
            st.session_state["congelar_inputs"] = True
            st.rerun()
        else:
            st.warning("Preencha todos os campos obrigatórios antes de continuar.")

# =============================
# ETAPA 2 – ESCOLHA DOS SINTOMAS
# =============================
elif st.session_state.etapa == 2:
    st.header("2. Selecione até 3 sintomas principais")


    sintomas_disponiveis = sorted(set(labels_fluxos() or []))

    if "sintomas_temp" not in st.session_state:
        st.session_state["sintomas_temp"] = ["", "", ""]

    sintomas_temp = st.session_state.sintomas_temp

    for i in range(3):
        col1, col2 = st.columns([4, 1])

        with col1:
            outros = [s for s in sintomas_disponiveis if s not in sintomas_temp or s == sintomas_temp[i]]
            sintoma = st.selectbox(
                f"Sintoma {i+1}",
                [""] + sorted(outros),
                index=([""] + sorted(outros)).index(sintomas_temp[i]) if sintomas_temp[i] in outros else 0,
                key=f"sintoma_{i}"
            )
            sintomas_temp[i] = sintoma

        with col2:
            if sintoma and sintoma in dic:
                info = dic[sintoma]
                with st.expander(f"ℹ️ Ajuda para: {sintoma}", expanded=True):
                    st.markdown(f"**📖 Definição Clínica:** {info['definicao']}")
                    st.markdown(f"**🗣️ Explicação Popular:** {info['popular']}")
                    st.markdown("**🧠 Termos usados na triagem:**")
                    for termo, explicacao in info["termos"].items():
                        st.markdown(f"- **{termo}**: {explicacao}")

    sintomas_validos = [s for s in sintomas_temp if s]
    if sintomas_validos:
        if st.button("Avançar para detalhamento", key="avancar_etapa_3"):
            st.session_state["sintomas_escolhidos"] = sintomas_validos
            st.session_state["sintomas_temp"] = sintomas_temp
            st.session_state["etapa"] = 3
            st.session_state["etapa_3"] = True
            st.rerun()
    else:
        st.warning("Escolha pelo menos um sintoma para continuar.")
        
# =============================
# ETAPA 3 – DETALHAMENTO DOS SINTOMAS
# =============================
elif st.session_state.etapa == 3 and st.session_state.get("etapa_3"):
    st.header("3. Detalhe os sintomas escolhidos")

    # Estados seguros
    if "respostas_usuario" not in st.session_state:
        st.session_state["respostas_usuario"] = {}
    if "fluxo_respostas" not in st.session_state:
        st.session_state["fluxo_respostas"] = {}
    if "sintomas_escolhidos" not in st.session_state:
        st.session_state["sintomas_escolhidos"] = []

    # Usamos um FORM: nada calcula/mostra até clicar "Ver resultado"
    with st.form("form_detalhamento"):
        # Renderização de perguntas por sintoma
        for sintoma in st.session_state["sintomas_escolhidos"]:
            st.markdown(f"### {sintoma}")
            if eh_fluxo(sintoma):
                chave = normalizar(sintoma)
                if chave not in st.session_state["fluxo_respostas"]:
                    st.session_state["fluxo_respostas"][chave] = {}
                coletar_respostas_fluxo(sintoma)
            else:
                st.caption("Sem fluxo específico — será classificado por regra geral.")

        enviado = st.form_submit_button("Ver resultado")

    # Só processa e exibe resultados SE o botão foi clicado
    if enviado:
        st.markdown("---")

        import re  # para quebrar texto em bullets

        # ===== helpers visuais =====
        def tag_cor(cor_txt: str) -> str:
            cores = {"vermelho":"#d9342b","laranja":"#f08c00","amarelo":"#e0c200","verde":"#2f9e44"}
            hexa = cores.get(str(cor_txt).lower(), "#6c757d")
            return f"""
            <span style="
                display:inline-block;padding:.2rem .6rem;border-radius:999px;
                background:{hexa}1A;color:{hexa};font-weight:600;
                border:1px solid {hexa}40;font-size:.9rem">
                {cor_txt.upper()}
            </span>
            """

        def card_inicio(titulo: str, cor_txt: str):
            st.markdown(
                f"""
                <div style="border:1px solid #e9ecef;border-radius:12px;padding:14px;margin:8px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <h4 style="margin:0;font-weight:700">{titulo}</h4>
                    {tag_cor(cor_txt)}
                  </div>
                """,
                unsafe_allow_html=True
            )

        def card_fim():
            st.markdown("</div>", unsafe_allow_html=True)

        def justificativas_do_fluxo(nome_sintoma: str, respostas_fluxo: dict) -> list[str]:
            chave = normalizar(nome_sintoma)
            fluxo = FLUXOS.get(chave, {})
            itens = []
            try:
                for regra in fluxo.get("regras_excecao", []):
                    cond = regra.get("se", {})
                    disparou, partes = True, []
                    for k, v in cond.items():
                        resp_user = respostas_fluxo.get(k)
                        if isinstance(v, list):
                            if not isinstance(resp_user, list) or not all(x in (resp_user or []) for x in v):
                                disparou = False; break
                            partes.extend(v)
                        else:
                            if resp_user != v:
                                disparou = False; break
                            partes.append(v)
                    if disparou and partes:
                        itens.append("Regra de exceção acionada: " + "; ".join(partes))
            except Exception:
                pass

            try:
                for pergunta in fluxo.get("perguntas", []):
                    pid = pergunta.get("id")
                    plabel = pergunta.get("label", "").strip()
                    resp = respostas_fluxo.get(pid)
                    if resp is None: continue
                    if isinstance(resp, list):
                        if resp: itens.append(f"{plabel}: " + ", ".join(resp))
                    else:
                        itens.append(f"{plabel}: {resp}")
                    if len(itens) >= 4: break
            except Exception:
                pass

            return itens[:4] or ["Resultado baseado nas respostas do fluxograma."]

        # ===== processamento por sintoma =====
        cores_geradas = []
        for sintoma in st.session_state["sintomas_escolhidos"]:
            if eh_fluxo(sintoma):
                chave = normalizar(sintoma)
                if chave not in st.session_state["fluxo_respostas"]:
                    st.session_state["fluxo_respostas"][chave] = {}
                cor, _ = pontuar_fluxo(sintoma, st.session_state["fluxo_respostas"][chave])
                cores_geradas.append(cor)

                card_inicio(sintoma, cor)
                st.markdown("**Justificativa para a cor**")
                for b in justificativas_do_fluxo(sintoma, st.session_state["fluxo_respostas"][chave]):
                    st.markdown(f"- {b}")
                card_fim()
            else:
                cor = "amarelo"  # fallback
                cores_geradas.append(cor)
                card_inicio(sintoma, cor)
                st.markdown("**Justificativa para a cor**")
                st.markdown("- Resultado baseado na seleção do sintoma.")
                card_fim()

        st.markdown("---")

        # ===== cor final combinada =====
        cor_final = classificar_combinacao(cores_geradas)
        

        # --- ajuste conservador (idade/gravidez etc.) ---
        gravidez = str(st.session_state.get("gravida", "")).strip().lower() in ["sim", "true", "1"]
        idade_paciente = st.session_state.get("idade")
        ajuste_niveis = calcular_ajuste_por_fatores_conservador(
            sintomas_escolhidos=st.session_state["sintomas_escolhidos"],
            cores_individuais=cores_geradas,
            idade=idade_paciente,
            gravida=gravidez
)
        if ajuste_niveis >= 1:
            cor_final = aumentar_cor_em_1_nivel(cor_final)

        # ===== card final =====
        st.markdown("## Resultado preliminar")
        card_inicio("Gravidade estimada", cor_final)
        st.markdown("**O que fazer agora**")
        if cor_final == "vermelho":
            st.markdown("- Procure atendimento imediato.")
        elif cor_final == "laranja":
            st.markdown("- Procure avaliação rápida em unidade de saúde.")
        elif cor_final == "amarelo":
            st.markdown("- Requer atenção, mas pode aguardar avaliação não imediata.")
        else:
            st.markdown("- Observação dos sintomas e medidas simples em casa.")
        card_fim()

        st.markdown("---")
        st.subheader("Legenda de Gravidade")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"{tag_cor('VERDE')} &nbsp; Baixa gravidade", unsafe_allow_html=True)
            st.markdown(f"{tag_cor('AMARELO')} &nbsp; Moderada, atenção", unsafe_allow_html=True)
        with col2:
            st.markdown(f"{tag_cor('LARANJA')} &nbsp; Urgente", unsafe_allow_html=True)
            st.markdown(f"{tag_cor('VERMELHO')} &nbsp; Emergência", unsafe_allow_html=True)
