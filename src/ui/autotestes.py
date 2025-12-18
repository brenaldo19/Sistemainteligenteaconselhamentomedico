# autotestes.py
import time
import random
import streamlit as st

# ========== 1) TEMPO DE REAÇÃO ==========
def render_tempo_de_reacao():
    import streamlit as st
    import time
    import random

    st.subheader("🧠 Teste de Tempo de Reação")
    st.warning("⚠️ A primeira tentativa é apenas um treino e **não será contabilizada** na média final.")

    # ---- Sessão inicial: informações do usuário ----
    if "sexo" not in st.session_state:
        st.session_state.sexo = st.radio("Selecione seu sexo:", ["Masculino", "Feminino", "Outro"])
    
    if "idade" not in st.session_state:
        st.session_state.idade = st.number_input("Idade:", min_value=1, max_value=120, value=30)
    
    if "massa" not in st.session_state:
        st.session_state.massa = st.number_input("Massa (kg):", min_value=10.0, max_value=300.0, value=70.0)
    
    if "altura" not in st.session_state:
        st.session_state.altura = st.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=1.70)
    
    # Calcula IMC automaticamente
    st.session_state.imc = st.session_state.massa / (st.session_state.altura ** 2)

    # Pergunta gravidez só se for sexo feminino
    if st.session_state.sexo == "Feminino" and "gravida" not in st.session_state:
        st.session_state.gravida = st.radio("Está grávida?", ["Não", "Sim"])

    # ---- Estados do teste ----
    st.session_state.setdefault("tentativa", 1)        # 1 = treino; 2..8 = válidas
    st.session_state.setdefault("resultados", [])      # guarda 7 tempos válidos
    st.session_state.setdefault("testando", False)     # está no ciclo do teste?
    st.session_state.setdefault("ready", False)        # já liberou o clique?
    st.session_state.setdefault("start_time", None)    # início do tempo de reação
    st.session_state.setdefault("delay", None)         # atraso aleatório antes do clique

    CORRECAO_SISTEMA = 0.47

    # ---- Fluxo principal do teste ----
    if st.session_state.tentativa <= 8:
        if not st.session_state.testando:
            st.session_state.delay = random.uniform(3, 7)
            st.session_state.ready = False
            st.session_state.testando = True
            st.rerun()
        elif st.session_state.testando and not st.session_state.ready:
            time.sleep(st.session_state.delay)
            st.session_state.start_time = time.time()
            st.session_state.ready = True
            st.rerun()
        else:
            st.success("✅ Clique agora!")
            # Input para "Enter" como clique
            enter = st.text_input("Pressione Enter e envie para registrar o tempo:", "")
            if enter == "":
                fim = time.time()
                bruto = fim - (st.session_state.start_time or fim)
                tempo_reacao = max(0.01, bruto - CORRECAO_SISTEMA)
                if st.session_state.tentativa != 1:
                    st.session_state.resultados.append(tempo_reacao)
                st.session_state.tentativa += 1
                st.session_state.testando = False
                st.session_state.ready = False
                st.session_state.start_time = None
                st.rerun()

        if st.session_state.tentativa == 1:
            st.caption("🎯 Tentativa de treino")
        else:
            feitas = len(st.session_state.resultados)
            st.caption(f"📌 Tentativas válidas registradas: {feitas}/7")

        if st.button("🔁 Recomeçar teste de reação"):
            for k in ["tentativa", "resultados", "testando", "ready", "start_time", "delay"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    else:
        # ---- Resultados finais ----
        st.subheader("⏱️ Resultados")
        for i, r in enumerate(st.session_state.resultados, start=2):
            st.write(f"Tentativa {i}: ⏱️ {r:.2f} s")

        media = sum(st.session_state.resultados) / len(st.session_state.resultados) if st.session_state.resultados else 0.0

        # Ajustes por idade, IMC, gravidez e riscos
        idade = st.session_state.idade
        imc = st.session_state.imc
        sexo = st.session_state.sexo
        gravidez = st.session_state.get("gravida", False)
        riscos = st.session_state.get("grupos_risco_refinados", [])

        base = 0.225  # média ajustada para tempo real

        if idade <= 7:
            base += 0.02
        elif idade <= 16:
            base += 0.01
        elif idade <= 35:
            base += 0.0
        elif idade <= 58:
            base += 0.02
        else:
            base += 0.03

        if imc < 16:
            base += 0.01
        elif imc >= 30:
            base += 0.01

        if str(gravidez).lower() in ["sim", "true", "1"]:
            base += 0.02

        if "neurológica" in riscos or "psiquiátrica" in riscos:
            base += 0.02
        if "cardíaca" in riscos:
            base += 0.01
        if "respiratória" in riscos:
            base += 0.01

        lim_inferior = base * 0.75
        lim_superior = base * 1.25

        st.markdown("---")
        st.subheader(f"🏁 Média final: **{media:.3f} s**")

        if media < lim_inferior:
            st.success("⚡ Seu tempo está **acima do esperado**. Excelente reflexo!")
        elif media > lim_superior:
            st.warning("🐢 Seu tempo está **abaixo do esperado**. Considere repetir o teste mais tarde.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Hipoglicemia, Hipotensão/colapso, Formigamento ou perda de força**")
        else:
            st.info("✅ Seu tempo está **dentro do esperado**.")

        if st.button("🔁 Refazer o teste"):
            for k in ["tentativa", "resultados", "testando", "ready", "start_time", "delay"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

# ========== 2) CALAFrIOS ==========
def render_calafrios():
    st.subheader("🥶 Teste de Calafrios (Temperatura + Contexto)")
    st.markdown("Informe a **temperatura máxima** e marque os **sinais associados**.")

    temp = st.number_input("Temperatura máxima (°C) nas últimas 24–48h", 34.0, 43.0, step=0.1, format="%.1f")
    repeticoes = st.selectbox("Frequência hoje", ["Nenhum", "Uma vez", "Várias vezes ao dia"])
    confusao = st.checkbox("Confusão/desorientação")
    hipotensao = st.checkbox("Pressão baixa/tontura ao levantar")
    urinaria = st.checkbox("Dor ao urinar / urina turva")
    tosse = st.checkbox("Tosse com catarro/dor no peito")
    ferida = st.checkbox("Ferida com vermelhidão/calor/saída de pus")
    viagem = st.checkbox("Calafrios após viagem endêmica")

    risco = 0
    if temp >= 39.0: risco += 2
    elif 38.0 <= temp < 39.0: risco += 1
    if repeticoes == "Várias vezes ao dia": risco += 1
    if confusao: risco += 2
    if hipotensao: risco += 1
    if urinaria: risco += 1
    if tosse: risco += 1
    if ferida: risco += 1
    if viagem: risco += 1

    if risco >= 4:
        st.error("🚨 Calafrios com sinais de alerta.")
        st.markdown("🔎 Relacionados: **Calafrios, Febre, Confusão mental, Alterações urinárias, Tosse, Infecção em ferida**")
    elif risco >= 2:
        st.warning("⚠️ Calafrios com possível foco associado.")
        st.markdown("🔎 Relacionados: **Calafrios, Febre, Alterações urinárias**")
    else:
        st.success("✅ Sem sinais relevantes além de calafrios isolados.")



# ========== 4) INSÔNIA ==========
def render_insonia():
    st.subheader("😵‍💫 Insônia (Duração + Impacto)")
    duracao = st.selectbox("Duração", ["< 1 semana", "1–4 semanas", "> 1 mês"])
    impacto = st.selectbox("Impacto no dia a dia", ["Leve", "Moderado", "Incapaz de trabalhar/estudar/dirigir"])
    ideacao = st.checkbox("Ideação suicida")
    mania = st.checkbox("Humor elevado/energia excessiva (mania)")
    ansiedade = st.checkbox("Ansiedade intensa/pânico")
    apneia = st.checkbox("Suspeita de apneia (ronco/pausas)")
    dor_cronica = st.checkbox("Dor crônica")
    estimulantes = st.checkbox("Uso de estimulantes (cafeína/anfetaminas)")

    risco = 0
    if duracao == "> 1 mês": risco += 1
    if impacto == "Moderado": risco += 1
    if impacto == "Incapaz de trabalhar/estudar/dirigir": risco += 2
    if ideacao: risco += 3
    if mania: risco += 1
    if ansiedade: risco += 1
    if apneia: risco += 1
    if dor_cronica: risco += 1

    if risco >= 4:
        st.error("🚨 Insônia com alto impacto/sinais importantes.")
        st.markdown("🔎 Relacionados: **Insônia, Ansiedade**")
    elif risco >= 2:
        st.warning("⚠️ Insônia relevante com alguns fatores associados.")
        st.markdown("🔎 Relacionados: **Insônia, Ansiedade**")
    else:
        st.success("✅ Insônia leve/recente sem sinais de alerta.")


# ========== 5) HIPOGLICEMIA ==========
def render_hipoglicemia():
    st.subheader("🧪 Hipoglicemia (Sintomas + Contexto)")
    desmaio_confusao_suor = st.checkbox("Desmaio/confusão com sudorese intensa")
    tremor_fome = st.checkbox("Tontura/tremores e fome súbita")
    jejum = st.checkbox("Jejum prolongado")
    exercicio = st.checkbox("Atividade física intensa sem alimentação")

    risco = 0
    if desmaio_confusao_suor: risco += 3
    if tremor_fome: risco += 2
    if jejum: risco += 1
    if exercicio: risco += 1

    if risco >= 4:
        st.error("🚨 Compatível com hipoglicemia significativa.")
        st.markdown("🔎 Relacionados: **Hipoglicemia, Desmaio/tontura, Confusão**")
    elif risco >= 2:
        st.warning("⚠️ Sugestivo de hipoglicemia leve/moderada.")
        st.markdown("🔎 Relacionados: **Hipoglicemia, Desmaio/tontura**")
    else:
        st.success("✅ Sem combinação forte para hipoglicemia.")


# ========== 6) HIPERGLICEMIA ==========
def render_hiperglicemia():
    st.subheader("🧪 Hiperglicemia (Sede/Urina + Sinais)")
    sede_noite = st.checkbox("Muita sede e urinar em excesso (inclusive à noite)")
    leve_freq = st.checkbox("Leve aumento da frequência urinária")
    perda_peso = st.checkbox("Perda de peso rápida (ou não intencional)")
    nausea_dor = st.checkbox("Náusea/vômito e/ou dor abdominal")
    carbos = st.checkbox("Excesso de carboidratos recentemente")

    risco = 0
    if sede_noite: risco += 2
    if leve_freq: risco += 1
    if perda_peso: risco += 1
    if nausea_dor: risco += 2
    if carbos: risco += 1

    if risco >= 4:
        st.error("🚨 Compatível com hiperglicemia importante.")
        st.markdown("🔎 Relacionados: **Hiperglicemia, Náusea/Enjoo, Perda de peso**")
    elif risco >= 2:
        st.warning("⚠️ Sinais sugestivos de hiperglicemia.")
        st.markdown("🔎 Relacionados: **Hiperglicemia, Náusea/Enjoo**")
    else:
        st.success("✅ Sem combinação forte para hiperglicemia.")


# ========== 7) MEMÓRIA CURTA ==========
def render_memoria_curta():
    st.subheader("🧠 Memória Curta")
    # estados
    st.session_state.setdefault("mc_palavras", None)
    st.session_state.setdefault("mc_mostrar", True)

    if st.session_state.mc_palavras is None:
        todas = ["abacate","ônibus","papel","relógio","vela","caneta","tigre","janela","maçã","boneco"]
        st.session_state.mc_palavras = random.sample(todas, 5)
        st.session_state.mc_mostrar = True

    if st.session_state.mc_mostrar:
        st.info("Memorize as palavras abaixo — você terá 8 segundos.")
        st.write(" | ".join(st.session_state.mc_palavras))
        time.sleep(8)
        st.session_state.mc_mostrar = False
        st.rerun()
    else:
        resposta = st.text_input("Digite as palavras separadas por vírgula:")
        if st.button("Ver resultado"):
            digitadas = [p.strip().lower() for p in resposta.split(",") if p.strip()]
            corretas = [p for p in digitadas if p in st.session_state.mc_palavras]
            st.success(f"Lembrou {len(corretas)} palavra(s). Corretas: {', '.join(corretas) or '—'}")
            st.info("5: excelente. 4: ok. 0–3: atenção à memória recente.")
            st.markdown("🔎 Relacionados: **Confusão mental, Comportamento estranho**")
        if st.button("Refazer"):
            for k in ["mc_palavras","mc_mostrar"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()


# ========== 8) ALTERAÇÕES NA FALA ==========
def render_alteracoes_fala():
    st.subheader("🗣️ Alterações na Fala")
    st.markdown("Leia uma frase conhecida 2x e avalie clareza/articulação.")
    resp = st.radio("Houve alteração na fala?", ["Não", "Sim, leve", "Sim, acentuada"], index=0)
    if resp == "Sim, acentuada":
        st.error("🚨 Pode indicar evento neurológico agudo. Procure atendimento.")
        st.markdown("🔎 Base: **Alterações na fala**")
    elif resp == "Sim, leve":
        st.warning("⚠️ Pequena alteração. Se persistir ou piorar, avalie.")
        st.markdown("🔎 Base: **Alterações na fala**")
    else:
        st.success("✅ Sem alteração relevante.")


# ========== 9) ALTERAÇÕES VISUAIS SÚBITAS ==========
def render_alteracoes_visuais_subitas():
    st.subheader("👁️ Alterações Visuais Súbitas")
    st.markdown("Cubra um olho, depois o outro; compare nitidez/cores/campo.")
    resp = st.radio("Perda/alteração súbita?", ["Não", "Parcial", "Total"], index=0)
    if resp == "Total":
        st.error("🚨 Perda total súbita. Procure atendimento imediatamente.")
        st.markdown("🔎 Base: **Alterações visuais súbitas**")
    elif resp == "Parcial":
        st.warning("⚠️ Alteração parcial. Requer avaliação.")
        st.markdown("🔎 Base: **Alterações visuais súbitas**")
    else:
        st.success("✅ Sem alteração relevante.")


# ========== 10) TREMores / MOVIMENTOS INVOLUNTÁRIOS ==========
def render_tremores():
    st.subheader("🤲 Tremores ou Movimentos Involuntários")
    st.markdown("Braços estendidos 20s; observe tremor. Segure um copo com água.")
    resp = st.radio("Percebeu tremores?", ["Não", "Sim, leves", "Sim, intensos"], index=0)
    if resp == "Sim, intensos":
        st.error("🚨 Tremores intensos. Procure avaliação.")
        st.markdown("🔎 Base: **Tremores/movimentos involuntários**")
    elif resp == "Sim, leves":
        st.warning("⚠️ Tremores leves. Acompanhe.")
        st.markdown("🔎 Base: **Tremores/movimentos involuntários**")
    else:
        st.success("✅ Sem tremores.")


# ========== 11) DIFICULDADE PARA ENGOLIR ==========
def render_dificuldade_engolir():
    st.subheader("🥛 Dificuldade para Engolir (Deglutição)")
    st.markdown("Tome água sentado; depois alimento macio. Avalie dor/bloqueio/engasgo.")
    resp = st.radio("Dor, bloqueio ou engasgo ao engolir?", ["Não", "Sim, leve", "Sim, acentuado"], index=0)
    if resp == "Sim, acentuado":
        st.error("🚨 Dificuldade acentuada. Procure atendimento.")
        st.markdown("🔎 Base: **Dificuldade para engolir**")
    elif resp == "Sim, leve":
        st.warning("⚠️ Pequena dificuldade. Acompanhe.")
        st.markdown("🔎 Base: **Dificuldade para engolir**")
    else:
        st.success("✅ Deglutição normal.")


# ========== 12) DOR OU OLHO VERMELHO ==========
def render_dor_olho_vermelho():
    st.subheader("👁️ Dor ou Olho Vermelho")
    st.markdown("Observe vermelhidão, inchaço, secreção; dor/ardência/corpo estranho.")
    resp = st.radio("Há dor ou vermelhidão nos olhos?", ["Não", "Sim, leve", "Sim, acentuada"], index=0)
    if resp == "Sim, acentuada":
        st.error("🚨 Dor intensa/vermelhidão importante. Procure atendimento.")
        st.markdown("🔎 Base: **Dor ou olho vermelho**")
    elif resp == "Sim, leve":
        st.warning("⚠️ Sinais leves. Higiene ocular e observação.")
        st.markdown("🔎 Base: **Dor ou olho vermelho**")
    else:
        st.success("✅ Sem sinal preocupante.")


# ========== 13) HIPOTENSÃO ==========
def render_hipotensao():
    st.subheader("📉 Pressão Baixa (Hipotensão)")
    st.markdown("Sente-se; levante devagar; avalie tontura/visão turva/fraqueza.")
    resp = st.radio("Sinais de hipotensão?", ["Não", "Sim, leves", "Sim, acentuados"], index=0)
    if resp == "Sim, acentuados":
        st.error("🚨 Queda de pressão significativa. Procure atendimento.")
        st.markdown("🔎 Base: **Hipotensão**")
    elif resp == "Sim, leves":
        st.warning("⚠️ Sinais leves. Hidrate-se e descanse.")
        st.markdown("🔎 Base: **Hipotensão**")
    else:
        st.success("✅ Sem sinais de hipotensão.")


# ========== 14) RESPIRAÇÃO (FR) ==========
def render_respiracao():
    st.subheader("🌬️ Frequência Respiratória")
    st.markdown("Conte respirações por 30s e informe o número.")
    st.session_state.setdefault("fr_contando", False)
    st.session_state.setdefault("fr_valor", None)

    if not st.session_state.fr_contando:
        if st.button("Iniciar 30s"):
            st.session_state.fr_contando = True
            st.rerun()
    else:
        st.info("⏳ Conte suas respirações por 30 segundos…")
        time.sleep(30)
        st.session_state.fr_contando = False
        st.rerun()

    if not st.session_state.fr_contando and st.session_state.fr_valor is None:
        resp = st.number_input("Respirações em 30s", 0, 50, step=1)
        if st.button("Ver resultado"):
            st.session_state.fr_valor = resp * 2
            st.rerun()

    if st.session_state.fr_valor is not None:
        freq = st.session_state.fr_valor
        idade = st.session_state.get("idade", 30)
        if idade < 12:
            normal = (18, 30); faixa = "crianças"
        elif idade < 60:
            normal = (12, 20); faixa = "adultos"
        else:
            normal = (12, 22); faixa = "idosos"

        st.subheader(f"📈 FR: **{freq} rpm** (faixa esperada {normal[0]}–{normal[1]} em {faixa})")
        if freq < normal[0]:
            st.warning("📉 Abaixo do esperado (bradipneia).")
            st.markdown("🔎 Relacionados: **Dificuldade respiratória, Falta de ar, Confusão, Hipotensão, Tontura**")
        elif freq <= normal[1]:
            st.success("✅ Dentro do esperado.")
        else:
            st.warning("📈 Acima do esperado (taquipneia).")
            st.markdown("🔎 Relacionados: **Dificuldade respiratória, Falta de ar, Ansiedade, Dor no peito, Febre**")

        if st.button("Refazer (Respiração)"):
            for k in ["fr_contando","fr_valor"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()


# ========== DIFERENCIAR FALTA DE AR x DIFICULDADE RESPIRATÓRIA ==========
def render_diferenciar_falta_de_ar():
    st.subheader("🌬️ Diferenciar Falta de Ar vs Dificuldade Respiratória")
    inicio_subito = st.radio("Início súbito (segundos/minutos)?", ["Não","Sim"], index=0, horizontal=True)
    fala_frases = st.radio("Consegue falar frases completas?", ["Sim","Não"], index=0, horizontal=True)
    posicao_alivia = st.radio("Mudar de posição alivia?", ["Não","Sim"], index=0, horizontal=True)
    chiado_estridor = st.radio("Chiado/estridor alto ao respirar?", ["Não","Sim"], index=0, horizontal=True)
    esforco_visivel = st.radio("Esforço visível para respirar?", ["Não","Sim"], index=0, horizontal=True)

    if st.button("Analisar"):
        score = 0
        if fala_frases == "Não": score += 2
        if chiado_estridor == "Sim": score += 2
        if esforco_visivel == "Sim": score += 2
        if inicio_subito == "Sim": score += 1

        if score >= 4:
            st.error("🚨 Indícios fortes de **dificuldade respiratória**.")
            st.markdown("🔎 Relacionados: **obstrução/comprometimento pulmonar**")
        elif score >= 2:
            st.warning("⚠️ Indícios mistos de dificuldade respiratória.")
        else:
            st.success("✅ Mais compatível com **falta de ar subjetiva**.")


# ========== VISÃO (CONTRASTE) ==========
def render_visao_contraste():
    st.subheader("👁️ Teste Visual com Dificuldade Progressiva")
    st.session_state.setdefault("vis_numeros", None)
    st.session_state.setdefault("vis_contrastes", None)

    if st.session_state.vis_numeros is None:
        todos = random.sample(range(10, 99), 5)
        st.session_state.vis_numeros = [str(n) for n in todos]
        st.session_state.vis_contrastes = ["#000000","#666666","#999999","#BBBBBB","#DDDDDD"]

    html = "<div style='font-size:16px; letter-spacing:12px;'>"
    for num, cor in zip(st.session_state.vis_numeros, st.session_state.vis_contrastes):
        html += f"<span style='color:{cor}'>{num}</span>  "
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    resposta = st.text_input("Quais números você viu? (separe por espaço)").strip()
    if st.button("Verificar"):
        usuario = resposta.split() if resposta else []
        corretos = [n for n in usuario if n in st.session_state.vis_numeros]
        st.success(f"Acertou {len(corretos)} número(s): {', '.join(corretos) or '—'}")
        if len(corretos) == 5:
            st.info("✅ Visão excelente no baixo contraste.")
        elif len(corretos) >= 4:
            st.warning("⚠️ Leve dificuldade em baixo contraste.")
        else:
            st.error("🚨 Dificuldade significativa. Considere avaliar com oftalmologista.")
    if st.button("Refazer (Visão)"):
        for k in ["vis_numeros","vis_contrastes"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()


# ========== CAMPO VISUAL ==========
def render_campo_visual():
    st.subheader("👁️ Campo Visual – Dedos Laterais")
    st.markdown("Fique de frente para um espelho e estique os braços para as laterais,observe seu rosto,e fique mexendo os dedos")
    campo = st.radio("Percebeu movimento com dedos bem laterais?", ["Sim, com os dois olhos","Apenas com um olho","Com dificuldade"], index=0)
    if st.button("Ver resultado"):
        if campo == "Sim, com os dois olhos":
            st.success("✅ Campo periférico preservado.")
        elif campo == "Apenas com um olho":
            st.warning("⚠️ Diferença entre os olhos. Investigar.")
        else:
            st.error("🚨 Campo visual comprometido. Avaliação oftalmológica indicada.")


# ========== PERCEPÇÃO DE CORES ==========
def render_percepcao_cores():
    st.subheader("🌈 Percepção de Cores")
    html = """
    <div style='display:flex;gap:20px;font-size:14px;'>
        <div style='background-color:red;width:50px;height:50px;'></div>
        <div style='background-color:green;width:50px;height:50px;'></div>
        <div style='background-color:blue;width:50px;height:50px;'></div>
        <div style='background-color:#E6B800;width:50px;height:50px;'></div>
        <div style='background-color:#00CED1;width:50px;height:50px;'></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    resp = st.text_input("Digite as cores que enxerga (separe por vírgulas):").lower()
    if st.button("Ver resultado"):
        corretas = ["vermelho","verde","azul","amarelo","azul"]
        entrada = [c.strip() for c in resp.split(",") if c.strip()]
        acertos = [c for c in entrada if c in corretas]
        st.success(f"Acertou {len(acertos)}: {', '.join(acertos) or '—'}")
        if len(acertos) == 5:
            st.info("✅ Percepção aparentemente normal.")
        elif len(acertos) >= 3:
            st.warning("⚠️ Dificuldade com alguns tons.")
        else:
            st.error("🚨 Dificuldade significativa — possível daltonismo. Investigar.")




# ========== CARDÍACO (PÓS-ESFORÇO) ==========
def render_cardiaco():
    st.subheader("❤️ Frequência Cardíaca pós-esforço")
    st.markdown("Sente-se em uma cadeira,depois mantenha um ritmo constante de sentar e levantar,depois que terminar,responda as perguntas")
    st.session_state.setdefault("c_etapa", 0)
    st.session_state.setdefault("c_bpm15", None)
    st.session_state.setdefault("c_fc", None)

    if st.session_state.c_etapa == 0:
        if st.button("Iniciar esforço (1 min senta-levanta)"):
            st.session_state.c_etapa = 1; st.rerun()
    elif st.session_state.c_etapa == 1:
        st.info("⏳ Faça 1 minuto de senta-levanta.")
        time.sleep(60); st.session_state.c_etapa = 2; st.rerun()
    elif st.session_state.c_etapa == 2:
        st.success("✅ Termine e sente-se. Prepare contagem de 15s.")
        if st.button("Iniciar 15s"): st.session_state.c_etapa = 3; st.rerun()
    elif st.session_state.c_etapa == 3:
        st.info("⏳ Conte batimentos por 15s…")
        time.sleep(15); st.session_state.c_etapa = 4; st.rerun()
    elif st.session_state.c_etapa == 4:
        bat = st.number_input("Batimentos em 15s:", 0, 100, step=1)
        if st.button("Ver resultado"):
            st.session_state.c_bpm15 = bat
            st.session_state.c_fc = bat * 4
            st.session_state.c_etapa = 5
            st.rerun()
    elif st.session_state.c_etapa == 5:
        fc = st.session_state.c_fc
        idade = st.session_state.get("idade", 30)
        imc = st.session_state.get("imc", 22)
        riscos = st.session_state.get("grupos_risco_refinados", [])
        obeso = imc >= 30
        risco_card = "cardíaca" in riscos
        lim = 110 if idade < 12 else (100 if idade <= 39 else (105 if idade <= 59 else 110))
        if obeso: lim -= 3
        if risco_card: lim -= 5

        st.subheader(f"📈 FC estimada: **{fc} bpm** (limite esperado {lim})")
        if fc < 60:
            st.warning("📉 Bradicardia/boa adaptação (avaliar com sintomas).")
        elif fc <= lim:
            st.success("✅ Dentro do esperado após esforço leve.")
        elif fc <= lim + 10:
            st.warning("⚠️ Leve taquicardia.")
        else:
            st.error("🚨 Muito acima do esperado.")
        if st.button("Refazer (Cardíaco)"):
            for k in ["c_etapa","c_bpm15","c_fc"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()


# ========== RECUPERAÇÃO CARDÍACA ==========
def render_recuperacao_cardiaca():
    st.subheader("❤️ Recuperação da FC")
    st.markdown("Sente-se em uma cadeira,depois sente e levante em ritmo constante por um minuto,então descanse por um minuto,leve a mão ao peito e conte quantos batimentos você contou em 15 segundos e preencha")
    idade = st.session_state.get("idade", 30)
    imc = st.session_state.get("imc", 22)
    risco = "cardíaca" in st.session_state.get("grupos_risco_refinados", [])
    bpm15 = st.number_input("Batimentos em 15s após 1 min de descanso:", 0, 100, step=1)
    if st.button("Avaliar"):
        bpm = bpm15 * 4
        limite = (100 if idade < 40 else 105) - (3 if imc >= 30 else 0) - (5 if risco else 0)
        st.subheader(f"📈 FC estimada: **{bpm} bpm** (limite {limite})")
        if bpm <= limite:
            st.success("✅ Boa recuperação.")
        elif bpm <= limite + 10:
            st.warning("⚠️ Recuperação mais lenta que o ideal.")
        else:
            st.error("🚨 FC alta mesmo após descanso.")


# ========== PALPITAÇÕES ==========
def render_palpitacoes():
    st.subheader("💓 Palpitações (Mão no Peito)")
    st.markdown("Leve a mão ao peito e observe seus batimentos e responda")
    ritmo = st.radio("Ritmo:", ["Regular","Levemente irregular","Muito irregular"], index=0)
    forca = st.radio("Força:", ["Normal","Muito forte","Muito fraca","Variando"], index=0)
    sensacao = st.radio("Desconforto/aceleração sem razão?", ["Não","Sim"], index=0)
    if st.button("Resultado"):
        risco_card = "cardíaca" in st.session_state.get("grupos_risco_refinados", [])
        alerta = (ritmo != "Regular") + (forca != "Normal") + (sensacao == "Sim") + (1 if risco_card else 0)
        if alerta == 0:
            st.success("✅ Nada anormal percebido.")
        elif alerta == 1:
            st.warning("⚠️ Sinais leves. Repita em outro momento.")
        else:
            st.error("🚨 Sinais de alteração. Procure avaliação.")


# ========== APNEIA SIMPLES ==========
def render_apneia_simples():
    st.subheader("🌬️ Apneia Simples (prender respiração)")
    st.markdown("Aperte o botão e prenda a respiração o máximo possível,e quando tiver que respirar novamente,aperte para parar")
    st.session_state.setdefault("ap_inicio", None)
    st.session_state.setdefault("ap_tempo", None)

    if st.session_state.ap_inicio is None:
        if st.button("Iniciar (prender agora)"):
            st.session_state.ap_inicio = time.perf_counter()
            st.rerun()
    else:
        if st.button("Soltei o ar (parar)"):
            st.session_state.ap_tempo = round(time.perf_counter() - st.session_state.ap_inicio)
            st.session_state.ap_inicio = None
            st.rerun()

    if st.session_state.ap_tempo is not None:
        t = st.session_state.ap_tempo
        st.subheader(f"🕒 {t} segundos")
        if t < 15:
            st.error("🚨 Capacidade muito baixa.")
        elif t < 25:
            st.warning("⚠️ Abaixo do ideal.")
        elif t < 40:
            st.success("✅ Dentro do esperado.")
        else:
            st.info("💪 Excelente resistência.")
        if st.button("Refazer (Apneia)"):
            for k in ["ap_inicio","ap_tempo"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()


# ========== SOPRO SUSTENTADO ==========
def render_sopro_sustentado():
    st.subheader("🫁 Sopro Sustentado – som 'Fffff'")
    st.markdown("Aperte o botão e assopre o máximo possível,ao parar,aperte o botão para encerrar a contagem")
    st.session_state.setdefault("sp_inicio", None)
    st.session_state.setdefault("sp_tempo", None)

    if st.session_state.sp_inicio is None:
        if st.button("Começar sopro"):
            st.session_state.sp_inicio = time.perf_counter()
            st.rerun()
    else:
        if st.button("Parei"):
            st.session_state.sp_tempo = round(time.perf_counter() - st.session_state.sp_inicio)
            st.session_state.sp_inicio = None
            st.rerun()

    if st.session_state.sp_tempo is not None:
        t = st.session_state.sp_tempo
        st.subheader(f"📏 Duração: **{t} s**")
        if t < 10:
            st.error("🚨 Força respiratória baixa.")
        elif t < 20:
            st.warning("⚠️ Capacidade moderada.")
        else:
            st.success("✅ Boa capacidade.")
        if st.button("Refazer (Sopro)"):
            for k in ["sp_inicio","sp_tempo"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

def render_nodulo_mama():
    st.subheader("🧪 Nódulo na Mama")
    duro_fixo = st.checkbox("Nódulo duro e pouco móvel (parece 'preso'")
    crescimento_rapido = st.checkbox("Crescimento perceptível em semanas/meses")
    retracao_pele_mamilo = st.checkbox("Retração do mamilo ou pele com aspecto de 'casca de laranja'")
    secrecao_sanguinolenta = st.checkbox("Saída de secreção sanguinolenta pelo mamilo")
    assimetria_recente = st.checkbox("Assimetria recente entre as mamas")
    dor_ciclica = st.checkbox("Dor que varia com o ciclo (mastalgia cíclica)")

    risco = 0
    if duro_fixo: risco += 2
    if crescimento_rapido: risco += 1
    if retracao_pele_mamilo: risco += 2
    if secrecao_sanguinolenta: risco += 2
    if assimetria_recente: risco += 1
    if dor_ciclica: risco += 0  # dor cíclica isolada costuma ser benigno

    if duro_fixo and (retracao_pele_mamilo or secrecao_sanguinolenta):
        risco = max(risco, 5)  # reforço para combinação de sinais de alarme

    if risco >= 5:
        st.error("🚨 Sinais de alerta para nódulo mamário. Procure avaliação com mastologista o quanto antes.")
        st.markdown("🔎 Relacionados: **Nódulo na Mama, Secreção Mamilar, Lesões na pele**")
    elif risco >= 2:
        st.warning("⚠️ Achados que merecem avaliação clínica em breve.")
        st.markdown("🔎 Relacionados: **Nódulo na Mama, Secreção Mamilar**")
    else:
        st.success("✅ Sem combinação forte de sinais de alerta no momento.")

def render_secrecao_mamilar():
    st.subheader("🧪 Secreção Mamilar (fora da amamentação)")
    unilateral = st.checkbox("Secreção unilateral (apenas uma mama)")
    espontanea = st.checkbox("Secreção espontânea (sem apertar)")
    unico_ducto = st.checkbox("Saindo de um único ponto/ducto")
    sanguinolenta = st.checkbox("Secreção sanguinolenta ou serossanguinolenta")
    transparente = st.checkbox("Transparente/água de rocha")
    esverdeada_leitosa = st.checkbox("Esverdeada/amarelada/leitosa (fora da amamentação)")

    risco = 0
    if unilateral: risco += 1
    if espontanea: risco += 1
    if unico_ducto: risco += 1
    if sanguinolenta: risco += 2
    if transparente: risco += 1
    if esverdeada_leitosa: risco += 0  # frequentemente benigno/ducto-ectasia/galactorreia

    # combinação clássica de alerta: unilateral + espontânea + único ducto + sanguinolenta
    if unilateral and espontanea and unico_ducto and sanguinolenta:
        risco = max(risco, 5)

    if risco >= 5 or sanguinolenta:
        st.error("🚨 Padrão de alerta para secreção mamilar. Agende avaliação com mastologista.")
        st.markdown("🔎 Relacionados: **Secreção Mamilar, Nódulo na Mama**")
    elif risco >= 2:
        st.warning("⚠️ Achados que justificam avaliação clínica.")
        st.markdown("🔎 Relacionados: **Secreção Mamilar**")
    else:
        st.success("✅ Sem combinação forte de sinais de alerta no momento.")

def render_nodulo_testicular():
    st.subheader("🧪 Nódulo Testicular")
    aumento_indolor = st.checkbox("Aumento de volume indolor no testículo")
    nodulo_duro = st.checkbox("Nódulo firme/duro ao toque")
    assimetria_recente = st.checkbox("Assimetria recente entre os testículos")
    peso_escroto = st.checkbox("Sensação de peso no escroto")
    dor_subita_intensa = st.checkbox("Dor súbita intensa com náusea/vômito")
    febre_dor_progressiva = st.checkbox("Dor progressiva com febre (sensação de inflamação)")

    # atalho emergente: torção testicular
    if dor_subita_intensa:
        st.error("🚨 Dor súbita intensa com náusea pode indicar **torção testicular**. Procure **emergência imediatamente**.")
        st.markdown("🔎 Relacionados: **Dor nos testículos**")
        # mesmo que haja outros achados, a orientação urgente prevalece
        return

    risco = 0
    if aumento_indolor: risco += 2
    if nodulo_duro: risco += 2
    if assimetria_recente: risco += 1
    if peso_escroto: risco += 1
    if febre_dor_progressiva: risco += 1  # pode sugerir orquiepididimite (infeccioso), menos típico de tumor

    if (aumento_indolor and nodulo_duro) or risco >= 4:
        st.error("🚨 Achados compatíveis com nódulo testicular suspeito. Procure urologista com brevidade.")
        st.markdown("🔎 Relacionados: **Nódulo Testicular, Dor nos testículos**")
    elif risco >= 2:
        st.warning("⚠️ Achados que justificam avaliação clínica.")
        st.markdown("🔎 Relacionados: **Nódulo Testicular**")
    else:
        st.success("✅ Sem combinação forte de sinais de alerta no momento.")

# ========== ENCHIMENTO CAPILAR ==========
def render_enchimento_capilar():
    st.subheader("🩸 Enchimento Capilar (unha)")
    st.markdown("Aperte a sua unha com a outra mão por aproximadamente 2 segundos,ao soltar,ela estará branca,conte quanto tempo ela demora para voltar ao normal e responda")
    tempo = st.number_input("Segundos para voltar à cor normal:", 0, 10, step=1)
    if st.button("Ver resultado"):
        if tempo <= 2:
            st.success("✅ Normal.")
        elif tempo <= 3:
            st.warning("⚠️ Levemente prolongado.")
        else:
            st.error("🚨 Lento — possível problema circulatório.")
    if st.button("Refazer (Capilar)"):
        st.rerun()


# ========== FORÇA DA MÃO ==========
def render_forca_da_mao():
    st.subheader("✊ Força de Pegada Manual (ambas as mãos)")
    st.markdown("Pegue um objeto com sua mão direita primeiramente e segure ele o mais forte que conseguir durante um minuto,depois,repita o processo com a esquerda e responda as perguntas")
    st.session_state.setdefault("pg_etapa", "direita")
    st.session_state.setdefault("pg_result", {})

    if st.session_state.pg_etapa in ["direita","esquerda"]:
        lado = st.session_state.pg_etapa
        if st.button(f"Iniciar mão {lado} (1 min)"):
            st.session_state.pg_etapa = f"{lado}_timer"; st.rerun()
    elif st.session_state.pg_etapa.endswith("_timer"):
        lado = st.session_state.pg_etapa.replace("_timer","")
        st.info(f"⏳ Segure a garrafa com a mão **{lado}** por 1 minuto.")
        time.sleep(60); st.session_state.pg_etapa = f"{lado}_result"; st.rerun()
    elif st.session_state.pg_etapa.endswith("_result"):
        lado = st.session_state.pg_etapa.replace("_result","")
        terminou = st.radio(f"Aguentou 60s na mão {lado}?", ["Sim","Não"], key=f"pg_term_{lado}")
        sentiu = st.multiselect(f"Sintomas na mão {lado}:", ["Tremor","Formigamento","Dor","Nenhum"], key=f"pg_sent_{lado}")
        if st.button(f"Salvar mão {lado}"):
            score = (0 if terminou=="Sim" else 1) + (1 if any(s in ["Tremor","Formigamento","Dor"] for s in sentiu) else 0)
            st.session_state.pg_result[lado] = score
            st.session_state.pg_etapa = "esquerda" if lado=="direita" else "fim"
            st.rerun()
    elif st.session_state.pg_etapa == "fim":
        d = st.session_state.pg_result.get("direita",0)
        e = st.session_state.pg_result.get("esquerda",0)
        def txt(score, lado):
            if score == 0: return f"✅ **{lado}**: força/resistência preservadas."
            if score == 1: return f"⚠️ **{lado}**: leve fadiga/sintoma. Observe."
            return f"🚨 **{lado}**: fraqueza/desconforto. Avaliação indicada."
        st.markdown(txt(d, "Mão direita"))
        st.markdown(txt(e, "Mão esquerda"))
        if abs(d-e) >= 2: st.warning("⚖️ Diferença importante entre as mãos.")
        if st.button("Refazer (Força da mão)"):
            for k in ["pg_etapa","pg_result"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()


# ========== SUBIR ESCADA COM UMA PERNA ==========
def render_subir_escada_uma_perna():
    st.subheader("🦿 Subir Escada com Uma Perna")
    st.markdown("Tente subir a escada com uma perna com as pernas direita e esquerda e responda as perguntas. **Teste de risco**")
    direita = st.radio("Conseguiu com a perna direita?", ["Sim","Com dificuldade","Não"], key="esc_dir")
    esquerda = st.radio("Conseguiu com a perna esquerda?", ["Sim","Com dificuldade","Não"], key="esc_esq")
    if st.button("Resultado"):
        def nota(r): return 0 if r=="Sim" else (1 if r=="Com dificuldade" else 2)
        score = nota(direita) + nota(esquerda)
        if score == 0:
            st.success("✅ Força/equilíbrio preservados.")
        elif score <= 2:
            st.warning("⚠️ Leve dificuldade — possível desequilíbrio muscular.")
        else:
            st.error("🚨 Dificuldade significativa — avalie.")


# ========== HIDRATAÇÃO (TURGOR) ==========
def render_hidratacao():
    st.subheader("💦 Hidratação pela Pele (Turgor)")
    st.session_state.setdefault("hid_etapa", 0)
    if st.session_state.hid_etapa == 0:
        if st.button("Iniciar cronômetro 2s (belisque a pele)"):
            st.session_state.hid_etapa = 1; st.rerun()
    elif st.session_state.hid_etapa == 1:
        st.info("⏳ Segure a pele por 2 segundos…")
        time.sleep(2); st.success("✅ Solte e observe!"); st.session_state.hid_etapa = 2; st.rerun()
    elif st.session_state.hid_etapa == 2:
        resultado = st.radio("Após soltar, o que ocorreu?", ["Voltou imediatamente","Ficou enrugada/demorou"], index=0)
        if st.button("Ver resultado"):
            if resultado == "Voltou imediatamente":
                st.success("✅ Hidratação parece boa.")
            else:
                st.error("🚨 Pode haver desidratação. Beba água e observe.")
        if st.button("Refazer (Hidratação)"):
            del st.session_state.hid_etapa; st.rerun()


# ========== ICTERÍCIA NEONATAL ==========
def render_ictericia_neonatal():
    st.subheader("👶 Icterícia Neonatal (observação)")
    faixa = st.selectbox("Extensão da cor amarela:", ["Só rosto","Até o abdome","Abaixo do umbigo/corpo todo"])
    sonol = st.checkbox("Sonolência excessiva")
    aliment = st.checkbox("Recusa/queda da mamada")
    febre = st.checkbox("Febre")
    piora = st.checkbox("Piora nas últimas 24h")

    risco = (3 if faixa=="Abaixo do umbigo/corpo todo" else (1 if faixa=="Até o abdome" else 0))
    if sonol: risco += 2
    if aliment: risco += 2
    if febre: risco += 2
    if piora: risco += 1

    if st.button("Resultado"):
        if risco >= 5:
            st.error("🚨 Sinais importantes em icterícia neonatal.")
        elif risco >= 2:
            st.warning("⚠️ Achados que merecem avaliação.")
        else:
            st.success("✅ Padrão leve, tende a melhorar.")





# ========== LINFONODOS ==========
def render_linfonodos():
    st.subheader("🔎 Palpação de Linfonodos (check‑list)")
    idade = st.session_state.get("idade")
    risco_idade = 1 if (isinstance(idade,(int,float)) and (idade <= 4 or idade >= 67)) else 0

    regioes = st.multiselect("Regiões:", ["Pescoço (lateral)","Abaixo da mandíbula","Atrás da orelha","Axila","Virilha"])
    dor = st.radio("Dor ao toque?", ["Não","Leve","Moderada","Intensa"], index=0, horizontal=True)
    mobilidade = st.radio("Mobilidade:", ["Móvel","Pouco móvel","Fixo"], index=0, horizontal=True)
    consist = st.radio("Consistência:", ["Macia/borrachosa","Firme","Dura/pedra"], index=0, horizontal=True)
    tam = st.radio("Tamanho:", ["< 1 cm","1–2 cm","> 2 cm"], index=0, horizontal=True)
    dur = st.radio("Duração:", ["< 1 semana","1–3 semanas","> 3 semanas"], index=0, horizontal=True)
    ferida = st.radio("Ferida próxima com sinais de infecção?", ["Não","Sim"], index=0, horizontal=True)
    edema_inexp = st.radio("Edema em outra parte sem explicação?", ["Não","Sim"], index=0, horizontal=True)
    sist = st.multiselect("Sinais sistêmicos:", ["Febre","Perda de peso","Suor noturno"])

    if st.button("Analisar"):
        alerta = 0
        alerta += 2 if tam == "> 2 cm" else (1 if tam == "1–2 cm" else 0)
        alerta += 2 if mobilidade == "Fixo" else (1 if mobilidade == "Pouco móvel" else 0)
        alerta += 2 if consist == "Dura/pedra" else (1 if consist == "Firme" else 0)
        alerta += 2 if dur == "> 3 semanas" else (1 if dur == "1–3 semanas" else 0)
        if any(s in ["Febre","Perda de peso","Suor noturno"] for s in sist): alerta += 2
        alerta += risco_idade
        if edema_inexp == "Sim": alerta += 1

        if alerta >= 5:
            st.error("🚨 Achados que merecem **avaliação médica**.")
        elif alerta >= 3:
            if ferida == "Sim":
                st.warning("⚠️ Achados intermediários + ferida infectada próxima.Higienize e acompanhe.")
            else:
                st.warning("⚠️ Achados intermediários. Monitorar e reavaliar.")
        else:
            if ferida == "Sim":
                st.success("✅ Sem alarme; parece infecção local de ferida. Observe 7–14 dias.")
            else:
                st.success("✅ Sem sinais de alarme no momento.")





# ========== AUSÊNCIA DE MENSTRUAÇÃO ==========
def render_ausencia_menstruacao():
    st.subheader("🩸 Ausência de Menstruação (atraso + sinais)")
    import datetime as _dt
    hoje = _dt.date.today()
    dt = st.date_input("Primeiro dia da última menstruação", value=hoje)
    sangramento = st.checkbox("Sangramento fora do padrão")
    dor_abd = st.checkbox("Dor abdominal intensa")
    tontura = st.checkbox("Tontura/desmaio")
    febre = st.checkbox("Febre")

    atraso = max((hoje - dt).days - 28, 0)
    st.markdown(f"**Atraso estimado:** {atraso} dias")

    risco = (2 if atraso >= 28 else (1 if atraso >= 7 else 0))
    if dor_abd: risco += 2
    if sangramento: risco += 2
    if tontura: risco += 1
    if febre: risco += 1

    if st.button("Resultado"):
        if risco >= 4:
            st.error("🚨 Atraso significativo com sinais de alerta.")
        elif risco >= 2:
            st.warning("⚠️ Atraso relevante. Monitorar/avaliar.")
        else:
            st.success("✅ Atraso discreto, sem sinais fortes.")


# ========== MENSTRUAÇÃO EXCESSIVA ==========
def render_menstruacao_excessiva():
    st.subheader("💧 Menstruação Excessiva (quantificação simples)")
    qtd = st.number_input("Absorventes/fraldas ENCHARCADOS por dia", 0, step=1)
    coag = st.checkbox("Coágulos grandes")
    tontura = st.checkbox("Tontura/desmaio")
    dor_abd = st.checkbox("Dor abdominal intensa")
    febre = st.checkbox("Febre")

    risco = (3 if qtd >= 8 else (2 if 5 <= qtd <= 7 else (1 if 3 <= qtd <= 4 else 0)))
    if coag: risco += 1
    if tontura: risco += 1
    if dor_abd: risco += 1
    if febre: risco += 1

    if st.button("Resultado"):
        if risco >= 4:
            st.error("🚨 Perda elevada e/ou sinais associados importantes.")
        elif risco >= 2:
            st.warning("⚠️ Volume aumentado. Observe evolução.")
        else:
            st.success("✅ Sem evidência forte de excesso.")


# ========== PERDA DE MEMÓRIA (INÍCIO + RED FLAGS) ==========
def render_perda_memoria():
    st.subheader("🧠 Perda de Memória (Início + Red Flags)")
    inicio = st.selectbox("Quando começou?", ["Horas/Dias (súbito)","Semanas/Meses (progressivo)","Eventual/leve"])
    fala = st.checkbox("Alterações na fala")
    forca = st.checkbox("Fraqueza/formigamento de um lado")
    visao = st.checkbox("Alteração visual súbita")
    cefaleia = st.checkbox("Cefaleia muito intensa")
    conv = st.checkbox("Convulsão")
    trauma = st.checkbox("Trauma craniano recente")
    febre = st.checkbox("Febre")
    sed_alcool = st.checkbox("Sedativos/álcool")
    idade65 = st.checkbox("Idoso (>65 anos)")

    risco = (2 if inicio=="Horas/Dias (súbito)" else (1 if inicio=="Semanas/Meses (progressivo)" else 0))
    for flag, val in {
        fala:2, forca:2, visao:2, cefaleia:2, conv:2, trauma:1, febre:1, sed_alcool:1, idade65:1
    }.items():
        if flag: risco += val

    if st.button("Resultado"):
        if risco >= 5:
            st.error("🚨 Comprometimento neurológico relevante — avalie.")
        elif risco >= 2:
            st.warning("⚠️ Fatores associados presentes. Monitorar/avaliar.")
        else:
            st.success("✅ Sem sinais fortes de alerta pelo relato.")


# ========== EQUILÍBRIO ==========
def render_equilibrio():
    st.subheader("🦶 Equilíbrio com Olhos Fechados")
    st.markdown("Se mantenha em pé por 30 segundos com os olhos fechados e responda a pergunta")
    conseguiu = st.radio("Manteve 30s?", ["Sim, sem problemas","Sim, com desequilíbrio leve","Não"], index=0)
    if st.button("Resultado"):
        if conseguiu == "Sim, sem problemas":
            st.success("✅ Equilíbrio adequado.")
        elif conseguiu == "Sim, com desequilíbrio leve":
            st.warning("⚠️ Pequena instabilidade. Observe.")
        else:
            st.error("🚨 Dificuldade aparente de equilíbrio.")

# ======================= COORDENAÇÃO FINA =======================
def render_coordenacao_fina():
    st.subheader("✍️ Teste de Coordenação Fina – Espiral com a mão não dominante")
    st.markdown("""
    Este teste avalia sua **coordenação motora fina**. Você vai desenhar uma espiral usando a **mão que você menos usa** (geralmente a esquerda para destros, e vice-versa).

    ### Como fazer:
    1. Pegue papel e caneta.
    2. Com a mão não dominante, tente desenhar uma espiral.
    3. Depois desenhe outra com a mão dominante.
    4. Compare os dois resultados.
    """)

    tremor = st.radio("O desenho com a mão não dominante saiu com muito tremor?", ["Não", "Leve", "Moderado", "Grave"])
    comparacao = st.radio("Comparado com a mão dominante, a diferença foi...", ["Pequena", "Moderada", "Muito grande"])

    if st.button("Ver resultado (Coordenação Fina)"):
        if tremor == "Grave" or comparacao == "Muito grande":
            st.error("🚨 Pode haver alteração significativa na coordenação fina. Se isso for incomum, procure orientação médica.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários**")
        elif tremor in ["Moderado"] or comparacao == "Moderada":
            st.warning("⚠️ Coordenação não dominante reduzida. Normal em alguns casos, mas vale observar.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários**")
        else:
            st.success("✅ Coordenação fina preservada. Diferença entre as mãos dentro do esperado.")


# ======================= HUMOR E ANSIEDADE =======================
def render_humor_ansiedade():
    st.subheader("🧠 Teste de Humor e Pensamentos Acelerados")
    st.markdown("Como você tem se sentido nos últimos 7 dias?")
    humor = st.slider("Numa escala de 0 a 10, como está seu humor geral?", 0, 10, 5)
    acelerado = st.radio("Pensamentos acelerados/dificuldade de desligar a mente?", ["Não", "Às vezes", "Sim, com frequência"])
    sono = st.radio("Tem dormido bem?", ["Sim", "Sono leve/interrompido", "Insônia ou dificuldade para dormir"])

    if st.button("Ver resultado (Humor e Ansiedade)"):
        score = 0
        if humor <= 3: score += 1
        if acelerado == "Sim, com frequência": score += 1
        if sono != "Sim": score += 1

        if score == 0:
            st.success("✅ Humor e mente equilibrados no momento.")
        elif score == 1:
            st.warning("⚠️ Leves sinais de estresse ou alteração emocional.")
        else:
            st.error("🚨 Sinais de sobrecarga mental ou emocional. Procure ajuda se persistir.")


# ======================= HUMOR NA ÚLTIMA SEMANA =======================
def render_humor_ultima_semana():
    st.subheader("🧠 Avaliação de Humor nos Últimos 7 Dias")
    st.write("Avalie seu humor em cada dia (1 a 5).")
    humor_dias = []
    for i in range(1, 8):
        nota = st.slider(f"Dia {i}", min_value=1, max_value=5, value=3, key=f"humor_dia_{i}")
        humor_dias.append(nota)

    if st.button("Ver resultado (Humor da semana)"):
        media = sum(humor_dias) / 7
        st.markdown(f"📊 **Média do humor nos últimos 7 dias: {media:.2f}**")
        if media >= 4:
            st.success("😊 Humor predominantemente positivo.")
        elif media >= 2.5:
            st.info("😐 Humor dentro do esperado, com variações.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Ansiedade ou agitação intensa, Comportamento estranho à normalidade**")
        else:
            st.warning("😟 Humor predominantemente baixo. Avalie se algo está afetando seu bem-estar.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Ansiedade ou agitação intensa, Comportamento estranho à normalidade, Confusão mental**")


# ======================= AUDIÇÃO – DETECÇÃO DE SOM =======================
def render_audicao_deteccao_de_som():
    st.subheader("🔊 Teste de Detecção de Som")
    st.info("Use fones de ouvido. Ajuste o volume para um nível confortável.")
    if st.button("▶️ Tocar som de teste (1000 Hz)"):
        st.audio("https://raw.githubusercontent.com/brenaldo19/Sistemainteligenteaconselhamentomedico/main/bip_bip_1000Hz_4s.mp3", format="audio/mp3")

    resposta = st.radio("Você conseguiu ouvir o som com clareza?", ["Sim", "Não", "Somente em um dos ouvidos"])
    if st.button("Ver resultado (Detecção de Som)"):
        if resposta in ["Não", "Somente em um dos ouvidos"]:
            st.warning("⚠️ Sinal de alteração na audição.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alteração na audição**")
        else:
            st.success("✅ Tudo certo com sua audição.")


# ======================= AUDIÇÃO – FREQUÊNCIAS ALTAS/BAIXAS =======================
def render_audicao_frequencias():
    st.subheader("🎧 Teste de Frequências Auditivas")
    st.markdown("Clique para ouvir cada frequência. Use fones de ouvido.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔈 Frequência baixa (250 Hz)"):
            st.audio("https://raw.githubusercontent.com/brenaldo19/Sistemainteligenteaconselhamentomedico/main/beep_250Hz.mp3", format="audio/mp3")
        if st.button("🔈 Frequência média (1000 Hz)"):
            st.audio("https://raw.githubusercontent.com/brenaldo19/Sistemainteligenteaconselhamentomedico/main/beep_1000Hz.mp3", format="audio/mp3")
    with col2:
        if st.button("🔈 Frequência alta (8000 Hz)"):
            st.audio("https://raw.githubusercontent.com/brenaldo19/Sistemainteligenteaconselhamentomedico/main/beep_8000Hz.mp3", format="audio/mp3")

    resposta = st.radio("Você ouviu todos os sons com clareza?",
                         ["Sim", "Não ouvi o grave (250 Hz)", "Não ouvi o médio", "Não ouvi o agudo (8000 Hz)"])
    if st.button("Ver resultado (Frequências)"):
        if resposta != "Sim":
            st.warning("⚠️ Pode indicar perda auditiva seletiva.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alteração na audição**")
        else:
            st.success("✅ Sem alterações aparentes.")


# ======================= CONTAGEM EM UMA RESPIRAÇÃO =======================
def render_contagem_em_uma_respiracao():
    st.subheader("🗣️ Contagem em uma Respiração (um fôlego)")
    idade = st.session_state.get("idade")
    if idade is None: faixa = "adulto"
    elif idade <= 12: faixa = "crianca"
    elif idade >= 67: faixa = "idoso"
    else: faixa = "adulto"
    cortes = {"crianca":[8,16,26], "adulto":[10,20,30], "idoso":[8,18,26]}
    c = cortes[faixa]

    st.markdown("""
    **Como fazer:**
    1. Respire fundo, clique em **Iniciar**, e comece a contar em voz alta: "1, 2, 3, ..."
    2. Pare quando precisar inspirar de novo e digite o último número alcançado.
    """)

    st.session_state.setdefault("onebreath_inicio", None)
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.onebreath_inicio is None:
            if st.button("Iniciar"):
                st.session_state.onebreath_inicio = time.perf_counter()
                st.rerun()
        else:
            st.info("Contando... fale em voz alta até precisar inspirar novamente.")
    with col2:
        if st.button("Terminei"):
            st.session_state.onebreath_inicio = None
            st.rerun()

    contagem = st.number_input("Digite o último número que conseguiu falar em um fôlego:", min_value=0, step=1, value=0)
    if st.button("Ver resultado (Contagem em um fôlego)"):
        if contagem <= c[0]:
            st.error("🚨 Resultado baixo para a sua faixa etária.")
            st.markdown("🔎 Relacionados: **falta de ar, dificuldade respiratória, ansiedade ou agitação intensas**")
        elif contagem <= c[1]:
            st.warning("⚠️ Abaixo do ideal na sua faixa. Monitore.")
            st.markdown("🔎 Relacionados: **Falta de ar, ansiedade ou agitação intensas**")
        elif contagem <= c[2]:
            st.success("✅ Dentro do esperado para a sua faixa etária.")
        else:
            st.info("💪 Desempenho acima do esperado.")


# ======================= VARIZES =======================
def render_varizes():
    st.subheader("🦵 Teste de Peso nas Pernas (Possível Sinal de Varizes)")
    st.markdown("""
    Fique **parado em pé** por **2 minutos**, sem apoio. Observe peso, desconforto, formigamento ou dor.
    """)

    sintomas = st.multiselect("Durante os 2 minutos, você sentiu:", ["Peso nas pernas", "Inchaço", "Formigamento", "Dor", "Nenhum sintoma"])
    idade = st.session_state.get("idade", 30)
    imc = st.session_state.get("imc", 22)

    if st.button("Ver resultado (Varizes)"):
        risco = 0
        if idade > 50: risco += 1
        if imc >= 30: risco += 1
        if any(s != "Nenhum sintoma" for s in sintomas): risco += 1

        if risco == 0:
            st.success("✅ Nenhum sinal relevante de varizes foi percebido.")
        elif risco == 1:
            st.warning("⚠️ Pequeno desconforto. Vale observar a frequência dos sintomas.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força**")
        else:
            st.error("🚨 Possível comprometimento venoso nas pernas. Pode indicar início de quadro de varizes.")


# ======================= LEVANTAR DO CHÃO =======================
def render_levantar_do_chao():
    st.subheader("🧍‍♂️ Teste de Mobilidade: Levantar do Chão sem Apoio")
    st.markdown("""
    1. Sente-se no chão.
    2. Tente levantar-se **sem usar as mãos** (ou o mínimo possível).
    """)

    apoio = st.radio("Para se levantar, você usou:", [
        "Apenas as pernas (sem mãos)",
        "Uma das mãos",
        "Ambas as mãos ou precisei de apoio externo"
    ])

    idade = st.session_state.get("idade", 30)

    if st.button("Ver resultado (Levantar do chão)"):
        if apoio == "Apenas as pernas (sem mãos)":
            st.success("✅ Excelente mobilidade e força funcional.")
        elif apoio == "Uma das mãos":
            st.warning("⚠️ Leve dificuldade funcional. Normal em algumas pessoas.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força**")
        else:
            st.error("🚨 Mobilidade comprometida. Pode indicar fraqueza ou limitação funcional.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força, dor na perna ou dificuldade pra caminhar**")
        if idade > 60 and apoio != "Apenas as pernas (sem mãos)":
            st.markdown("👴 Em pessoas >60, esse teste é um preditor de risco de quedas.")


# ======================= COR DA URINA =======================
def render_cor_da_urina():
    st.subheader("💧 Teste Visual da Cor da Urina")
    st.markdown("Observe sua urina e escolha a cor mais próxima.")

    cor = st.radio("Qual cor mais se parece com a sua urina?", [
        "Transparente ou amarelo-claro",
        "Amarelo forte",
        "Amarelo escuro ou âmbar",
        "Laranja ou marrom",
        "Vermelha ou com sangue visível"
    ])

    if st.button("Ver resultado (Cor da urina)"):
        if cor == "Transparente ou amarelo-claro":
            st.success("✅ Hidratação adequada. Urina normal.")
        elif cor == "Amarelo forte":
            st.warning("⚠️ Leve desidratação. Beba mais água.")
        elif cor == "Amarelo escuro ou âmbar":
            st.warning("⚠️ Provável desidratação. Fique atento à ingestão de líquidos.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alterações urinárias**")
        elif cor == "Laranja ou marrom":
            st.error("🚨 Pode haver presença de bile, desidratação severa ou uso de medicamentos.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Icterícia**")
        else:
            st.error("🚨 Sangue na urina. **Procure um médico imediatamente.**")
            st.markdown("🔎 Possíveis sintomas relacionados: **Infecção urinária, dor ou dificuldade ao urinar**")


# ======================= DIGESTÃO =======================
def render_digestao():
    st.subheader("🍽️ Teste de Sensações Pós-Refeição")
    st.markdown("Marque sintomas que costuma sentir **após uma refeição comum**.")
    sintomas = st.multiselect("Sintomas:", [
        "Azia ou queimação no peito",
        "Empachamento (sensação de peso)",
        "Arroto frequente",
        "Inchaço abdominal ou gases",
        "Nada disso"
    ])

    if st.button("Ver resultado (Digestão)"):
        if not sintomas or "Nada disso" in sintomas:
            st.success("✅ Digestão aparentemente normal.")
        elif len(sintomas) == 1:
            st.info("🔎 Sintoma isolado. Observe se repete com frequência.")
        elif len(sintomas) == 2:
            st.warning("⚠️ Desconforto digestivo recorrente (possível relação com alimentação).")
            st.markdown("🔎 Possíveis sintomas relacionados: **Gases, dor abdominal**")
        else:
            st.error("🚨 Múltiplos sintomas digestivos. Avaliação médica pode ser indicada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Gases, dor abdominal, diarreia, náusea e enjoo**")


# ======================= RITMO INTESTINAL =======================
def render_ritmo_intestinal():
    st.subheader("🚽 Teste de Ritmo Intestinal")
    freq = st.radio("Frequência semanal:", ["Todos os dias", "4 a 6 vezes", "1 a 3 vezes", "Menos de 1 vez"])
    aspecto = st.radio("Consistência das fezes:", ["Macias/normais", "Muito duras", "Muito moles/líquidas", "Varia bastante"])

    if st.button("Ver resultado (Ritmo intestinal)"):
        risco = 0
        if freq in ["1 a 3 vezes", "Menos de 1 vez"]: risco += 1
        if aspecto in ["Muito duras", "Muito moles/líquidas", "Varia bastante"]: risco += 1

        if risco == 0:
            st.success("✅ Ritmo e consistência normais.")
        elif risco == 1:
            st.warning("⚠️ Leve alteração. Observe nos próximos dias.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Diarreia**")
        else:
            st.error("🚨 Alterações importantes. Avaliação pode ser necessária.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Diarreia, sangramento gastrointestinal, sangramento retal**")


# ======================= PELE E COCEIRA =======================
def render_pele_e_coceira():
    st.subheader("🧴 Autoavaliação de Manchas ou Coceiras na Pele")
    alteracoes = st.multiselect("Você percebeu recentemente:", [
        "Manchas vermelhas ou escuras",
        "Coceira frequente",
        "Descamação ou ressecamento excessivo",
        "Lesões que não cicatrizam",
        "Nada disso"
    ])

    if st.button("Ver resultado (Pele e Coceira)"):
        if not alteracoes or "Nada disso" in alteracoes:
            st.success("✅ Nenhuma alteração cutânea perceptível no momento.")
        elif "Lesões que não cicatrizam" in alteracoes:
            st.error("🚨 Lesões persistentes precisam ser avaliadas por um dermatologista.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Manchas anormais na pele, Infecção em ferida, lesões na pele, alergia cutânea**")
        elif len(alteracoes) >= 2:
            st.warning("⚠️ Múltiplos sinais de alteração cutânea. Fique atento e monitore a evolução.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Coceira, Infecção em ferida, lesões na pele, alergia cutânea**")
        else:
            st.info("🔎 Pequena alteração percebida. Se persistir por dias, procure um profissional.")


# ======================= URINÁRIO =======================
def render_urinario():
    st.subheader("💧 Teste Informal de Frequência Urinária")
    st.markdown("Avalia padrão diário de urina para possíveis alterações renais/urinárias.")

    freq = st.selectbox("Quantas vezes você urina por dia (em média)?", ["Menos de 4 vezes", "4 a 7 vezes", "8 a 10 vezes", "Mais de 10 vezes"])
    nocturia = st.radio("Você acorda à noite para urinar?", ["Não", "1 vez", "2 vezes ou mais"])
    jato = st.radio("Dificuldade para iniciar/interromper o jato?", ["Não", "Leve", "Moderada", "Grave"])

    if st.button("Ver resultado (Urinário)"):
        score = 0
        if freq in ["Menos de 4 vezes", "Mais de 10 vezes"]: score += 1
        if nocturia == "2 vezes ou mais": score += 1
        if jato in ["Moderada", "Grave"]: score += 1

        st.markdown("---")
        st.subheader("📊 Avaliação")
        if score == 0:
            st.success("✅ Nenhum sinal de alteração evidente no padrão urinário.")
        elif score == 1:
            st.warning("⚠️ Leve alteração no padrão urinário. Mantenha atenção.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alterações urinárias**")
        else:
            st.error("🚨 Alterações percebidas. Considere procurar urologista ou clínico.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alterações urinárias; retenção ou incontinência (depende do caso)**")
        if st.button("Refazer teste urinário"):
            st.rerun()
            # ======================= ENERGIA MATINAL =======================
def render_energia_matinal():
    st.subheader("☕ Teste de Energia ao Acordar")
    st.markdown("""
    Esse teste ajuda a identificar **níveis de fadiga e alerta ao longo do dia**.
    """)

    sono = st.radio("Você costuma acordar...", [
        "Descansado(a) e disposto(a)",
        "Com leve cansaço",
        "Muito cansado(a), mesmo dormindo bem"
    ])
    cafe = st.radio("Você precisa de café ou estimulante para funcionar pela manhã?",
                    ["Não", "Às vezes", "Todos os dias"])

    if st.button("Ver resultado (Energia matinal)"):
        pontos = 0
        if sono == "Com leve cansaço": pontos += 1
        if sono == "Muito cansado(a), mesmo dormindo bem": pontos += 2
        if cafe == "Às vezes": pontos += 1
        if cafe == "Todos os dias": pontos += 2

        if pontos == 0:
            st.success("✅ Energia matinal adequada.")
        elif pontos <= 2:
            st.warning("⚠️ Pode haver leve fadiga acumulada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Náusea ou enjoo, Confusão mental**")
        else:
            st.error("🚨 Sinais de fadiga importante. Avalie seu sono, rotina e alimentação.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Hipotensão ou colapso, Náusea ou enjoo, Confusão mental**")


# ======================= VARIAÇÃO DE PESO (30 DIAS) =======================
def render_variacao_peso_30d():
    st.subheader("⚖️ Variação de Peso nos Últimos 30 Dias")
    peso_atual = st.number_input("Digite seu peso atual (kg):", min_value=20.0, max_value=300.0, step=0.1)
    peso_passado = st.number_input("Digite seu peso de 30 dias atrás (kg):", min_value=20.0, max_value=300.0, step=0.1)

    if st.button("Ver resultado (Variação de peso)"):
        variacao = peso_atual - peso_passado
        percentual = (abs(variacao) / peso_passado) * 100 if peso_passado else 0.0

        st.markdown(f"📉 Variação: **{variacao:.1f} kg** ({percentual:.1f}%)")

        if percentual < 2:
            st.success("✅ Variação dentro da faixa esperada.")
        elif percentual <= 5:
            st.info("⚠️ Pequena variação detectada. Fique atento(a).")
            st.markdown("🔎 Possíveis sintomas relacionados: **Náusea ou enjoo, Ansiedade ou agitação intensa, Comportamento estranho à normalidade**")
        else:
            st.warning("🚨 Variação significativa! Considere investigar causas clínicas ou comportamentais.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Náusea ou enjoo, Hiperglicemia, Hipoglicemia, Ansiedade ou agitação intensa, Comportamento estranho à normalidade**")

