# autotestes.py
import time
import random
import streamlit as st

# ========== 1) TEMPO DE REAÇÃO ==========
def render_tempo_de_reacao():
    st.subheader("🧠 Teste de Tempo de Reação")
    st.warning("⚠️ A primeira tentativa é de preparação e **não será contabilizada**.")

    # estados (prefixo tr_)
    st.session_state.setdefault("tr_testando", False)
    st.session_state.setdefault("tr_ready", False)
    st.session_state.setdefault("tr_start", None)
    st.session_state.setdefault("tr_delay", None)
    st.session_state.setdefault("tr_tentativa", 1)
    st.session_state.setdefault("tr_resultados", [])

    # fluxo
    if not st.session_state.tr_testando and st.session_state.tr_tentativa <= 8:
        st.session_state.tr_delay = random.uniform(3, 7)
        st.session_state.tr_ready = False
        st.session_state.tr_testando = True
        st.experimental_rerun()

    elif st.session_state.tr_testando and not st.session_state.tr_ready:
        time.sleep(st.session_state.tr_delay)
        st.session_state.tr_start = time.perf_counter()
        st.session_state.tr_ready = True
        st.experimental_rerun()

    elif st.session_state.tr_testando and st.session_state.tr_ready:
        st.success("✅ Clique agora!")
        if st.button("🟢 Clique aqui!"):
            fim = time.perf_counter()
            tempo_reacao = fim - (st.session_state.tr_start or fim) - 0.47  # correção interna
            if st.session_state.tr_tentativa != 1:
                st.session_state.tr_resultados.append(tempo_reacao)
            st.session_state.tr_tentativa += 1
            st.session_state.tr_testando = False
            st.session_state.tr_ready = False
            st.experimental_rerun()

    elif st.session_state.tr_tentativa > 8:
        st.subheader("⏱️ Resultados")
        for i, r in enumerate(st.session_state.tr_resultados, start=2):
            st.write(f"Tentativa {i}: ⏱️ {r:.2f} s")

        if st.session_state.tr_resultados:
            media = sum(st.session_state.tr_resultados) / len(st.session_state.tr_resultados)
            st.subheader(f"🏁 Média final: **{media:.2f} s**")

            # Perfil e faixas (mantido do seu miolo, simplificado para não depender de outros estados)
            idade = st.session_state.get("idade", 30)
            imc = st.session_state.get("imc", 22)
            gravidez = st.session_state.get("gravida", False)
            sexo = st.session_state.get("sexo", "Outro")
            riscos = st.session_state.get("grupos_risco_refinados", [])

            base = 0.40
            if idade <= 7: base += 0.20
            elif idade <= 16: base += 0.10
            elif idade <= 35: base += 0.00
            elif idade <= 58: base += 0.05
            else: base += 0.10

            if imc < 16: base += 0.10
            elif imc >= 30: base += 0.05
            if gravidez: base += 0.08
            if "neurológica" in riscos or "psiquiátrica" in riscos: base += 0.10
            if "cardíaca" in riscos: base += 0.05
            if "respiratória" in riscos: base += 0.05

            lim_inf = base * 0.75
            lim_sup = base * 1.25

            if media < lim_inf:
                st.success("⚡ Seu tempo está **acima do esperado**. Excelente reflexo!")
            elif media > lim_sup:
                st.warning("🐢 Seu tempo está **abaixo do esperado**. Considere repetir o teste mais tarde.")
                st.markdown("🔎 Relacionados: **Hipoglicemia, Hipotensão/colapso, Formigamento ou perda de força**")
            else:
                st.info("✅ Dentro do esperado para seu perfil.")

        if st.button("🔁 Refazer o teste (Tempo de Reação)"):
            for k in ["tr_testando","tr_ready","tr_start","tr_delay","tr_tentativa","tr_resultados"]:
                if k in st.session_state: del st.session_state[k]
            st.experimental_rerun()


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


# ========== 3) SUDORESE NOTURNA ==========
def render_sudorese_noturna():
    st.subheader("🌙 Sudorese Noturna (Duração + Red Flags)")
    duracao = st.selectbox("Há quanto tempo?", ["Menos de 1 semana", "1–3 semanas", "≥ 4 semanas"])
    encharca = st.checkbox("Encharca roupa/lençol")
    febre = st.checkbox("Febre")
    perda_peso = st.checkbox("Perda de peso não intencional/rápida")
    tosse_persistente = st.checkbox("Tosse > 2 semanas")
    tosse_sangue = st.checkbox("Tosse com sangue")
    linfonodo = st.checkbox("Inchaço dos linfonodos")
    palpitacoes = st.checkbox("Palpitações")
    ansiedade = st.checkbox("Ansiedade/agitação intensas")

    risco = 0
    if duracao == "≥ 4 semanas": risco += 2
    if encharca: risco += 1
    if febre: risco += 1
    if perda_peso: risco += 2
    if tosse_persistente: risco += 1
    if tosse_sangue: risco += 2
    if linfonodo: risco += 1
    if palpitacoes or ansiedade: risco += 1

    if risco >= 5:
        st.error("🚨 Sudorese noturna com sinais de alerta.")
        st.markdown("🔎 Relacionados: **Sudorese noturna, Febre, Perda de peso, Tosse, Linfonodos, Palpitações, Ansiedade**")
    elif risco >= 2:
        st.warning("⚠️ Sudorese noturna com achados associados.")
        st.markdown("🔎 Relacionados: **Sudorese noturna, Febre, Perda de peso**")
    else:
        st.success("✅ Quadro leve/recente sem outros sinais relevantes.")


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
        st.experimental_rerun()
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
            st.experimental_rerun()


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
            st.experimental_rerun()
    else:
        st.info("⏳ Conte suas respirações por 30 segundos…")
        time.sleep(30)
        st.session_state.fr_contando = False
        st.experimental_rerun()

    if not st.session_state.fr_contando and st.session_state.fr_valor is None:
        resp = st.number_input("Respirações em 30s", 0, 50, step=1)
        if st.button("Ver resultado"):
            st.session_state.fr_valor = resp * 2
            st.experimental_rerun()

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
            st.experimental_rerun()
