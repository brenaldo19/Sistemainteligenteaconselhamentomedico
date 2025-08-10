import streamlit as st
from datetime import datetime
import pandas as pd
import unicodedata
import re

def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    t = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    t = t.strip().lower()
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^a-z0-9_]", "", t)
    return t

ORDEM_CORES = ["verde", "amarelo", "laranja", "vermelho"]

def max_cor(*cores):
    idx = [ORDEM_CORES.index(c) for c in cores if c in ORDEM_CORES]
    return ORDEM_CORES[max(idx)] if idx else "verde"

def score_para_cor(score, tabela):
    # Ordena por limiar, do maior pro menor
    tabela_ord = sorted(tabela, key=lambda x: x[0], reverse=True)
    for limiar, cor in tabela_ord:
        if score >= limiar:
            return cor
    return "verde"

# ===============================
# MAPEAMENTO DE SINTOMAS E SISTEMAS
# ===============================

sistemas_sintomas = {
    "cardiaco": [
        "dor no peito", "palpitação", "dor no ombro ou braço", "queimação no peito"
    ],
    "respiratorio": [
        "falta de ar", "dificuldade respiratória", "engasgo ou obstrução das vias aéreas"
    ],
    "neurologico": [
        "convulsão", "confusão mental", "comportamento estranho à normalidade",
        "desmaio ou tontura", "alterações na fala", "alterações visuais súbitas",
        "tremores ou movimentos involuntários", "formigamento ou perda de força", "sensação de desmaio"
    ],
    "gastrointestinal": [
        "náusea ou enjoo", "diarreia em criança", "sangramento gastrointestinal",
        "vômito em criança", "dor abdominal", "gases", "diarreia", "sangramento retal", "vômito"
    ],
    "urinario": [
        "dor ou dificuldade ao urinar", "retenção urinária", "incontinência urinária",
        "alterações urinárias"
    ],
    "musculoesqueletico": [
        "dor nas articulações", "dor nas costas", "dor na perna e dificuldade pra caminhar",
        "trauma ou queda", "dor no ombro ou braço"
    ],
    "cutaneo": [
        "alergia cutânea", "reação alérgica", "lesões na pele", "Manchas anormais na pele", "coceira na pele", "inchaço incomum"
    ],
    "oftalmologico": [
        "alterações visuais súbitas", "dor ou olho vermelho", "inchaço nos olhos ou face",
        "corpo estranho nos olhos, ouvidos ou nariz"
    ],
    "otorrino": [
        "dor no ouvido", "coriza e espirros", "sangramento nasal", "Alteração na audição", "dificuldade pra engolir", "corpo estranho na garganta"
    ],
    "obstetrico": [
        "dor durante a gravidez", "trabalho de parto", "redução dos movimentos fetais", "sangramento vaginal"
    ],
    "pediatrico": [
        "febre lactente", "icterícia neonatal", "queda em criança", "choro persistente"
    ],
    "hematologico": [
        "sangramento ativo", "sangramento gastrointestinal", "sangramento nasal", "sangramento retal", "inchaço dos linfonodos"
    ],
    "psiquiatrico": [
        "ansiedade ou agitação intensas", "comportamento estranho à normalidade"
    ],
    "endocrino": [
        "hipoglicemia", "hiperglicemia", "hipotensão", "temperatura muito baixa"
    ],
    "hepatico": [
        "icterícia", "icterícia neonatal"
    ],
    "infeccioso": [
        "febre", "infecção em ferida", "sinais de intoxicação ou envenenamento"
    ],
    "reprodutor_masculino": [
        "nódulo testicular", "dor nos testículos", "sangue no sêmen"
    ],
    "mamario": [
        "nódulo mamário", "secreção mamilar (fora da amamentação)"
    ],
    "ginecologico": [
        "sangramento vaginal"  # (também listado em obstétrico por regra de exceção)
    ]
}

# Recria o mapa sintoma → sistema JÁ com normalização
sintoma_para_sistema = {
    normalizar(s): k
    for k, lista in sistemas_sintomas.items()
    for s in lista
}

# Dicionário sintoma → sistema, já normalizado
sintoma_para_sistema = {
    normalizar(sintoma): sistema
    for sistema, lista in sistemas_sintomas.items()
    for sintoma in lista
}

# ===============================
# CONTROLE INICIAL DO SESSION_STATE
# ===============================
valores_iniciais = {
    "etapa": 1,
    "etapa_2": False,
    "etapa_3": False,
    "congelar_inputs": False,
    "sintomas_escolhidos": []
}

for chave, valor in valores_iniciais.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

manual_aberto = st.toggle("📘 Manual do sistema – clique para abrir/fechar")

if manual_aberto:
    st.markdown("""
    ### 📘 Guia de Uso – Sistema de Aconselhamento Médico

    Muitos recorrem a bancos de pesquisa, como o Google, quando se sentem doentes,não por ignorância, mas por desespero diante de um sistema de saúde que fecha as portas para quem não tem cartão de crédito. Este sistema foi criado para tentar atenuar, ainda que minimamente, essa desigualdade, oferecendo, de forma ética e responsável, um aconselhamento inteligente, confiável e acessível. Não porque somos melhores, mas sim porque somos iguais.

    Além disso, também desenvolvemos um dicionário e buscamos adaptar tudo para a linguagem mais popular possível, pois estamos cansados de uma linguagem médica excessivamente técnica,limitando o entendimento real da situação.
    
    Este sistema foi feito pra ajudar você a **entender melhor seus sintomas** antes de buscar um atendimento,ao final do aconselhamento principal será fornecida uma cor a você,ao receber o resultado receberá uma legenda explicando quais são os melhores próximos passos a serem tomados,mas o sistema se manifesta em todas as suas nuances,não somente no resultado final,fique atento a todas as mensagens fornecidas pelo sistema para uma experiência mais completa.

    
    - **🧠 Dicionário de Sintomas:** explica os sintomas em dois níveis, técnico e em linguagem acessível,além disso,explica os termos que serão apresentados durante a questão de detalhamento do sintoma
    - **🧪 Autotestes:** você pode fazer alguns testes simples em casa para investigar sinais do corpo.
    - **📊 Aconselhamento Principal:** aqui você escolhe um sintoma, responde perguntas e recebe um nível de atenção (Entre 'Pode ficar tranquilo' até 'Vá ao médico o mais rápido possível).

    > 🧭 A ideia é funcionar como um **guia de viagem pelo seu corpo**, não como um diagnóstico final.

    **Observações importantes**:Se estiver no celular,consulte o dicionário antes de escolher os sintomas,pois a escolha manual de sintomas no celular se manifesta melhor ao escrever-se o sintoma,e para escrever corretamente e ter certeza que o sintoma selecionado é o certo a ser selecionado para seu caso,siga a instrução de consulta.
    
    **Observações importantes**:No menu lateral esquerda,você terá três opções,'Nenhuma','Dicionário de sintomas' e 'Autotestes para apuração de sintomas',caso você selecione o primeiro a tela ficará livre para você seguir o aconselhamento principal normalmente,já se você escolher algum dos outros dois,o escolhido ficará na parte de cima da tela,onde você poderá interagir com ele,mantendo o aconselhamento principal na parte de baixo da tela
    
    **Observações importantes**:Os autotestes só ficarão disponíveis após você preencher todos os seus dados na primeira etapa,pois estes serão importantes para cálculos posteriores
    
    **Observações importantes**:O sistema NÃO guarda seus dados,tudo é feito internamente e sem qualquer tipo de exportação de dados
    
    **⚠️ Importante**:O sistema **NÃO substitui consulta médica**. Se estiver em dúvida, procure um profissional.

    """)


# ===============================
# FUNÇÕES UTILITÁRIAS
# ===============================
def aumentar_cor_em_1_nivel(cor_atual):
    ordem = ["verde", "amarelo", "laranja", "vermelho"]
    try:
        idx = ordem.index(cor_atual)
        if idx < len(ordem) - 1:
            return ordem[idx + 1]
        else:
            return cor_atual  # já é vermelho, não sobe mais
    except ValueError:
        return cor_atual  # cor inválida, retorna como veio

def calcular_imc(altura, peso):
    """Retorna o IMC com uma casa decimal."""
    try:
        return round(peso / (altura ** 2), 1)
    except ZeroDivisionError:
        return None

def classificar_imc(imc):
    """Classifica o IMC como Desnutrido, Normal ou Obeso."""
    if imc is None:
        return "Inválido"
    elif imc < 18.5:
        return "Desnutrido"
    elif imc >= 30:
        return "Obeso"
    else:
        return "Normal"

def gerar_sistemas_afetados_por_fatores(idade, imc_class, gravida, condicoes_brutas):
    # tudo em slug (sem acento/caixa)
    refinados = {normalizar(x) for x in (condicoes_brutas or [])}

    if idade is not None:
        if idade < 5:
            refinados.update(["infeccioso","respiratorio","neurologico","musculoesqueletico","otorrino","gastrointestinal","pediatrico"])
        elif idade > 60:
            refinados.update(["cardiaco","neurologico","musculoesqueletico","endocrino","infeccioso","hepatico","oftalmologico","cutaneo","urinario"])
        elif idade < 14 and imc_class == "Desnutrido":
            refinados.add("neurologico")

    if imc_class == "Obeso":
        refinados.update(["cardiaco","respiratorio","hematologico","psiquiatrico","endocrino","musculoesqueletico"])
    elif imc_class == "Desnutrido":
        refinados.update(["infeccioso","hematologico","gastrointestinal","musculoesqueletico","neurologico","psiquiatrico"])

    if str(gravida).lower() in ["sim","true","1"]:
        refinados.update(["hematologico","endocrino","mamario","infeccioso","otorrino","musculoesqueletico","ginecologico","obstetrico"])
        if idade is not None and idade < 16:
            refinados.update(["cardiaco","neurologico","endocrino","obstetrico","psiquiatrico","mamario","ginecologico"])

    return list(refinados)

def sistemas_afetados_secundariamente(grupo_primario):
    g = normalizar(grupo_primario)
    tabela = {
        "cardiaco": ["respiratorio", "hematologico", "urinario", "neurologico"],
        "respiratorio": ["cardiaco", "otorrino", "neurologico"],
        "neurologico": ["psiquiatrico", "musculoesqueletico", "urinario", "gastrointestinal", "respiratorio", "cardiaco"],
        "gastrointestinal": ["hepatico", "hematologico", "urinario"],
        "urinario": ["cardiaco", "endocrino"],
        "otorrino": ["respiratorio"],
        "hematologico": ["cardiaco", "endocrino", "hepatico", "urinario"],
        "psiquiatrico": ["neurologico"],
        "endocrino": ["cardiaco", "hepatico", "hematologico"],
        "hepatico": ["gastrointestinal", "hematologico"],
        "autoimune": ["cutaneo","hematologico","urinario","neurologico","musculoesqueletico","hepatico","psiquiatrico"],
        "diabetes": ["neurologico","oftalmologico","urinario","cardiaco","cutaneo","hematologico"],
        "reprodutor_masculino": ["reprodutor_masculino"],
        "mamario": ["mamario"],
        "pediatrico": ["pediatrico"],
        "obstetrico": ["obstetrico"],
        "cutaneo": ["cutaneo"],
        "oftalmologico": ["oftalmologico"],
        "ginecologico": ["ginecologico"],
    }
    return tabela.get(g, [])

def verificar_se_deve_subir_cor(sintomas_escolhidos, sistemas_afetados, sintoma_para_sistema):
    sistemas_norm = {normalizar(s) for s in (sistemas_afetados or [])}
    for s in sintomas_escolhidos:
        sistema = sintoma_para_sistema.get(normalizar(s))
        if sistema and sistema in sistemas_norm:
            return True
    return False


    for sintoma in sintomas_norm:
        sistema = sintoma_para_sistema.get(sintoma)
        if sistema and normalizar(sistema) in sistemas_norm:
            return True
    return False

def classificar_combinacao(sintomas, cores):
    """
    Combina de forma conservadora:
    1) Nunca rebaixa abaixo da maior cor individual.
    2) Usa soma de pesos para ESCALAR quando fizer sentido.
    """
    pesos = {"verde": 0.2, "amarelo": 1.0, "laranja": 3.5, "vermelho": 6.5}
    total = sum(pesos.get(c, 0) for c in cores)

    # 1) Maior cor individual (nunca abaixo disso)
    cor_individual_max = max_cor(*cores)

    # 2) Escalonamento por soma
    if any(c == "vermelho" for c in cores):
        cor_por_total = "vermelho"
    elif total >= 4.5:
        cor_por_total = "vermelho"
    elif total >= 2.2:
        cor_por_total = "laranja"
    elif total >= 1.0:
        cor_por_total = "amarelo"
    else:
        cor_por_total = "verde"

    # Resultado final = máximo entre a maior individual e a do total
    return max_cor(cor_individual_max, cor_por_total)


# --- AJUSTE CONSERVADOR POR FATORES (idade/gravidez e duplicidade de sistema) ---
def calcular_ajuste_por_fatores_conservador(
    sintomas_escolhidos,
    cores_individuais,
    sintoma_para_sistema,
    idade=None,
    gravida=False
):
    """
    Retorna 0 (sem ajuste) ou 1 (sobe 1 nível).

    Regras:
      - Se TODOS os sintomas estão VERDES → NÃO ajusta.
      - Só considera ajuste se houver pelo menos um sintoma AMARELO, LARANJA ou VERMELHO.
      - Ajusta (sobe 1) se:
          a) idade <= 4 ou >= 67, OU gravidez verdadeira; OU
          b) houver >= 2 sintomas do MESMO sistema corporal.
    """
    cores_individuais = cores_individuais or []
    sintomas_escolhidos = sintomas_escolhidos or []

    # 1) Tudo verde? Não ajusta
    if all(c == "verde" for c in cores_individuais):
        return 0

    # 2) Só consideramos ajuste se houver alguma cor >= amarelo
    if not any(c in ("amarelo", "laranja", "vermelho") for c in cores_individuais):
        return 0

    # 3) Risco alto por idade/gravidez
    risco_alto = False
    if idade is not None and (idade <= 4 or idade >= 67):
        risco_alto = True
    if str(gravida).strip().lower() in ["sim", "true", "1"]:
        risco_alto = True

    # 4) Checa duplicidade de sistema entre os sintomas escolhidos
    contagem_por_sistema = {}
    for s in sintomas_escolhidos:
        sist = sintoma_para_sistema.get(normalizar(s))
        if not sist:
            continue
        contagem_por_sistema[sist] = contagem_por_sistema.get(sist, 0) + 1

    duplicidade_sistema = any(qtd >= 2 for qtd in contagem_por_sistema.values())

    # 5) Critério final de ajuste
    if risco_alto or duplicidade_sistema:
        return 1

    return 0

st.title("Sistema Inteligente de Aconselhamento médico")
st.markdown("⚠️ Este sistema é apenas um aconselhamento inicial e **não substitui atendimento médico.**")
st.markdown("👋 Olá! Bem-vindo ao sistema de aconselhamento interativo.")
st.markdown("Consulte o manual do sistema para coompreender todas as funcionalidades do site e usá-lo mais eficientemente")
st.markdown("Responda com sinceridade. O único beneficiado por sua honestidade nesse sistema é você mesmo")
st.markdown("---")


# SIDEBAR – BOTÃO DO DICIONÁRIO
def dicionario_sintomas():
    d={
"Mãos ou pés frios e arroxeados": {
    "definicao": "Alteração de temperatura e cor nas extremidades, geralmente causada por má circulação ou resposta exagerada ao frio.",
    "popular": "Mãos ou pés ficam frios e com cor arroxeada.",
    "clinico": "Cianose periférica / Fenômeno de Raynaud",
    "termos": {
        "Sempre, mesmo em clima quente": "As extremidades permanecem frias e arroxeadas o tempo todo.",
        "Principalmente em dias frios": "O problema aparece mais quando a temperatura está baixa.",
        "Apenas ocasionalmente": "Acontece raramente.",
        "Mais de 1 mês": "O sintoma persiste há mais de um mês.",
        "Entre 1–4 semanas": "O sintoma começou há uma a quatro semanas.",
        "Menos de 1 semana": "O sintoma surgiu nos últimos dias.",
        "Dormência ou formigamento": "Sensação de formigamento ou dormência nos dedos.",
        "Dor ao movimentar os dedos": "Dor ao mexer dedos das mãos ou dos pés.",
        "Mudança de cor ao frio (branco/azul/vermelho)": "Alterações de cor quando exposto ao frio.",
        "Feridas nas extremidades": "Feridas que surgem nas mãos ou pés."
    }
},

"Perda progressiva da visão": {
    "definicao": "Diminuição gradual da acuidade visual ao longo do tempo, podendo afetar um ou ambos os olhos.",
    "popular": "Está perdendo a visão aos poucos.",
    "clinico": "Baixa visual progressiva",
    "termos": {
        "Semanas a meses": "A visão foi piorando ao longo de semanas ou meses.",
        "Mais de 1 ano": "A perda de visão acontece há mais de um ano.",
        "Poucos dias": "A visão piorou de forma rápida, em poucos dias.",
        "Um olho": "A alteração visual afeta apenas um olho.",
        "Ambos os olhos": "A alteração visual afeta os dois olhos.",
        "Dor ocular": "Desconforto ou dor nos olhos.",
        "Olho vermelho": "Vermelhidão ocular visível.",
        "Sensibilidade à luz (fotofobia)": "Incomodo excessivo com luz.",
        "Halos ao redor de luzes": "Aparição de círculos luminosos ao redor das luzes."
    }
},

"Visão embaçada progressiva": {
    "definicao": "Perda gradual da nitidez da visão, dificultando o foco em objetos e detalhes.",
    "popular": "A visão está ficando turva aos poucos.",
    "clinico": "Opacificação visual progressiva",
    "termos": {
        "Semanas a meses": "O embaçamento foi se instalando ao longo de semanas ou meses.",
        "Mais de 1 ano": "O embaçamento está presente há mais de um ano.",
        "Poucos dias": "O embaçamento surgiu de forma recente, em poucos dias.",
        "Um olho": "A visão turva afeta apenas um olho.",
        "Ambos os olhos": "A visão turva afeta os dois olhos.",
        "Cefaleia": "Dor de cabeça.",
        "Dificuldade para focar": "Problema em ajustar o foco da visão.",
        "Piora à noite": "A visão fica pior em ambientes escuros.",
        "Alterações de cores": "Mudança na percepção das cores."
    }
},

    "Ausência de menstruação": {
    "definicao": "Falta do ciclo menstrual no período esperado, podendo indicar gravidez, alterações hormonais ou outras condições médicas.",
    "popular": "A menstruação não veio na data esperada.",
    "clinico": "Amenorreia",
    "termos": {
        "Atraso ≥ 4 semanas": "O ciclo menstrual está atrasado um mês ou mais.",
        "Atraso de 1 a 3 semanas": "O ciclo menstrual está atrasado de uma a três semanas.",
        "Dor abdominal intensa": "Dor forte na barriga.",
        "Sangramento vaginal": "Sangramento fora do ciclo normal.",
        "Tontura/desmaio": "Sensação de perda de equilíbrio ou desmaio.",
        "Febre": "Temperatura do corpo elevada."
    }
},

"Menstruação excessiva": {
    "definicao": "Sangramento menstrual em grande quantidade ou por tempo prolongado.",
    "popular": "A menstruação vem muito forte ou dura mais que o normal.",
    "clinico": "Menorragia",
    "termos": {
        "≥ 8 totalmente encharcados": "Uso de oito ou mais absorventes/fraldas cheios por dia.",
        "5–7 encharcados": "Uso de cinco a sete absorventes/fraldas cheios por dia.",
        "Tontura/desmaio": "Sensação de perda de equilíbrio ou desmaio.",
        "Palidez intensa": "Pele muito clara, indicando possível anemia.",
        "Dor abdominal intensa": "Dor forte na barriga.",
        "Febre": "Temperatura do corpo elevada."
    }
},

"Tosse": {
    "definicao": "Ato reflexo para limpar as vias aéreas de muco, partículas ou irritantes.",
    "popular": "Forçar a saída de ar com som, para limpar o peito ou garganta.",
    "clinico": "Tosse",
    "termos": {
        "≥ 3 semanas": "Tosse que dura três semanas ou mais.",
        "1–2 semanas": "Tosse que dura entre uma e duas semanas.",
        "Com sangue": "Presença de sangue ao tossir.",
        "Produtiva (com catarro)": "Tosse que traz muco ou secreção.",
        "Falta de ar": "Dificuldade para respirar.",
        "Dor torácica": "Dor no peito.",
        "Febre": "Temperatura do corpo elevada.",
        "Perda de peso": "Emagrecimento não intencional.",
        "Sudorese noturna": "Suor excessivo durante a noite."
    }
},

"Hemorragia gengival intensa": {
    "definicao": "Sangramento abundante nas gengivas, podendo indicar inflamação, trauma ou distúrbios de coagulação.",
    "popular": "Sangramento forte na gengiva.",
    "clinico": "Hemorragia gengival",
    "termos": {
        "Diária": "O sangramento na gengiva acontece todos os dias.",
        "≥ 10 minutos": "O sangramento leva dez minutos ou mais para parar.",
        "Hematomas frequentes": "Aparecimento fácil de manchas roxas na pele.",
        "Sangramentos em outros locais": "Presença de sangramento no nariz, urina, fezes ou pele.",
        "Febre": "Temperatura do corpo elevada.",
        "Cansaço extremo": "Sensação intensa de fadiga e falta de energia."
    }
},

"Edema inexplicado": {
    "definicao": "Acúmulo anormal de líquido nos tecidos, causando inchaço, sem causa aparente imediata.",
    "popular": "Inchaço no corpo sem motivo claro.",
    "clinico": "Edema",
    "termos": {
        "Um lado apenas": "Inchaço localizado em apenas um membro ou parte do corpo.",
        "Ambos os lados": "Inchaço simétrico, como nas duas pernas.",
        "Rosto/pálpebras": "Inchaço visível no rosto ou nos olhos.",
        "Súbito (minutos/horas)": "Inchaço que aparece rapidamente, em poucas horas ou minutos.",
        "Falta de ar": "Dificuldade para respirar.",
        "Dor no peito": "Dor na região torácica.",
        "Febre": "Temperatura do corpo elevada.",
        "Vermelhidão/dor local": "Área inchada e dolorida, possivelmente inflamada.",
        "Aumento súbito de peso": "Ganho de peso rápido, sem explicação."
    }
},
"Perda súbita de coordenação": {
    "definicao": "Dificuldade repentina para realizar movimentos coordenados, podendo indicar problemas neurológicos graves como AVC.",
    "popular": "Perdeu de repente a capacidade de se mover de forma coordenada.",
    "clinico": "Ataxia de início súbito",
    "termos": {
        "Início súbito (minutos/horas)": "A dificuldade de coordenação começou de repente, em minutos ou poucas horas.",
        "Início em até 48h": "A dificuldade se instalou em um ou dois dias.",
        "Fraqueza em um lado do corpo": "Perda de força em apenas um lado do corpo.",
        "Alteração na fala": "Fala enrolada ou dificuldade para se expressar.",
        "Alteração visual súbita": "Perda ou mudança repentina na visão.",
        "Cefaleia muito intensa/pior da vida": "Dor de cabeça muito forte, descrita como a pior já sentida.",
        "Perda de sensibilidade/formigamentos": "Dormência ou sensação de formigamento em partes do corpo.",
        "Trauma craniano recente": "Bateu a cabeça recentemente.",
        "Uso de anticoagulantes": "Faz uso de medicamentos que afinam o sangue."
    }
},

"Calafrios": {
    "definicao": "Sensação súbita de frio com tremores, geralmente associada a febre e infecção.",
    "popular": "Sensação de frio intenso com tremedeira, mesmo em ambiente quente.",
    "clinico": "Calafrios",
    "termos": {
        "Febre ≥ 39°C": "Temperatura do corpo de 39°C ou mais.",
        "Febre 38–38,9°C": "Temperatura entre 38 e 38,9°C.",
        "Várias vezes ao dia": "Os calafrios se repetem diversas vezes no mesmo dia.",
        "Confusão/desorientação": "Dificuldade para entender onde está ou o que está acontecendo.",
        "Pressão baixa/tontura ao levantar": "Sensação de fraqueza e queda de pressão ao levantar-se.",
        "Dor ao urinar/urina turva": "Desconforto ou ardência para urinar com urina turva.",
        "Tosse com catarro/dor torácica": "Produção de secreção ao tossir e dor no peito.",
        "Ferida com vermelhidão/calor/saída de pus": "Sinal de infecção em ferida aberta.",
        "Calafrios após viagem/área endêmica": "Histórico de viagem para regiões com doenças como malária."
    }
},

"Sudorese noturna": {
    "definicao": "Suor excessivo durante o sono, podendo encharcar roupas ou lençóis.",
    "popular": "Suor forte à noite, a ponto de molhar roupa e cama.",
    "clinico": "Hiperidrose noturna",
    "termos": {
        "≥ 4 semanas": "Sudorese persistente por um mês ou mais.",
        "Encharca roupa/lençol": "Suor tão intenso que molha roupas e lençol.",
        "Febre": "Temperatura do corpo elevada.",
        "Perda de peso não intencional": "Emagrecimento sem estar tentando.",
        "Tosse há > 2 semanas": "Tosse persistente por mais de duas semanas.",
        "Tosse com sangue": "Presença de sangue ao tossir.",
        "Inchaço dos linfonodos": "Gânglios aumentados no pescoço, axilas ou virilha.",
        "Palpitações/ansiedade": "Sensação de coração acelerado ou ansiedade intensa."
    }
},

"Perda de peso súbita": {
    "definicao": "Emagrecimento rápido e não intencional em um curto período de tempo.",
    "popular": "Perdeu muito peso de repente, sem dieta.",
    "clinico": "Emagrecimento súbito",
    "termos": {
        "> 5% em 1 mês": "Perdeu mais de 5% do peso corporal em um mês.",
        "Muito diminuído": "Apetite bastante reduzido.",
        "Sede/urinar muito": "Sensação de sede constante e urina frequente.",
        "Náusea/vômitos persistentes": "Enjoo e vômitos que não passam.",
        "Diarreia crônica": "Diarreia frequente por semanas.",
        "Dificuldade para engolir (progressiva)": "A dificuldade para engolir foi piorando com o tempo.",
        "Fezes pretas (melena) ou sangue nas fezes": "Presença de sangue visível ou fezes muito escuras.",
        "Febre e/ou sudorese noturna": "Febre persistente ou suor excessivo à noite.",
        "Tremor/taquicardia/intolerância ao calor": "Mãos trêmulas, batimentos acelerados e desconforto com calor."
    }
},

"Dor durante relação sexual": {
    "definicao": "Desconforto ou dor que ocorre durante o ato sexual, podendo ser superficial ou profunda.",
    "popular": "Dor ou queimação durante a relação sexual.",
    "clinico": "Dispareunia",
    "termos": {
        "Dor pélvica intensa e súbita": "Dor forte e repentina na pelve.",
        "Dor profunda recorrente": "Dor que ocorre repetidamente em relações.",
        "Dor superficial/queimação na entrada": "Desconforto na entrada da vagina ou pênis.",
        "Sangramento após a relação": "Sangue logo após o ato sexual.",
        "Febre": "Temperatura do corpo elevada.",
        "Corrimento com odor/desconforto": "Secreção anormal com mau cheiro.",
        "Náusea/vômitos": "Enjoo ou vômito após ou durante a relação.",
        "Atraso menstrual/possível gestação": "Menstruação atrasada ou suspeita de gravidez.",
        "Dor testicular (em homens)": "Desconforto ou dor nos testículos."
    }
},

"Daltonismo": {
    "definicao": "Alteração na percepção das cores, geralmente hereditária, podendo ser adquirida em casos raros.",
    "popular": "Dificuldade para diferenciar algumas cores.",
    "clinico": "Deficiência de percepção cromática",
    "termos": {
        "Desde a infância (sempre foi assim)": "A dificuldade para diferenciar cores existe desde pequeno.",
        "Percebi há meses/anos": "O problema começou a ser notado recentemente.",
        "Início súbito (dias/semanas)": "A dificuldade surgiu repentinamente.",
        "Um olho apenas": "A alteração é percebida somente em um olho.",
        "Ambos os olhos": "A alteração ocorre nos dois olhos.",
        "Dor ocular": "Desconforto ou dor nos olhos.",
        "Queda de acuidade visual": "Visão embaçada ou menos nítida.",
        "Fotofobia": "Sensibilidade excessiva à luz.",
        "Cefaleia": "Dor de cabeça.",
        "Olho vermelho": "Olho com vermelhidão visível."
    }
},
"Delírio ou alucinações": {
    "definicao": "Percepção de coisas irreais ou crenças falsas, podendo estar associada a condições neurológicas, psiquiátricas ou intoxicações.",
    "popular": "Está vendo ou ouvindo coisas que não existem ou acreditando em coisas que não são reais.",
    "clinico": "Psicose / Estado confusional agudo",
    "termos": {
        "Início súbito nas últimas 24h": "Os sintomas apareceram de repente, em menos de um dia.",
        "Progressivo há dias/semanas": "Os sintomas foram piorando ao longo de dias ou semanas.",
        "Agitação intensa/violência": "A pessoa está muito agitada ou agressiva.",
        "Ansiedade/agitação moderada": "A pessoa está inquieta, mas controlável.",
        "Calmo/cooperativo": "A pessoa está tranquila e colaborativa.",
        "Febre alta": "Temperatura corporal muito elevada.",
        "Rigidez na nuca": "Dificuldade ou dor para flexionar o pescoço.",
        "Cefaleia intensa": "Dor de cabeça forte.",
        "Confusão/desorientação": "Não sabe onde está, que dia é ou quem são as pessoas ao redor.",
        "Uso recente de álcool/drogas ou abstinência": "Início dos sintomas após consumo ou suspensão de álcool ou drogas.",
        "Idoso (>65 anos) ou criança": "Idade de maior risco para complicações."
    }
},

"Perda de memória": {
    "definicao": "Dificuldade em recordar informações recentes ou passadas, podendo ser súbita ou progressiva.",
    "popular": "Está esquecendo fatos importantes ou recentes.",
    "clinico": "Amnésia",
    "termos": {
        "Súbita recente (horas/dias)": "Perda de memória que começou de repente, em horas ou dias.",
        "Progressiva (semanas/meses)": "Perda de memória que vem piorando com o tempo.",
        "Eventual/esquecimentos leves": "Esquece coisas pequenas ocasionalmente.",
        "Fraqueza/queda de força em um lado": "Diminuição súbita de força em um lado do corpo.",
        "Alteração na fala": "Fala enrolada ou dificuldade para se expressar.",
        "Alteração visual súbita": "Perda ou mudança repentina na visão.",
        "Cefaleia intensa/pior da vida": "Dor de cabeça muito forte.",
        "Convulsão": "Episódios de movimentos involuntários e perda de consciência.",
        "Trauma craniano recente": "Bateu a cabeça recentemente.",
        "Uso de sedativos/álcool": "Consumo de medicamentos ou substâncias que afetam o sistema nervoso.",
        "Febre": "Temperatura corporal elevada.",
        "Idoso (>65 anos)": "Idade avançada, fator de risco para comprometimento cognitivo.",
        "Doenças prévias (hipotireoidismo, depressão)": "Histórico de doenças que podem afetar a memória."
    }
},

"Insônia": {
    "definicao": "Dificuldade para iniciar ou manter o sono, ou acordar muito cedo, com prejuízo na qualidade de vida.",
    "popular": "Não consegue dormir direito ou demora muito para pegar no sono.",
    "clinico": "Insônia",
    "termos": {
        "Há menos de 1 semana": "Os problemas de sono começaram há poucos dias.",
        "Entre 1–4 semanas": "A dificuldade de dormir dura entre uma e quatro semanas.",
        "Há mais de 1 mês": "A dificuldade de dormir dura há mais de um mês.",
        "Incapaz de trabalhar/estudar/dirigir": "A insônia está afetando atividades essenciais.",
        "Prejuízo moderado no dia a dia": "A insônia atrapalha, mas não impede totalmente as atividades.",
        "Leve/sem grande impacto": "A insônia não interfere muito na rotina.",
        "Ideação suicida": "Pensamentos sobre se machucar ou tirar a própria vida.",
        "Humor elevado/energia excessiva (mania)": "Período de muita energia e pouca necessidade de sono.",
        "Ansiedade intensa/pânico": "Sensação de nervosismo extremo ou ataques de pânico.",
        "Apneia suspeita (ronco/pausas respiratórias)": "Indícios de interrupções da respiração durante o sono.",
        "Dor crônica": "Dor persistente por semanas ou meses.",
        "Uso de estimulantes (cafeína/anfetaminas)": "Consumo de substâncias que atrapalham o sono."
    }
},

"Sonolência excessiva": {
    "definicao": "Necessidade anormal de dormir durante o dia, mesmo após sono noturno adequado.",
    "popular": "Sente muito sono durante o dia, mesmo dormindo à noite.",
    "clinico": "Hipersonia",
    "termos": {
        "Dorme durante conversas/dirigindo": "Adormece em situações ativas ou perigosas.",
        "Adormece em atividades passivas": "Pega no sono em momentos de inatividade.",
        "Apenas cansaço ao longo do dia": "Sente-se cansado, mas sem dormir involuntariamente.",
        "Súbito nas últimas 24–48h": "O sono excessivo começou de repente nos últimos dois dias.",
        "Progressivo (semanas/meses)": "A sonolência vem aumentando ao longo do tempo.",
        "Confusão/desorientação": "Fica desorientado ou confuso junto com o sono excessivo.",
        "Cefaleia matinal": "Acorda com dor de cabeça.",
        "Ronco alto/pausas respiratórias (apneia)": "Indícios de apneia do sono.",
        "Uso de sedativos/álcool": "Consumo de substâncias que causam sonolência.",
        "Febre": "Temperatura corporal elevada.",
        "Fraqueza/déficit focal": "Perda de força ou função em parte do corpo."
    }
},

"Aumento súbito de sede ou fome": {
    "definicao": "Sensação repentina e persistente de sede intensa ou fome excessiva, podendo indicar alterações metabólicas.",
    "popular": "De repente começou a sentir muita sede ou muita fome.",
    "clinico": "Polidipsia / Polifagia de início súbito",
    "termos": {
        "Urina em excesso (poliúria) e à noite": "Urina em grande quantidade, inclusive durante a madrugada.",
        "Leve aumento da frequência": "Vai ao banheiro um pouco mais que o normal.",
        "Sem mudanças": "Frequência urinária normal.",
        "Perda >5% em 1 mês": "Perdeu muito peso em pouco tempo.",
        "Perda leve (<5%)": "Emagreceu um pouco.",
        "Náusea/vômitos": "Enjoo ou vômito.",
        "Respiração rápida/cheiro de frutas (suspeita de cetoacidose)": "Respiração acelerada com hálito adocicado.",
        "Visão turva": "Enxergando de forma embaçada.",
        "Tremor/sudorese/confusão (hipoglicemia)": "Tremores, suor frio e confusão mental.",
        "Infecção recente (febre/infecção urinária/pele)": "Doença ou infecção recente."
    }
},
        

    "Inchaço dos linfonodos": {
        "definicao": "Aumento anormal dos gânglios linfáticos, geralmente como resposta a infecções ou inflamações.",
        "popular": "Gânglios inchados, como caroços no pescoço, axila ou virilha, que podem doer e vir com febre.",
        "clinico": "Linfadenopatia",
        "termos": {
        "Linfonodo(gânglio linfático)": "“Carocinho” do sistema de defesa; pode inchar em infecções e, raramente, por outras doenças.",
        "Generalizado x Localizado": "Generalizado = em várias partes do corpo; localizado = só numa região.",
        "Consistência (duro, borrachoso, macio)": "Como o nódulo/linfonodo se sente ao toque. Duro/fixo preocupa mais que móvel/borrachoso.",
        "Fixo x Móvel": "Fixo não “desliza” na pele quando você empurra; móvel se desloca com facilidade.",
        "Vermelhidão/calor (sinais inflamatórios)": "Pele vermelha e quente sobre a área, típico de inflamação/infecção.",
        "Febre baixa x alta": "Baixa ~37,8–38,4 °C; alta ≥38,5 °C.",
        "Perda de peso >10% em 6 meses": "Emagrecer sem querer mais de 10% do peso no período (ex.: de 70 kg para <63 kg).",
        "Prurido": "Coceira no corpo.",
        "Imunossupressão": "Sistema de defesa “mais fraco” por doença (ex.: HIV) ou remédios (corticoide, quimioterapia).",
        "Corticoide/Quimioterapia": "Remédios que reduzem a inflamação ou tratam câncer, mas também diminuem a imunidade.",
            
        }
    },

"Nódulo na mama": {
    "definicao": "Presença de massa ou caroço na mama, que pode ser benigno ou sinal de câncer.",
    "popular": "Caroço no seio que pode doer ou crescer, às vezes sai líquido.",
    "clinico": "Nódulo mamário",
    "termos": {
        "Retração da pele / “casca de laranja”": "Afundamento/repuxamento da pele ou porinhos aparentes, lembrando casca de laranja.",
        "Secreção mamilar": "Saída de líquido pelo mamilo. Com sangue preocupa mais; leitosa fora da amamentação também merece avaliação.",
        "Alteração do mamilo (inversão/ferida)": "Mamilo “entra” de repente ou apresenta machucado/ferida.",
        "Nódulo axilar do mesmo lado": "Caroço na axila do lado da mama com nódulo (linfonodo aumentado).",
        "Assimetria súbita da mama": "Uma única mama aumenta ou muda o formato rapidamente",
        "Dor não cíclica": "Dor que não acompanha o ciclo menstrual"
        }
    },

"Nódulo testicular": {
    "definicao": "Presença de caroço ou massa em um dos testículos, podendo ser indolor e progressivo.",
    "popular": "Caroço no saco, geralmente sem dor, que pode crescer com o tempo.",
    "clinico": "Massa testicular",
    "termos": {
        "Escroto": "Bolsa de pele que envolve os testículos",
        "Endurecimento de parte do testículo": "Área mais rígida ao toque,diferente do resto",
        "Aumento rápido do volume testicular": "Crescimento perceptível em dias/semanas",
        "Sensação de peso no escroto": "Peso/desconforto 'puxando' pra baixo",
        "Dor surda em baixo-ventre/virilha": "Dor incômoda NÃO AGUDA,na parte de baixo da barriga",
        "Aumento de mamas/sensibilidade mamilar": "Crescimento do tecido mamário do homem ou dor ao toque",
        "Criptorquidia (Testículo não descido)": "Quando, na infância, o testículo não desceu para o escroto (fator de risco na vida adulta)"
        }
    },

"Dor nos testículos": {
    "definicao": "Dor localizada em um ou ambos os testículos, podendo ser sinal de urgência médica.",
    "popular": "Dor nas bolas, que pode ser leve ou muito forte, às vezes de repente.",
    "clinico": "Orquialgia",
    "termos": {
            "Início súbito, forte, há menos de 6 horas": "Dor que começou de repente e muito forte nas últimas horas (sugere torção).",
            "Inchaço visível": "Aumento do volume visível do testículo ou escroto.",
            "Vermelhidão ou calor no escroto": "Pele avermelhada e quente sobre os testículos, sinal de inflamação.",
            "Náusea ou vômito junto da dor": "Enjoo ou vômitos ocorrendo junto com a Dor nos testículos.",
            "Criptorquidia (testículo não descido)": "Testículo que não desceu para o escroto na infância, aumenta riscos.",
            "Infecção urinária recente": "Infecção de urina nos últimos dias/semanas que pode inflamar estruturas próximas."
        }
    },

"Secreção mamilar (fora da amamentação)": {
    "definicao": "Saída de líquido pelo mamilo quando a pessoa não está amamentando.",
    "popular": "Sai leite ou outro líquido do peito mesmo sem estar grávida ou amamentando.",
    "clinico": "Galactorreia / secreção mamilar anormal",
    "termos": {
            "Transparente ou leitosa (fora da amamentação)": "Secreção clara ou leitosa que surge quando a pessoa não está amamentando",
            "Amarelada ou esverdeada": "Secreção com coloração sugestiva de pus ou infecção",
            "Aquosa clara": "Secreção semelhante à água, sem cor ou cheiro marcante",
            "Contínua ou espontânea (sem apertar)": "Secreção que sai sozinha, sem necessidade de compressão da mama",
            "Apenas quando comprimida": "Secreção que aparece somente ao apertar a mama ou o mamilo",
            "Retração do mamilo": "Quando o mamilo passa a ficar para dentro de forma repentina ou incomum",
            "Ferida ou crosta no mamilo": "Lesão ou formação de crosta na pele do mamilo",
            "Nódulo palpável na mama": "Caroço sentido ao toque durante a palpação da mama"
            }
        },

"Sangue no sêmen": {
    "definicao": "Presença de sangue visível no esperma, podendo ter várias causas.",
    "popular": "Esperma sai com sangue, cor rosa ou marrom.",
    "clinico": "Hemospermia",
    "termos": {
            "Em vários episódios recentes": "Apareceu sangue no sêmen repetidas vezes em pouco tempo.",
            "Após trauma ou procedimento urológico recente": "Depois de pancada, biópsia, vasectomia ou manipulação urológica.",
            "Dor ao ejacular": "Dor que aparece durante a ejaculação.",
            "Sangue na urina": "Urina com sangue visível (vermelha ou escura)."
            }
        },

"Febre em lactente": {
    "definicao": "Temperatura corporal elevada em bebês pequenos, que pode indicar infecção séria.",
    "popular": "Quando o bebê fica com febre alta por muito tempo, não quer mamar e parece muito molinho.",
    "clinico": "Febre persistente em lactente",
    "termos": {
        "Febre alta persistente com prostração ou recusa alimentar": "Febre que não baixa e o bebê fica fraco ou não quer mamar.",
        "Responde a estímulos": "Mesmo doente, reage ao toque ou à voz.",
        "Comportamento preservado": "Mesmo com febre, o bebê age como de costume, sorri ou interage."
        }
    },

"Choro persistente": {
    "definicao": "Choro prolongado e fora do padrão habitual da criança, sem causa clara.",
    "popular": "Quando o bebê ou criança chora muito, sem parar, e nada faz melhorar — diferente do choro normal.",
    "clinico": "Choro inconsolável",
    "termos": {
        "Choro inconsolável": "Nada faz o choro parar — nem colo, comida, carinho.",
        "Diferente do habitual": "O jeito de chorar está estranho, mais alto, irritado ou com pausas diferentes."
        }
    },

"Icterícia neonatal": {
    "definicao": "Coloração amarelada da pele em recém-nascidos, geralmente nos primeiros dias de vida.",
    "popular": "Quando o bebê fica amarelinho, principalmente no rosto e barriga. Às vezes pode estar mais sonolento.",
    "clinico": "Icterícia em recém-nascidos",
    "termos": {
        "Sonolência excessiva": "O bebê dorme demais, mais do que o normal.",
        "Amarelado moderado até o abdome": "A cor amarelada desce do rosto até a barriga.",
        "Melhora espontânea": "O amarelado melhora sozinho, sem tratamento."
        }
    },

"Queda em criança": {
    "definicao": "Acidente com impacto físico, como tombos, que pode causar machucados leves ou preocupantes.",
    "popular": "Quando a criança cai, bate a cabeça ou o corpo, e depois age diferente ou fica com hematoma.",
    "clinico": "Trauma leve ou moderado em pediatria",
    "termos": {
        "Perda de consciência": "A criança desmaiou ou ficou desacordada por alguns segundos.",
        "Convulsão": "Movimentos involuntários do corpo ou rigidez, com olhar parado ou perda de consciência.",
        "Vômitos repetidos": "Vomitou várias vezes seguidas após a queda.",
        "Sangue/fluido saindo do ouvido ou nariz": "Saída de sangue ou líquido claro depois da batida.",
        "Muito sonolenta/confusa": "Dorme demais, está lenta ou diferente do habitual."
        }
    },

"Vômito em criança": {
    "definicao": "Expulsão do conteúdo do estômago pela boca, podendo ocorrer em jato e várias vezes.",
    "popular": "Quando a criança vomita com força, várias vezes, e parece estar desidratando.",
    "clinico": "Vômitos persistentes em pediatria",
    "termos": {
        "Mais de 5 vezes em 6h": "Vomitou muitas vezes num curto período.",
        "Com sangue ou verde-escuro": "Vômito vermelho/escuro (sangue) ou verde (bile).",
        "Com muco ou restos alimentares": "Vômito com catarro/ranho ou pedaços de comida.",
        "Apenas líquido claro": "Vômito transparente, parecido com água.",
        "Febre alta": "Temperatura geralmente acima de 38,5°C.",
        "Letargia/confusão": "Muito mole/sonolenta ou sem reagir direito.",
        "Dificuldade para beber líquidos": "Recusa água/soro ou vomita logo após tentar beber."
        }
    },

"Diarreia em criança": {
    "definicao": "Evacuações frequentes e líquidas, que podem causar desidratação.",
    "popular": "Quando a criança faz cocô mole várias vezes ao dia e começa a mostrar sinais de que está desidratada.",
    "clinico": "Diarreia aguda pediátrica",
    "termos": {
        "Mais de 5 dias": "Diarreia que não melhora depois de vários dias.",
        "Com sangue ou pretas": "Fezes com sangue visível ou muito escuras (tipo borra de café).",
        "Muito aquosas": "Fezes líquidas, como água.",
        "Febre alta": "Temperatura geralmente acima de 38,5°C.",
        "Letargia/confusão": "Muito mole/sonolenta ou sem reagir direito.",
        "Boca seca ou olhos fundos": "Sinais de desidratação: sem saliva, poucas lágrimas, olhos afundados."
        }
    },

"Sensibilidade à luz ou som": {
    "definicao": "Maior incômodo causado por barulhos ou luz, mesmo que não sejam intensos.",
    "popular": "Quando a luz ou o som começa a incomodar mais do que o normal — dá dor de cabeça, irritação ou mal-estar.",
    "clinico": "Fotofobia ou fonofobia",
    "termos": {
        "Sensibilidade intensa com dor de cabeça e náusea": "Luz ou barulho incomodam muito, junto com dor de cabeça e enjoo.",
        "Incômodo moderado que piora em ambientes claros ou barulhentos": "Luz ou barulho incomodam de forma moderada.",
        "Leve desconforto ao sair no sol ou ouvir sons agudos": "Luz ou som incomodam só um pouco.",
        "Sensação leve e eventual": "Luz ou som incomodam raramente e de leve."
        }
    },

"Dor no ouvido": {
    "definicao": "Dor localizada dentro do ouvido, podendo estar acompanhada de secreção ou zumbido.",
    "popular": "Quando o ouvido dói, sai alguma coisa de dentro, faz barulho estranho ou não melhora com remédio.",
    "clinico": "Otalgia",
    "termos": {
        "Dor intensa com febre ou secreção purulenta": "Ouvido dói muito e tem febre ou sai pus.",
        "Dor forte e contínua, sem melhora com analgésico": "Ouvido dói bastante e não melhora com remédio.",
        "Dor leve com coceira ou zumbido": "Ouvido incomoda um pouco, coça ou apita.",
        "Desconforto discreto que vai e volta": "Incomoda de leve e só de vez em quando."
        }
    },

"Alterações na fala": {
    "definicao": "Mudança na forma de falar, que pode ficar lenta, confusa ou arrastada.",
    "popular": "Quando a pessoa começa a falar estranho, enrolado ou muito devagar, como se tivesse bêbada ou confusa.",
    "clinico": "Disartria ou afasia",
    "termos": {
        "Perda súbita da fala ou fala arrastada": "De repente não consegue falar direito ou fala enrolado.",
        "Dificuldade de encontrar palavras ou formar frases": "Quer falar, mas não consegue achar as palavras.",
        "Fala lenta ou confusa, mas consegue se expressar": "Fala mais devagar ou meio confuso, mas ainda dá pra entender.",
        "Leve hesitação, mas sem prejuízo da comunicação": "Às vezes trava um pouco para falar, mas nada grave."
        }
    },

"Alterações visuais súbitas": {
    "definicao": "Mudança repentina na forma de enxergar, com visão turva, dupla ou embaçada.",
    "popular": "Quando a vista escurece, dobra ou embaça do nada, dificultando enxergar mesmo por pouco tempo.",
    "clinico": "Alteração visual aguda",
    "termos": {
        "Perda súbita da visão ou visão muito turva de um lado": "Pode indicar AVC, descolamento de retina ou oclusão arterial ocular.",
        "Visão dupla ou embaçada com dor de cabeça ou náusea": "Sugere aumento de pressão intracraniana ou distúrbio neurológico.",
        "Leve embaçamento ou dificuldade temporária pra focar": "Geralmente fadiga ocular ou alteração momentânea da visão.",
        "Cansaço visual leve, sem perda ou dor": "Sintoma leve e não relacionado a doenças graves."
        }
    },

"Queimação no peito": {
    "definicao": "Sensação de ardência ou calor no peito, geralmente após alimentação.",
    "popular": "Aquela sensação de fogo no meio do peito, que piora depois de comer ou deitar.",
    "clinico": "Refluxo gastroesofágico ou dispepsia",
    "termos": {
        "Queimação forte com náusea ou suor frio": "Ardência muito forte no peito, junto de enjoo ou suor frio.",
        "Desconforto moderado que piora ao deitar": "Ardência média no peito que piora quando deita.",
        "Ardência leve após comer alimentos pesados": "Ardência leve depois de comer muito ou comida pesada.",
        "Sensação leve, ocasional, sem outros sintomas": "Ardência fraca que aparece de vez em quando."
        }
    },

"Coceira na pele": {
    "definicao": "Sensação que provoca vontade de coçar, podendo estar associada a lesões.",
    "popular": "Quando a pele começa a coçar muito, com ou sem manchas vermelhas. Às vezes não passa nem com creme ou banho.",
    "clinico": "Prurido cutâneo",
    "termos": {
        "Coceira intensa com placas vermelhas e inchaço": "Coça muito e a pele fica vermelha e inchada.",
        "Coceira forte que não alivia, atrapalha o sono": "Coça tanto que não consegue dormir.",
        "Coceira moderada e localizada": "Coça um pouco e só em um lugar.",
        "Coceira leve, passageira": "Coça levemente e passa rápido."
        }
    },

"Sangramento nasal": {
    "definicao": "Saída de sangue pelas narinas, geralmente por rompimento de pequenos vasos.",
    "popular": "Quando o nariz começa a sangrar, às vezes do nada ou após espirrar forte.",
    "clinico": "Epistaxe",
    "termos": {
        "Pressão direta": "Usa os dedos ou pano pra estancar o sangue.",
        "Após esforço ou espirro": "O sangramento começou depois de fazer força ou espirrar."
        }
    },

"Inchaço nos olhos ou face": {
    "definicao": "Aumento de volume em regiões da face, especialmente ao redor dos olhos.",
    "popular": "Quando o rosto incha, principalmente os olhos, por alergia, pancada ou infecção.",
    "clinico": "Edema facial ou periorbitário",
    "termos": {
        "Inchaço com dor intensa, febre ou fechamento dos olhos": "Inchaço forte ao redor dos olhos, com dor intensa, febre ou fechamento das pálpebras.",
        "Inchaço moderado com vermelhidão e coceira": "Inchaço médio no rosto ou olhos, com vermelhidão e coceira.",
        "Inchaço leve sem dor, após alergia ou trauma": "Leve inchaço sem dor, causado por alergia ou pancada.",
        "Inchaço pequeno e passageiro": "Pequeno inchaço que some rapidamente."
        }
    },

"Ansiedade ou agitação intensas": {
    "definicao": "Estado de excitação ou preocupação extrema, com sintomas físicos ou comportamentais.",
    "popular": "Quando a pessoa fica muito agitada, com o coração disparado, falta de ar, tremores ou até ideias confusas.",
    "clinico": "Crise de ansiedade ou agitação psicomotora",
    "termos": {
        "Agitação extrema com risco de autoagressão ou agressividade": "Comportamento muito agitado e perigoso, com risco de machucar a si mesmo ou outros.",
        "Crise intensa com falta de ar, tremores ou choro incontrolável": "Crise de ansiedade forte, com sintomas físicos como falta de ar, tremores ou choro que não para.",
        "Ansiedade moderada com pensamentos acelerados": "Estado de ansiedade com pensamentos rápidos e dificuldade para relaxar.",
        "Sensação leve de nervosismo ou tensão": "Pequeno nervosismo que não impede as atividades do dia a dia."
        }
    },

"Alterações urinárias": {
    "definicao": "Mudança na frequência, volume ou capacidade de urinar.",
    "popular": "Quando vai ao banheiro muitas vezes ou simplesmente não consegue fazer xixi, mesmo com vontade.",
    "clinico": "Disúria, poliúria ou retenção",
    "termos": {
        "Urina com sangue": "Urina avermelhada/rosada ou com coágulos visíveis.",
        "Incapacidade de urinar": "Vontade de urinar, mas nada sai.",
        "Urina turva e com odor forte": "Urina “espessa”, amarelada e com cheiro forte.",
        "Cateter vesical": "Tubo usado para drenar a urina.",
        "Dor nas costas (lado dos rins)": "Dor na parte de trás, na altura da cintura, de um lado."
        }
    },

"Corpo estranho nos olhos, ouvidos ou nariz": {
    "definicao": "Entrada de objeto ou substância em cavidades sensoriais, com ou sem sintomas.",
    "popular": "Quando algo entra no olho, nariz ou ouvido — como sujeira, grão ou inseto — e pode causar dor, secreção ou febre.",
    "clinico": "Presença de corpo estranho em cavidade sensorial",
    "termos": {
        "Dor intensa ou secreção com febre": "Possível infecção grave causada pelo corpo estranho.",
        "Desconforto moderado e persistente": "Corpo estranho em local sensível que não saiu espontaneamente.",
        "Leve irritação, sem dor ou sinais de infecção": "Irritação leve causada por contato com corpo estranho.",
        "Presença confirmada, mas sem sintomas": "Objeto visível, mas sem causar inflamação ou dor."
        }
    },

"Ferimentos ou cortes com objetos": {
    "definicao": "Lesão na pele causada por faca, vidro, objetos pontiagudos ou cortantes.",
    "popular": "Quando a pessoa se corta com algo e o ferimento pode ser leve ou profundo, com risco de infecção.",
    "clinico": "Laceração ou corte",
    "termos": {
        "Corte profundo com sangramento intenso e exposição de tecidos": "Ferimento grave com risco de hemorragia e infecção.",
        "Ferida moderada com sangramento que demora a parar": "Sangramento persistente, com necessidade de cuidados médicos.",
        "Ferida pequena, mas com sinais de infecção (pus, vermelhidão)": "Infecção localizada que requer tratamento.",
        "Corte leve, limpo e controlado": "Ferimento superficial de baixa gravidade."
        }
    },

"Engasgo ou obstrução das vias aéreas": {
    "definicao": "Dificuldade de respirar causada por algo bloqueando a passagem do ar.",
    "popular": "Quando algo entala e a pessoa não consegue respirar direito, nem tossir com força.",
    "clinico": "Obstrução das vias aéreas superiores",
    "termos": {
        "Engasgo com tosse ineficaz, lábios roxos ou dificuldade extrema": "Obstrução grave das vias aéreas, risco de asfixia.",
        "Tosse persistente com respiração ofegante": "Obstrução parcial das vias aéreas ou irritação intensa.",
        "Tossiu, mas respira normalmente agora": "Situação controlada, sem risco imediato.",
        "Episódio leve e isolado, sem sinais atuais": "Engasgo leve, resolvido sem complicações."
        }
    },

"Sinais de intoxicação ou envenenamento": {
    "definicao": "Efeitos provocados por substâncias tóxicas ingeridas, inaladas ou em contato com a pele.",
    "popular": "Quando a pessoa bebe, come ou entra em contato com algo que pode fazer mal, como produto de limpeza ou veneno.",
    "clinico": "Intoxicação exógena",
    "termos": {
        "Ingestão de substância tóxica com confusão, vômito ou inconsciência": "Indica intoxicação grave, com risco de depressão neurológica ou falência de órgãos.",
        "Ingestão suspeita com sintomas moderados (náusea, tontura)": "Sugere intoxicação moderada, possivelmente em fase inicial.",
        "Ingestão leve com sintomas leves (enjoo leve, dor de barriga)": "Quadro leve e autolimitado, possivelmente por ingestão de pequena quantidade.",
        "Ingestão pequena com sintomas ausentes ou mínimos": "Baixa probabilidade de complicações, mas requer observação."
        }
    },

    "Retenção urinária": {
    "definicao": "Dificuldade ou incapacidade de urinar completamente, mesmo com sensação de bexiga cheia.",
    "popular": "Quando a pessoa sente vontade de fazer xixi, mas não consegue ou sai só um pouco, mesmo com a bexiga cheia.",
    "clinico": "Retenção urinária aguda ou crônica",
    "termos": {
        "Retenção urinária": "Quando sente vontade de urinar mas não consegue.",
        "Jato fraco": "Quando o xixi sai com pouca força.",
        "Distensão abdominal": "Barriga estufada por acúmulo de urina."
        }
    },

"Tremores ou movimentos involuntários": {
    "definicao": "Movimentos que o corpo faz sozinho, sem controle consciente, podendo ser leves ou fortes.",
    "popular": "Quando a mão ou o corpo começa a tremer sem motivo ou faz movimentos esquisitos sozinho, sem conseguir parar.",
    "clinico": "Movimentos involuntários ou tremores",
    "termos": {
        "Tremores": "Movimentos involuntários do corpo, geralmente nas mãos.",
        "Espasmos": "Contrações rápidas e fora de controle dos músculos.",
        "Rigidez muscular": "Quando o músculo fica duro e difícil de mexer."
        }
    },

"Dificuldade pra engolir": {
    "definicao": "Sensação de que a comida ou líquido não desce corretamente pela garganta.",
    "popular": "Quando engolir água ou comida parece difícil ou incômodo, como se algo estivesse travando na garganta.",
    "clinico": "Disfagia",
    "termos": {
        "Disfagia": "Quando é difícil engolir comida ou bebida.",
        "Sensação de entalo": "Sensação de que o alimento está preso na garganta.",
        "Dor ao engolir": "Ardência ou dor durante a deglutição."
        }
    },

"Icterícia": {
    "definicao": "Cor amarelada na pele e nos olhos, geralmente causada por problemas no fígado.",
    "popular": "Quando a pele ou os olhos da pessoa ficam amarelos, mesmo que levemente. É comum em recém-nascidos ou problemas no fígado.",
    "clinico": "Icterícia",
    "termos": {
        "Icterícia": "Pele e olhos com tom amarelado.",
        "Bilirrubina": "Substância do sangue que, quando acumulada, deixa a pele amarela.",
        "Colestase": "Bloqueio no caminho da bile, líquido que ajuda na digestão."
        }
    },

"Corpo estranho na garganta": {
    "definicao": "Sensação ou presença real de algo preso na garganta.",
    "popular": "Quando parece que tem algo entalado na garganta — um pedaço de comida, espinha de peixe ou qualquer coisa — e a pessoa sente incômodo ao engolir.",
    "clinico": "Obstrução faríngea leve",
    "termos": {
        "Obstrução": "Algo bloqueando a passagem de ar ou comida.",
        "Engasgo": "Quando algo entra no caminho errado e atrapalha a respiração.",
        "Aspiração": "Quando um objeto ou alimento vai para os pulmões por engano."
        }
    },

"Sangramento gastrointestinal": {
    "definicao": "Presença de sangue na evacuação ou vômito, geralmente indicando sangramento interno.",
    "popular": "Quando sai sangue pelo vômito ou pelas fezes, o que pode assustar e indicar problema no estômago ou intestino.",
    "clinico": "Hemorragia digestiva",
    "termos": {
        "Fezes escuras": "Fezes pretas ou com cor de piche, indicando sangue digerido.",
        "Vômito com sangue": "Quando o vômito sai com sangue vermelho vivo ou escuro.",
        "Hematêmese": "Nome técnico para vômito com sangue."
        }
    },

"Dor no ombro ou braço": {
    "definicao": "Dor localizada ou que se espalha entre o ombro e o braço, podendo indicar lesão ou outro problema.",
    "popular": "Quando o ombro ou o braço doem, formigam ou não se mexem direito, com dor que pode ir do pescoço até os dedos.",
    "clinico": "Dor irradiada ou lesão músculo-esquelética",
    "termos": {
        "Irradiação": "Quando a dor começa em um lugar e se espalha para outro.",
        "Dormência": "Sensação de formigamento ou falta de sensibilidade.",
        "Fraqueza muscular": "Quando o braço ou ombro perdem força para segurar ou levantar objetos."
        }
    },

"Náusea ou enjoo": {
    "definicao": "Sensação de mal-estar no estômago, com ou sem vontade de vomitar.",
    "popular": "Quando bate aquele enjoo, como se fosse vomitar ou estivesse com o estômago revirado.",
    "clinico": "Náusea",
    "termos": {
        "Náusea": "Sensação de que vai vomitar, mesmo sem chegar a vomitar.",
        "Enjoo": "Desconforto no estômago, como se estivesse 'embrulhado'.",
        "Vômito persistente": "Quando vomita várias vezes e não consegue segurar líquidos ou comida."
        }
    },

"Dor na perna e dificuldade pra caminhar": {
    "definicao": "Dor nas pernas associada à limitação nos movimentos ou dificuldade ao andar.",
    "popular": "Quando andar fica difícil por causa da dor ou fraqueza nas pernas, podendo até causar queda.",
    "clinico": "Claudicação ou limitação motora",
    "termos": {
        "Dor súbita com inchaço, vermelhidão ou dificuldade de mover a perna": "Possível trombose venosa profunda ou lesão grave, com sinais de comprometimento vascular.",
        "Dor intensa após queda ou lesão recente": "Sugere fratura, luxação ou lesão musculoesquelética importante.",
        "Dor moderada, persistente, mas ainda consegue caminhar": "Pode ser lesão muscular ou articular leve a moderada.",
        "Dor leve e passageira, sem sinais visíveis": "Sintoma autolimitado, geralmente por esforço ou postura inadequada."
        }
    },

"Dores no pescoço ou rigidez da nuca": {
    "definicao": "Dor localizada na região cervical ou dificuldade de movimentar o pescoço normalmente.",
    "popular": "Quando o pescoço fica duro, dolorido e difícil de mexer, como se tivesse travado ou dormido de mau jeito.",
    "clinico": "Rigidez cervical ou torcicolo",
    "termos": {
        "Dor intensa com febre, vômito ou confusão": "Pode indicar meningite ou infecção grave do sistema nervoso.",
        "Rigidez importante com dor de cabeça forte": "Sinal de possível meningite ou comprometimento neurológico.",
        "Dor moderada após esforço físico ou posição ruim": "Sugere causa muscular ou postural.",
        "Dor leve e localizada, sem outros sintomas": "Desconforto localizado, geralmente de origem benigna."
        }
    },

    "Comportamento estranho à normalidade": {
    "definicao": "Mudanças repentinas no modo como a pessoa age, pensa ou se comunica.",
    "popular": "Quando a pessoa começa a agir de forma esquisita do nada — vê coisas que não existem, parece confusa, fala coisas desconexas ou fica estranhamente calma ou agitada.",
    "clinico": "Alteração aguda de comportamento",
    "termos": {
        "Alucinação": "Vê/ouve coisas que não estão ali.",
        "Rigidez na nuca": "Pescoço duro, difícil encostar o queixo no peito.",
        "Imunossupressão": "Defesas do corpo enfraquecidas por doença/medicamento."
        }
    },

"Sangramento ativo": {
    "definicao": "Perda visível de sangue que ainda está acontecendo, por corte, lesão ou outra causa.",
    "popular": "Quando a pessoa está sangrando de verdade — seja pouco ou muito — e ainda não parou totalmente.",
    "clinico": "Hemorragia ativa",
    "termos": {
        "Palidez/pele fria": "Pessoa fica muito branca e gelada ao toque.",
        "Batimento muito acelerado": "Coração disparado mesmo em repouso.",
        "Uso de anticoagulante": "Remédios que afinam o sangue e aumentam sangramento."
        }
    },

"Alergia cutânea": {
    "definicao": "Reação alérgica que afeta a pele, causando coceira, vermelhidão ou descamação.",
    "popular": "Quando a pele fica irritada, coçando, com manchas vermelhas ou até sem sintomas, mas com aspecto diferente.",
    "clinico": "Dermatite alérgica",
    "termos": {
        "Urticária": "Placas vermelhas na pele que coçam muito.",
        "Erupção": "Aparecimento repentino de manchas ou bolinhas na pele.",
        "Edema": "Inchaço em alguma parte do corpo."
        }
    },

"Reação alérgica": {
    "definicao": "Resposta do corpo a uma substância estranha, podendo causar sintomas leves ou graves.",
    "popular": "Quando o corpo reage mal a algo — como comida, remédio ou picada — e aparecem manchas vermelhas, coceira ou até sintomas no corpo todo.",
    "clinico": "Reação anafilática ou alérgica sistêmica",
    "termos": {
        "Placas vermelhas": "Manchas altas e avermelhadas que coçam (urticária).",
        "Chiado no peito": "Som de apito ao respirar.",
        "Tontura/desmaio": "Cabeça leve, visão escurecendo ou perda de consciência."
        }
    },

"Trauma ou queda": {
    "definicao": "Impacto causado por batida, pancada, acidente ou queda de altura.",
    "popular": "Quando a pessoa bate alguma parte do corpo, cai ou sofre algum acidente e sente dor ou fica inconsciente.",
    "clinico": "Traumatismo",
    "termos": {
        "Alto impacto": "Acidente de trânsito ou queda de altura.",
        "Sangramento importante que não para": "Sangue escorrendo contínuo, encharca curativo.",
        "Deformidade aparente": "Membro torto, encurtado ou com inchaço grande.",
        "Perda de consciência": "Desmaiou na hora do trauma."
        }
    },

"Infecção em ferida": {
    "definicao": "Contaminação de um machucado, com sinais de inflamação e proliferação de bactérias.",
    "popular": "Quando o machucado piora com pus, vermelhidão, inchaço ou cheiro ruim. Pode começar a doer mais do que antes.",
    "clinico": "Ferida infeccionada",
    "termos": {
        "Supuração": "Saída de pus do machucado.",
        "Inflamação": "Vermelhidão, calor e inchaço ao redor da ferida.",
        "Cicatrização": "Processo natural de fechamento do machucado."
        }
    },

"Convulsão": {
    "definicao": "Atividade elétrica anormal no cérebro que causa tremores, rigidez ou perda de consciência.",
    "popular": "Quando a pessoa começa a tremer forte, perde os sentidos ou tem uma crise de epilepsia.",
    "clinico": "Crise convulsiva",
    "termos": {
        "Convulsão > 5 min": "Crise longa, não para sozinha.",
        "Trauma na cabeça durante a crise": "Bateu a cabeça enquanto convulsionava.",
        "Uso de anticoagulante": "Remédios que “afinam” o sangue.",
        "Recuperação parcial com confusão": "Após a crise, a pessoa acorda confusa e lenta."
        }
    },

"Desmaio ou tontura": {
    "definicao": "Sensação de perda de equilíbrio ou apagão súbito, com ou sem perda de consciência.",
    "popular": "Quando a pessoa sente que vai cair, vê tudo girando ou chega a desmaiar por segundos ou minutos.",
    "clinico": "Síncope ou pré-síncope",
    "termos": {
        "Perda de consciência prolongada": "Ficou desacordado por mais tempo que um desmaio rápido.",
        "Suor frio e palidez intensa": "Suor excessivo com pele muito pálida.",
        "Arritmia": "Batimentos do coração fora do ritmo normal."
        }
    },

"Dificuldade respiratória": {
    "definicao": "Problema mecânico para puxar ou soltar o ar, com esforço visível para respirar.",
    "popular": "É diferente de só sentir falta de ar. Aqui, a pessoa parece estar 'lutando' pra respirar, com o peito subindo muito, chiado forte ou até sensação de sufocamento.",
    "clinico": "Insuficiência respiratória ou esforço respiratório aumentado",
    "termos": {
        "Lábios/pontas dos dedos roxos": "Sinal de pouco oxigênio no sangue.",
        "Súbito": "Começou de uma hora para outra.",
        "Asma/bronquite/DPOC": "Doenças que dificultam a passagem de ar."
        }
    },

"Falta de ar": {
    "definicao": "Sensação subjetiva de que o ar não está entrando o suficiente, mesmo sem esforço visível.",
    "popular": "Diferente da dificuldade respiratória, aqui a pessoa diz que não consegue puxar o ar direito, mesmo se a respiração parecer normal de fora. Pode ocorrer em crises de ansiedade ou pulmão cheio.",
    "clinico": "Dispneia subjetiva",
    "termos": {
        "Lábios ou ponta dos dedos roxos": "Cor arroxeada indicando pouco oxigênio.",
        "Chiado no peito": "Som de apito ao respirar.",
        "De repente (minutos/horas)": "Começou muito rápido, sem aviso.",
        "Asma/bronquite/DPOC": "Doenças que dificultam a passagem de ar."
        }
    },

"Lesões na pele": {
    "definicao": "Alterações visíveis na pele como manchas, bolhas, descamações ou feridas.",
    "popular": "Quando aparecem manchas vermelhas, roxas ou feridas na pele que coçam, ardem ou mudam de cor. Pode ser por alergia, infecção ou até problema de circulação.",
    "clinico": "Lesões cutâneas",
    "termos": {
        "Púrpuras": "Manchas roxas/vermelhas que não somem quando aperta.",
        "Urticária (placas)": "Carocinhos/placas altas e vermelhas que coçam.",
        "Inchaço de lábios/rosto": "Aumento rápido dessas regiões (alerta para alergia grave)."
        }
    },

"Dor ou olho vermelho": {
    "definicao": "Desconforto ocular associado a vermelhidão, ardência ou sensibilidade à luz.",
    "popular": "Quando o olho está vermelho, dói, arde ou fica sensível à luz. Pode estar seco ou soltando secreção.",
    "clinico": "Conjuntivite ou inflamação ocular",
    "termos": {
        "Trauma químico": "Produto químico entrou no olho (ex.: água sanitária).",
        "Halos ao redor da luz": "Anéis ao redor das luzes, visão embaçada.",
        "Lentes de contato": "Lentes sobre os olhos para corrigir visão/estética."
        }
    },

"Sangramento vaginal": {
    "definicao": "Perda de sangue pela vagina fora do ciclo menstrual esperado ou em volume incomum.",
    "popular": "Quando desce sangue fora da menstruação normal ou vem em grande quantidade, podendo assustar.",
    "clinico": "Sangramento uterino anormal",
    "termos": {
        "Coágulos grandes": "Pedaços de sangue espesso saindo junto do fluxo.",
        "Tontura ou desmaio": "Sensação de apagar/escurecer a visão.",
        "Fora do ciclo": "Sangramento em dias que não eram esperados."
        }
    },

"Dor ou dificuldade ao urinar": {
    "definicao": "Sensação de dor, queimação ou esforço para urinar, geralmente por infecção.",
    "popular": "Quando arde ao fazer xixi, a urina sai fraca ou vem acompanhada de dor na barriga. Pode dar vontade toda hora e sair pouco.",
    "clinico": "Disúria ou infecção urinária",
    "termos": {
        "Dor intensa com sangue na urina ou febre": "Urina com forte dor acompanhada de sangue ou febre alta.",
        "Ardência moderada com urgência e desconforto abdominal": "Sensação de queimação ao urinar, com vontade frequente e desconforto na barriga.",
        "Ardência leve ou aumento de frequência urinária": "Leve queimação ao urinar ou vontade de urinar mais vezes que o normal.",
        "Leve desconforto, sem outros sintomas": "Sensação incômoda ao urinar, mas sem dor forte ou outros sinais associados."
        }
    },

"Inchaço incomum": {
    "definicao": "Acúmulo de líquido em partes do corpo, especialmente mãos, pernas, rosto ou barriga.",
    "popular": "Quando alguma parte do corpo incha de repente, incha tudo ao mesmo tempo ou parece só um leve acúmulo de água. Pode ter várias causas.",
    "clinico": "Edema",
    "termos": {
        "Panturrilha/perna única": "Inchaço em uma perna, principalmente na batata da perna.",
        "Ganho rápido de peso": "Aumento de vários quilos em poucos dias por retenção.",
        "Pílula/terapia hormonal": "Uso de anticoncepcionais ou reposição hormonal.",
        "Imobilização": "Ficar muito tempo sem mexer a perna (gesso, viagem longa)."
        }
    },

"Hipotensão": {
    "definicao": "Pressão arterial abaixo dos níveis normais, podendo causar tontura, fraqueza ou desmaio.",
    "popular": "Quando a pressão está baixa e a pessoa fica fraca, pálida ou com sensação de desmaio.",
    "clinico": "Hipotensão arterial",
    "termos": {
        "Hipoperfusão": "Sensação de corpo fraco, pele fria e pálida, como se a energia estivesse acabando.",
        "Anafilaxia": "Reação alérgica grave com inchaço, falta de ar e vermelhidão espalhada pelo corpo."
        }
    },

"Hipoglicemia": {
    "definicao": "Queda dos níveis de açúcar no sangue, podendo causar sintomas neurológicos e físicos.",
    "popular": "Quando a glicose baixa demais, causando tremedeira, fome de repente, suor e até desmaio.",
    "clinico": "Hipoglicemia",
    "termos": {
        "Desmaio ou confusão com sudorese intensa": "Pessoa cai ou fica desorientada, suando muito.",
        "Tontura, tremores e fome súbita": "Sensação repentina de fraqueza com mãos trêmulas e muita fome.",
        "Jejum prolongado": "Ficou muitas horas sem comer.",
        "Atividade física intensa sem alimentação": "Exercício pesado sem comer antes."
        }
    },

"Hiperglicemia": {
    "definicao": "Excesso de glicose no sangue, comum em pessoas com diabetes descompensado.",
    "popular": "Quando o açúcar do sangue está alto e a pessoa sente muita sede, enjoo e mal-estar.",
    "clinico": "Hiperglicemia",
    "termos": {
        "Sede intensa, urina excessiva e cansaço extremo": "Bebe muita água, urina demais e se sente exausto.",
        "Mal-estar com enjoo e dor abdominal": "Desconforto no estômago com náusea e dor de barriga.",
        "Excesso de carboidratos": "Comeu muito açúcar ou massas recentemente."
        }
    },

"Temperatura baixa": {
    "definicao": "Redução anormal da temperatura corporal, conhecida como hipotermia.",
    "popular": "Quando o corpo esfria demais e a pessoa fica com frio, tremendo e com mãos e pés gelados.",
    "clinico": "Hipotermia",
    "termos": {
        "Extremidades frias com sonolência ou confusão": "Mãos e pés gelados junto com muito sono ou desorientação.",
        "Calafrios e pele fria persistente": "Tremores contínuos e pele gelada mesmo agasalhado.",
        "Pele arroxeada": "Tom roxo nas extremidades pelo frio."
        }
    },

"Dor durante a gravidez": {
    "definicao": "Desconforto abdominal ou pélvico em gestantes, que pode ou não indicar complicações.",
    "popular": "Quando a grávida sente dor no pé da barriga, com ou sem contrações, podendo indicar algo grave.",
    "clinico": "Dor gestacional",
    "termos": {
        "Dor intensa com sangramento ou perda de líquido": "Dor forte junto com sangue ou líquido saindo pela vagina.",
        "Diminuição ou ausência de movimentos do bebê": "Bebê mexendo pouco ou parou de mexer.",
        "Pressão alta recente": "Medição recente mostrou pressão elevada."
        }
    },

"Redução dos movimentos fetais": {
    "definicao": "Diminuição ou ausência percebida dos chutes e movimentos do bebê na barriga.",
    "popular": "Quando o bebê parece não estar mais se mexendo como antes, ou fica muito parado por horas.",
    "clinico": "Redução da movimentação fetal",
    "termos": {
        "Nenhum movimento fetal": "A grávida não sente o bebê mexer por um longo período.",
        "Redução clara": "Os movimentos diminuíram bastante em comparação aos dias anteriores.",
        "Menos ativos": "O bebê se mexe, mas de forma mais fraca ou mais rara."
        }
    },

"Trabalho de parto": {
    "definicao": "Período em que começam as contrações uterinas regulares e há dilatação para nascimento do bebê.",
    "popular": "Quando a barriga começa a endurecer e doer em intervalos regulares, como se fosse cólica forte, e a grávida sente pressão na parte de baixo.",
    "clinico": "Trabalho de parto",
    "termos": {
        "Contrações": "Dores regulares e fortes que fazem a barriga endurecer e relaxar.",
        "Pressão pélvica": "Sensação de peso ou pressão na parte íntima, como se algo estivesse empurrando."
        }
    },

    "Mordedura": {
    "definicao": "Ferimento causado por mordida de animal ou ser humano, podendo gerar infecção ou risco de doenças.",
    "popular": "Quando a pessoa é mordida e a pele fica machucada. Pode ser leve ou profunda, e em caso de cachorro ou animal desconhecido, é bom suspeitar de raiva.",
    "clinico": "Mordedura ou ferimento por mordida",
    "termos": {
        "Mordida profunda com sangramento e suspeita de raiva": "Ferimento profundo causado por mordida, com sangramento e risco de raiva.",
        "Mordida com dor e sinais de infecção": "Ferimento de mordida com dor e características de infecção (vermelhidão, calor, pus).",
        "Mordida superficial com inchaço": "Ferimento leve de mordida com pequeno aumento de volume local.",
        "Pequeno arranhão sem dor": "Lesão muito leve na pele, sem dor associada."
        }
    },

"Queimadura": {
    "definicao": "Lesão na pele ou tecidos por calor, produtos químicos, eletricidade ou radiação.",
    "popular": "Quando encosta em algo quente ou químico e a pele queima. Pode ficar vermelha, fazer bolhas ou queimar profundamente.",
    "clinico": "Queimadura térmica ou química",
    "termos": {
        "Queimadura extensa, com bolhas e pele escura": "Lesão grave que afeta área grande, com bolhas e coloração escura indicando profundidade.",
        "Queimadura moderada com bolhas e dor intensa": "Queimadura de gravidade intermediária, com bolhas e dor acentuada.",
        "Queimadura pequena com vermelhidão e dor leve": "Lesão pequena com vermelhidão e dor suportável.",
        "Apenas vermelhidão passageira sem dor": "Mancha vermelha na pele que melhora rapidamente, sem dor."
        }
    },

"Ferida não-traumática": {
    "definicao": "Ferida que surge sem pancada ou corte, geralmente por infecção, circulação ruim ou doenças de pele.",
    "popular": "Machucado que aparece sozinho, sem cair ou se bater. Pode ter pus, doer, cheirar mal ou piorar com o tempo.",
    "clinico": "Úlcera cutânea ou lesão espontânea",
    "termos": {
        "Ferida grande com secreção e mal cheiro": "Ferimento extenso, com saída de secreção e odor desagradável.",
        "Ferida dolorosa com sinais de infecção": "Ferida que apresenta dor e indícios de infecção como pus ou calor local.",
        "Ferida pequena com vermelhidão": "Lesão reduzida com área avermelhada ao redor.",
        "Apenas uma mancha sem dor ou secreção": "Alteração superficial na pele sem dor ou secreção."
        }
    },

"Gases": {
    "definicao": "Acúmulo de ar no intestino, provocando distensão e desconforto.",
    "popular": "Barriga estufada, soltando pum o tempo todo ou barulho alto no intestino. Às vezes não melhora nem depois de soltar.",
    "clinico": "Flatulência ou distensão abdominal",
    "termos": {
        "Dor abdominal intensa com inchaço e sem alívio": "Dor forte na barriga acompanhada de aumento de volume e sem melhora.",
        "Desconforto forte e barulhos intestinais altos": "Sensação desconfortável no abdômen com sons intensos vindos do intestino.",
        "Flatulência frequente com leve dor": "Eliminação de gases em excesso com dor leve.",
        "Gases leves, sem incômodo relevante": "Pequena quantidade de gases sem causar desconforto."
        }
    },

"Sangramento retal": {
    "definicao": "Presença de sangue saindo pelo ânus, geralmente visível nas fezes ou no papel higiênico.",
    "popular": "Quando sai sangue pelo ânus ao evacuar. Pode ser pouco ou muito, e o sangue geralmente é vermelho vivo.",
    "clinico": "Rectorragia",
    "termos": {
        "Sangramento intenso que não para com pressão direta": "Nariz sangrando muito e sem parar mesmo com pressão.",
        "Sangramento moderado que reaparece durante o dia": "Nariz sangra um pouco, mas volta a sangrar mais tarde no mesmo dia.",
        "Sangramento leve após esforço ou espirro": "Nariz sangra levemente depois de esforço ou espirrar.",
        "Sangramento isolado e já controlado": "Nariz sangrou uma vez e já parou."
        }
    },

"Confusão mental": {
    "definicao": "Alteração da clareza de pensamento, com dificuldade para entender, lembrar ou se orientar.",
    "popular": "Quando a pessoa começa a falar coisas sem sentido, não reconhece as pessoas, esquece onde está ou age de forma estranha.",
    "clinico": "Alteração do estado mental ou delirium",
    "termos": {
    "Desorientação completa e fala incoerente": "Pessoa não sabe onde está, que dia é ou quem são as pessoas, falando frases sem sentido.",
    "Confusão mental com dificuldade de reconhecer pessoas ou lugares": "Pessoa não reconhece familiares ou o próprio local onde está.",
        "Início súbito (minutos a horas)": "Sintomas apareceram de repente, de uma hora para outra.",
        "Instalação gradual (dias a semanas)": "Sintomas foram surgindo aos poucos, piorando com o tempo.",
        "Rigidez na nuca": "Pescoço duro e dolorido, com dificuldade para encostar o queixo no peito.",
        "Sinais focais neurológicos": "Um lado do corpo fraco, caído ou com fala enrolada.",
        "Convulsão": "Movimentos involuntários do corpo, como tremores fortes, ou rigidez com perda de consciência.",
        "Hipoglicemiantes": "Remédios para baixar açúcar no sangue, usados por pessoas com diabetes.",
        "Imunossupressão": "Defesas do corpo enfraquecidas, deixando a pessoa mais vulnerável a infecções."
        }
    },

"Perda de consciência": {
    "definicao": "Quando a pessoa deixa de responder, desmaia ou apaga, mesmo que por pouco tempo.",
    "popular": "Quando a pessoa cai ou apaga e não responde. Pode voltar sozinha depois ou precisar de ajuda.",
    "clinico": "Perda de consciência",
    "termos": {
            "Pré-síncope": "Sensação de que vai desmaiar, com visão escurecendo ou ouvido abafando, mas sem cair.",
            "Hipotensão ortostática": "Tontura ou visão turva ao se levantar rápido.",
            "Arritmia": "Sensação de coração batendo muito rápido, devagar ou fora de ritmo.",
            "Anticoagulante": "Remédio que afina o sangue, aumentando risco de sangramento."
        }
    },

"Trauma na cabeça": {
    "definicao": "Lesão na cabeça provocada por batida, queda ou impacto direto.",
    "popular": "Quando a pessoa bate a cabeça com força, em queda ou pancada. Pode ficar tonta, vomitar, esquecer o que aconteceu ou até desmaiar.",
    "clinico": "Traumatismo cranioencefálico (TCE)",
    "termos": {
        "Amnésia": "Perda parcial ou total da memória após um evento.",
        "Confusão mental": "Estado de pensamento desorganizado ou dificuldade de concentração.",
        "Alteração visual": "Mudança súbita na visão, como visão turva ou dupla.",
        "Fraqueza em braço/perna": "Diminuição da força muscular em um ou mais membros.",
        "Sonolência excessiva": "Sensação anormal de muito sono e dificuldade de manter-se acordado."
        }
    },

"Manchas anormais na pele": {
    "definicao": "Alterações na coloração da pele, como manchas vermelhas, roxas, escuras ou esbranquiçadas.",
    "popular": "Manchas que surgem na pele do nada ou após remédio, febre ou pancada. Pode coçar, doer, espalhar ou mudar de cor com o tempo.",
    "clinico": "Exantema, petéquias ou equimoses (dependendo do tipo)",
    "termos": {
        "Descamação": "Quando a pele começa a soltar pequenas placas ou pedaços.",
        "Bordas elevadas": "Margem da lesão mais alta que o nível da pele ao redor.",
        "Ferida que não cicatriza": "Lesão aberta que não fecha ou melhora após semanas.",
        "Aspecto de casca de laranja": "Textura irregular da pele, semelhante à casca de uma laranja."
        }
    },

"Incontinência urinária": {
    "definicao": "Incapacidade de segurar a urina, com perdas involuntárias.",
    "popular": "Quando a pessoa faz xixi sem querer, seja aos poucos ou tudo de uma vez, mesmo tentando segurar.",
    "clinico": "Incontinência urinária",
    "termos": {
        "Trato urinário": "Sistema formado por rins, ureteres, bexiga e uretra, responsável pela produção e eliminação da urina.",
        "Cirurgia pélvica": "Procedimento cirúrgico realizado na região inferior do abdômen.",
        "Parto vaginal múltiplo": "Dois ou mais partos realizados pela via natural.",
        "Doença neurológica": "Condição que afeta o sistema nervoso, como Parkinson ou esclerose múltipla."
        }
    },

"Coriza e espirros": {
    "definicao": "Coriza é o nariz escorrendo, e espirros são expulsões rápidas de ar pelo nariz e boca, geralmente por irritação.",
    "popular": "Nariz escorrendo sem parar, espirrando o tempo todo, com ou sem febre. Pode ser gripe, resfriado ou alergia.",
    "clinico": "Rinorreia e espirros",
    "termos": {
        "Coriza": "Corrimento nasal, geralmente por resfriado ou alergia.",
        "Espirros": "Expulsões rápidas de ar pelo nariz e boca por irritação nasal.",
        "Nariz entupido": "Sensação de bloqueio das narinas, com dificuldade de passagem de ar.",
        "Febre alta": "Temperatura geralmente ≥ 38,5°C.",
        "Falta de ar": "Sensação de ar insuficiente ao respirar.",
        "Chiado no peito": "Som agudo ao respirar, típico de asma/broncoespasmo.",
        "Secreção amarela/verde": "Catarro espesso, sugerindo infecção bacteriana.",
        "Lábios roxos": "Coloração arroxeada por baixa oxigenação.",
        "Asma": "Doença respiratória com broncoespasmo recorrente.",
        "DPOC": "Doença pulmonar obstrutiva crônica (bronquite/enfisema)."
        }
    },

"Incontinência urinária em idosos": {
    "definicao": "Perda involuntária de urina, comum na população idosa por fatores musculares, neurológicos ou medicamentos.",
    "popular": "O idoso começa a fazer xixi sem perceber ou não consegue chegar ao banheiro a tempo. Pode acontecer à noite ou durante o dia, com ou sem aviso.",
    "clinico": "Incontinência urinária senil",
    "termos": {
        "Incontinência": "Perda involuntária de urina.",
        "Dor/ardência ao urinar": "Queimação durante a micção (disúria).",
        "Cateter vesical": "Tubo colocado na bexiga para drenar urina.",
        "Imobilidade": "Dificuldade de se mover ou ficar de pé.",
        "Diurético": "Remédio que aumenta a produção de urina.",
        "Sedativo": "Medicamento que reduz ansiedade e dá sono."
        }
    },

"Queda em idosos": {
    "definicao": "Perda de equilíbrio ou escorregão que leva ao chão, com ou sem lesão.",
    "popular": "Quando o idoso cai sozinho, tropeça, escorrega ou perde a força. Pode bater a cabeça, quebrar ossos ou ficar muito assustado.",
    "clinico": "Queda de altura do próprio corpo",
    "termos": {
        "Fratura": "Quebra de osso.",
        "Incapacidade de apoiar o peso": "Não conseguir sustentar o corpo sobre a perna.",
        "Anticoagulante": "Medicamento que afina o sangue e aumenta risco de sangramento.",
        "Laceração": "Corte profundo na pele."

        }
    },

"Delírio em idosos": {
    "definicao": "Confusão mental repentina, com alteração na atenção, memória e comportamento.",
    "popular": "Quando o idoso começa a falar coisa sem sentido, se perde no tempo e espaço ou vê coisas que não existem. Pode surgir de repente e piorar à noite.",
    "clinico": "Delirium",
    "termos": {
        "Desorientação": "Perda da noção de tempo, lugar ou pessoa.",
        "Alucinações": "Ver/ouvir coisas que não existem.",
        "Flutuação de consciência": "Oscilações entre momentos de lucidez e confusão.",
        "Fala enrolada": "Dificuldade para articular palavras.",
        "Desidratação": "Falta de líquidos no corpo (boca seca, pouca urina)."
        }
    },

"Trauma grave": {
    "definicao": "Lesão corporal severa que coloca a vida em risco, como batidas fortes, atropelamentos ou quedas de altura.",
    "popular": "Quando a pessoa se machuca seriamente, com muito sangue, fratura exposta, dificuldade pra respirar ou inconsciência.",
    "clinico": "Trauma de alta energia",
    "termos": {
        "Fratura exposta": "Quebra de osso com ferida aberta, deixando o osso em contato com o exterior.",
        "Sangramento grave": "Perda de sangue em grande volume ou de forma contínua, difícil de estancar.",
        "Hematoma": "Mancha roxa sob a pele causada por acúmulo de sangue após trauma.",
        "Incapacidade de apoiar o peso": "Impossibilidade de sustentar o corpo sobre a perna por dor ou fraqueza.",
        "Anticoagulante": "Remédio que afina o sangue e aumenta o risco de sangramentos.",
        "Politrauma": "Trauma que atinge várias partes do corpo ao mesmo tempo."
        }
    },
    
"Dor de dente": {
    "definicao": "Dor localizada nos dentes, podendo ser constante ou pulsante.",
    "popular": "Quando o dente começa a doer forte, latejar ou doer ao morder. Pode vir com inchaço, febre ou dor irradiada pra cabeça.",
    "clinico": "Odontalgia",
    "termos": {
        "Secreção purulenta": "Líquido amarelado/esverdeado espesso, típico de infecção.",
        "Trismo": "Dificuldade para abrir a boca por dor ou rigidez dos músculos.",
        "Irradiação da dor": "Quando a dor se espalha para outra região (ex.: face ou orelha)."
        }
    },

"Alteração na audição": {
    "definicao": "Redução da audição ou percepção de sons anormais.",
    "popular": "Quando a pessoa começa a escutar menos, sentir o ouvido tapado, ouvir zumbido ou ter dor no ouvido.",
    "clinico": "Hipoacusia ou zumbido",
    "termos": {
        "Perda súbita da audição": "Queda rápida da audição em horas/dias, geralmente em um ouvido.",
        "Zumbido": "Som percebido no ouvido (apito/chiado) sem fonte externa.",
        "Ouvido tampado": "Sensação de pressão/entupimento no ouvido.",
        "Vertigem": "Sensação de que tudo está girando (rodação).",
        "Barotrauma": "Lesão por mudança brusca de pressão (voo/mergulho)."
        }
    },

"Dor de garganta": {
    "definicao": "Dor ou irritação na garganta, que pode dificultar engolir ou falar.",
    "popular": "Aquela dor pra engolir, que às vezes vem com pus, placas brancas ou febre. Pode arder, queimar ou deixar a voz rouca.",
    "clinico": "Faringite ou amigdalite",
    "termos": {
        "Placas/pus nas amígdalas": "Material esbranquiçado nas amígdalas, comum em infecções.",
        "Dificuldade para engolir saliva (baba)": "Saliva escorrendo porque engolir está muito doloroso/difícil.",
        "Voz abafada ('batata quente')": "Fala alterada com som abafado, sugerindo inflamação importante na garganta."
        }
    },

"Dor nas articulações": {
    "definicao": "Dor ou desconforto nas juntas (joelho, ombro, cotovelo, etc.).",
    "popular": "É quando dói o joelho, ombro ou outra articulação, principalmente ao se mexer ou depois de uma batida. Pode inchar e ficar quente.",
    "clinico": "Artralgia",
    "termos": {
        "Dor súbita com inchaço e dificuldade de movimentar": "Apareceu de repente, está inchado e difícil de mexer.",
        "Dor intensa após trauma ou inflamação visível": "Dói muito depois de bater ou quando está visivelmente inchado/vermelho.",
        "Dor moderada que piora com o uso": "Dói um pouco e piora quando mexe ou anda.",
        "Dor leve que melhora com repouso": "Dói pouco e melhora quando descansa."
        }
    },

"Dor no peito": {
    "definicao": "Dor ou pressão no peito, que pode vir do coração, dos pulmões ou da musculatura.",
    "popular": "É aquela dor no peito que acontece do nada ou depois de exercícios físicos, ela pode ser estável (permanece igual com o tempo) ou ficar cada vez pior.",
    "clinico": "Dor torácica",
    "termos": {
        "Aperto/queimação intensa": "Dor forte no peito como se estivesse sendo apertado ou queimando.",
        "Irradiação para braço, mandíbula ou costas": "A dor do peito se espalha para braço, mandíbula ou costas.",
        "Suor frio": "Suor excessivo com sensação de frio e palidez.",
        "Desmaio/confusão": "Perdeu a consciência ou ficou desorientado junto com a dor.",
        "Piora progressiva": "A dor vai aumentando com o tempo."
        }
    },
"Dor de cabeça": {
    "definicao": "Dor na região da cabeça, que pode ter várias causas como tensão, problemas neurológicos ou infecções.",
    "popular": "É quando a cabeça começa a doer forte, média ou fraca, podendo vir com enjoo, luz incomodando ou vista embaçada.",
    "clinico": "Cefaleia",
    "termos": {
        "Muito forte e súbita": "Dor que “explode” de uma vez.",
        "Rigidez na nuca": "Pescoço duro, difícil encostar o queixo no peito.",
        "Fraqueza de um lado/fala enrolada": "Um lado do corpo fica fraco ou fala sai arrastada.",
        "Sensibilidade à luz": "Luz incomoda e piora a dor."
        }
    },
"Sensação de desmaio": {
    "definicao": "Sensação de desequilíbrio, fraqueza ou como se fosse desmaiar.",
    "popular": "É quando parece que tudo gira ou que vai cair. Pode dar visão escura, fraqueza e suor frio.",
    "clinico": "Pré-síncope ou vertigem",
    "termos": {
        "Fraqueza súbita com visão turva e suor frio": "Sensação repentina de fraqueza, visão embaçada e suor frio.",
        "Tontura persistente com sensação de queda iminente": "Tontura que continua e dá a impressão de que vai cair.",
        "Sensação leve de cabeça vazia ou instabilidade": "Leve sensação de cabeça leve ou falta de firmeza ao andar.",
        "Episódio pontual que já passou": "Sensação de desmaio que aconteceu mas já cessou."
        }
    },
"Formigamento ou perda de força": {
    "definicao": "Sensação de dormência, formigamento ou fraqueza em uma parte do corpo.",
    "popular": "Pode parecer que a mão ou perna está dormente ou sem força. Se for de repente, é mais preocupante.",
    "clinico": "Parestesia ou déficit motor",
    "termos": {
        "Face caída de um lado": "Um lado do rosto fica ‘torto’ ou sem força.",
        "Fala arrastada": "Palavras saem enroladas/difíceis de entender.",
        "Súbito": "Começou de repente, sem aviso.",
        "AVC/AIT": "Derrame ou ‘mini-derrame’ com sintomas que podem passar."
        }
    },
"Vômito": {
    "definicao": "Expulsão do conteúdo do estômago pela boca.",
    "popular": "Quando o estômago coloca pra fora o que comeu. Pode acontecer uma vez ou várias.",
    "clinico": "Emese",
    "termos": {
        "Não consegue manter líquidos": "Vomita logo após beber água/soro e não hidrata.",
        "Mais de 5 vezes": "Muitas vezes em pouco tempo.",
        "Vômitos com sangue": "Vômito vermelho/escuro; pode parecer borra de café.",
        "Sinais de desidratação": "Boca seca, pouca urina, tontura."
        }
    },
"Dor abdominal": {
    "definicao": "Dor na barriga, que pode ter várias causas como gases, inflamações ou infecções.",
    "popular": "É dor na barriga, que pode ser leve ou forte, de repente ou aos poucos, e pode vir com febre ou vômito.",
    "clinico": "Dor abdominal",
    "termos": {
        "Barriga muito dura": "Abdome rígido ao toque.",
        "Sem eliminar gases/fezes": "Intestino parado, sem evacuar ou soltar gases.",
        "Lado direito inferior": "Região da apendicite (parte baixa do lado direito).",
        "Parte de cima do lado direito": "Região do fígado/vesícula."
        }
    },
"Dor nas costas": {
    "definicao": "Dor na região lombar, média ou alta da coluna.",
    "popular": "Aquela dor nas costas que pode piorar ao se mexer ou pegar peso, às vezes travando o movimento.",
    "clinico": "Lombalgia ou dorsalgia",
    "termos": {
        "Dormência em sela": "Formigamento/insensibilidade na região entre as pernas.",
        "Irradiação para a perna (ciática)": "Dor que desce pela perna com formigamento ou fraqueza.",
        "Trauma recente importante": "Queda forte, batida ou acidente recente."
        }
    },
"Febre": {
    "definicao": "Temperatura do corpo acima do normal (geralmente acima de 37,8°C).",
    "popular": "Quando o corpo fica quente, pode vir com tremores, mal-estar e cansaço.",
    "clinico": "Hipertermia",
    "termos": {
        "≥ 40°C": "Febre muito alta no termômetro.",
        "3 a 7 dias": "Febre que não cede por vários dias seguidos.",
        "Confusão mental": "Pessoa desorientada, falando coisas sem sentido.",
        "Rigidez na nuca": "Pescoço duro, difícil de encostar o queixo no peito.",
        "Falta de ar intensa": "Respiração muito difícil, sensação de ar faltando."
        }
    },
"Palpitações": {
    "definicao": "Sensação de que o coração está acelerado ou batendo forte.",
    "popular": "Quando o coração dispara ou bate fora do normal, mesmo em repouso.",
    "clinico": "Taquicardia ou arritmia",
    "termos": {
        "Batimentos acelerados com dor no peito ou falta de ar": "Coração disparado acompanhado de dor no peito ou dificuldade para respirar.",
        "Palpitações intensas e persistentes, sem outros sintomas": "Coração acelerado por um período longo, mas sem outros sinais.",
        "Batimentos rápidos ocasionais, mas sem desconforto": "Coração bate rápido de vez em quando, sem causar incômodo.",
        "Sensação leve que passa rapidamente": "Coração bateu rápido por pouco tempo e depois voltou ao normal."
        }
    },
"Diarreia": {
    "definicao": "Evacuação líquida ou amolecida mais vezes que o normal.",
    "popular": "Quando vai ao banheiro várias vezes com fezes moles ou líquidas, podendo vir com dor de barriga.",
    "clinico": "Diarreia",
    "termos": {
        "Diarreia intensa com sangue ou sinais de desidratação": "Fezes muito líquidas e frequentes, com sangue ou sinais de desidratação.",
        "Várias evacuações líquidas com febre ou dor abdominal": "Evacuações frequentes e líquidas acompanhadas de febre ou dor de barriga.",
        "Episódio isolado de diarreia sem outros sintomas": "Um único episódio de fezes líquidas sem outros problemas.",
        "Fezes amolecidas por curto período": "Fezes mais moles do que o normal, por pouco tempo."
        }
    }
}
    return dict(sorted(d.items()))

dic = dicionario_sintomas()

import streamlit as st
import time
import random
import pandas as pd

st.set_page_config(page_title="Sistema de Triagem", layout="centered")

# --- ESTADO INICIAL ---
st.session_state.setdefault("etapa", 1)
st.session_state.setdefault("tentativa", 1)
st.session_state.setdefault("resultados", [])
st.session_state.setdefault("testando", False)
st.session_state.setdefault("ready", False)
st.session_state.setdefault("start_time", None)

correcao_sistema = 0.47

# --- MENU LATERAL COM CONTROLE DE ETAPA ---
opcoes_disponiveis = ["Nenhuma", "Dicionário de sintomas"]
if st.session_state.etapa >= 2:
    opcoes_disponiveis.append("Autotestes para apuração de sintoma")

opcao = st.sidebar.selectbox("Escolha uma opção", opcoes_disponiveis)

# --- MENU DE SISTEMAS E TESTES INFORMAL ---
sistemas = {
    "🧠 Neurológico": [
        "Tempo de Reação",
        "Memória Curta",
        "Reflexo Seletivo",
        "Coordenação Fina",
        "Toque Rápido (10s)",
        "Equilíbrio",
        "Humor e Ansiedade",
        "Humor na última semana"
    ],
    "👁️ Sensorial": [
        "Visão",
        "Campo Visual",
        "Percepção de Cores",
        "Audição (Frequências Altas e Baixas)",
        "Audição (Detecção de Som)"
    ],
    "💓 Cardíaco": [
        "Cardíaco",
        "Recuperação Cardíaca",
        "Palpitações"
    ],
    "🫁 Respiratório": [
        "Respiração",
        "Apneia Simples",
        "Sopro Sustentado",
        "Contagem em uma Respiração",
        "Diferenciar Falta de Ar e Dificuldade Respiratória",
    ],
    "🧬 Vascular / Circulatório": [
        "Enchimento Capilar",
        "Varizes"
    ],
    "🦵 Musculoesquelético": [
        "Força da Mão",
        "Subir Escada com Uma Perna",
        "Levantar do Chão"
    ],
    "🚽 Digestivo / Intestinal": [
        "Digestão",
        "Ritmo Intestinal"
    ],
    "💧 Urinário e Hidratação": [
        "Urinário",
        "Hidratação",
        "Cor da Urina"
    ],
    "🧴 Cutâneo": [
        "Pele e Coceira"
    ],
    "☕ Energia e Vitalidade": [
        "Energia Matinal",
        "Variação de Peso (Últimos 30 Dias)"
    ],
    "Testes de apuração de sintomas": [
        "Palpação de Linfonodos (Check-list)"
    ]
}


subteste = None
if opcao == "Autotestes para apuração de sintoma":
    st.title("📋 Autotestes para apuração de sintoma de Saúde")
    st.caption("Esses testes são apenas indicativos e não substituem avaliação médica.")
    sistema_escolhido = st.selectbox("🔍 Escolha o sistema para testar:", list(sistemas.keys()))
    subteste = st.radio("🧪 Escolha o teste específico:", sistemas[sistema_escolhido])

# --- DICIONÁRIO DE SINTOMAS ---
if opcao == "Dicionário de sintomas":
    sintoma_selecionado = st.selectbox("Escolha um sintoma:", list(dic.keys()))
    st.subheader(f"🔎 {sintoma_selecionado}")
    st.markdown(f"**Definição Clínica:** {dic[sintoma_selecionado]['definicao']}")
    st.markdown(f"**Explicação Popular:** {dic[sintoma_selecionado]['popular']}")
    st.markdown(f"**Nome Clínico:** {dic[sintoma_selecionado]['clinico']}")
    st.markdown("**Variações do Sintoma:**")
    for subtitulo, explicacao in dic[sintoma_selecionado]["termos"].items():
        st.markdown(f"- **{subtitulo}:** {explicacao}")

#AUTO TESTES
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Tempo de Reação":
    st.subheader("🧠 Teste de Tempo de Reação")
    st.warning("⚠️ A primeira tentativa é apenas um teste de preparação e **não será contabilizada na média final**.")


    if not st.session_state.testando and st.session_state.tentativa <= 8:
        delay = random.uniform(3, 7)
        st.session_state.delay = delay
        st.session_state.ready = False
        st.session_state.testando = True
        st.rerun()

    elif st.session_state.testando and not st.session_state.ready:
        time.sleep(st.session_state.delay)
        st.session_state.start_time = time.time()
        st.session_state.ready = True
        st.rerun()

    elif st.session_state.testando and st.session_state.ready:
        st.success("✅ Clique agora!")
        if st.button("🟢 Clique aqui!"):
            fim = time.time()
            tempo_reacao = fim - st.session_state.start_time - 0.47  # Correção interna

            if st.session_state.tentativa != 1:
                st.session_state.resultados.append(tempo_reacao)

            st.session_state.tentativa += 1
            st.session_state.testando = False
            st.session_state.ready = False
            st.rerun()
    # Finalizar após 8 tentativas
    elif st.session_state.tentativa > 8:
        st.subheader("⏱️ Resultados")

        for i, r in enumerate(st.session_state.resultados, start=2):
            st.write(f"Tentativa {i}: ⏱️ {r:.2f} segundos")

        media = sum(st.session_state.resultados) / len(st.session_state.resultados)

        # === PERFIL ===
        idade = st.session_state.get("idade", 30)
        imc = st.session_state.get("imc", 22)
        gravidez = st.session_state.get("gravida", False)
        sexo = st.session_state.get("sexo", "Outro")
        riscos = st.session_state.get("grupos_risco_refinados", [])

        base = 0.40  # base geral

        # Ajustes por idade
        if idade <= 7:
            base += 0.20
        elif idade <= 16:
            base += 0.10
        elif idade <= 35:
            base += 0.00
        elif idade <= 58:
            base += 0.05
        else:
            base += 0.10

        # Ajustes por IMC
        if imc < 16:
            base += 0.10
        elif imc >= 30:
            base += 0.05

        # Gravidez
        if gravidez:
            base += 0.08

        # Riscos específicos
        if "neurológica" in riscos or "psiquiátrica" in riscos:
            base += 0.10
        if "cardíaca" in riscos:
            base += 0.05
        if "respiratória" in riscos:
            base += 0.05

        # Tolerância de 25%
        lim_inferior = base * 0.75
        lim_superior = base * 1.25

        st.markdown("---")
        st.subheader(f"🏁 Média final: **{media:.2f} segundos**")

        if media < lim_inferior:
            st.success("⚡ Seu tempo está **acima do esperado**. Excelente reflexo!")
        elif media > lim_superior:
            st.warning("🐢 Seu tempo está **abaixo do esperado**. Considere repetir o teste mais tarde.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Hipoglicemia,Hipotensão ou colapso,Formigamento ou perda de força**")
        else:
            st.info("✅ Seu tempo está **dentro do esperado**. Tudo normal por aqui!")

        # Resetar botão
        if st.button("🔁 Refazer o teste"):
            for key in ["tentativa", "resultados", "testando", "ready", "start_time"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Memória Curta":
    st.subheader("🧠 Teste de Memória Curta")

    if "palavras_memoria" not in st.session_state:
        todas_palavras = ["abacate", "ônibus", "papel", "relógio", "vela", "caneta", "tigre", "janela", "maçã", "boneco"]
        st.session_state.palavras_memoria = random.sample(todas_palavras, 5)
        st.session_state.exibir_palavras = True
        st.session_state.resposta_usuario = ""

    if st.session_state.exibir_palavras:
        st.info("Leia e memorize as palavras abaixo. Você terá 8 segundos.")
        st.write(" | ".join(st.session_state.palavras_memoria))
        time.sleep(8)
        st.session_state.exibir_palavras = False
        st.rerun()
    else:
        st.write("Agora, escreva abaixo as palavras que você se lembra.")
        resposta = st.text_input("Digite as palavras separadas por vírgula:")
        if st.button("Ver resultado"):
            palavras_digitadas = [p.strip().lower() for p in resposta.split(",")]
            corretas = [p for p in palavras_digitadas if p in st.session_state.palavras_memoria]
            st.success(f"Você lembrou corretamente de {len(corretas)} palavra(s).")
            st.write(f"Palavras corretas: {', '.join(corretas)}")
            st.info("5 palavras: Excelente memória. 4: dentro do esperado. 0 a3: sugere atenção à memória recente.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Confusão mental,Comportamento estranho à normalidade,delírio em idosos(se aplicável)**")
            if st.button("Refazer teste"):
                for key in ["palavras_memoria", "exibir_palavras", "resposta_usuario"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Diferenciar Falta de Ar e Dificuldade Respiratória":
    st.subheader("🌬️ Diferenciar Falta de Ar e Dificuldade Respiratória")

    st.markdown("""
    Este autoteste ajuda a diferenciar entre **sensação subjetiva de falta de ar** e **dificuldade real para respirar**.

    **Definições rápidas:**
    - **Falta de ar**: sensação desconfortável de que precisa de mais ar, mas consegue movimentar o ar normalmente.
    - **Dificuldade respiratória**: incapacidade ou esforço anormal para mover o ar (entrada ou saída).

    **Responda às perguntas abaixo:**
    """)

    # Perguntas
    inicio_subito = st.radio("O sintoma começou de forma súbita (em segundos/minutos)?", ["Não", "Sim"], index=0, horizontal=True)
    fala_frases = st.radio("Você consegue falar frases completas sem parar para respirar?", ["Sim", "Não"], index=0, horizontal=True)
    posicao_alivia = st.radio("Mudar de posição (sentar, inclinar) alivia o sintoma?", ["Não", "Sim"], index=0, horizontal=True)
    chiado_estridor = st.radio("Há ruído alto ao respirar (chiado ou estridor)?", ["Não", "Sim"], index=0, horizontal=True)
    esforco_visivel = st.radio("Movimentos visíveis de esforço para respirar (pescoço, tórax, abdome)?", ["Não", "Sim"], index=0, horizontal=True)

    if st.button("Analisar tipo de sintoma respiratório"):
        score_dificuldade = 0
        if fala_frases == "Não":
            score_dificuldade += 2
        if chiado_estridor == "Sim":
            score_dificuldade += 2
        if esforco_visivel == "Sim":
            score_dificuldade += 2
        if inicio_subito == "Sim":
            score_dificuldade += 1

        if score_dificuldade >= 4:
            st.error("🚨 Indícios fortes de **dificuldade respiratória**.")
            st.markdown("🔎 Relacionados: **dificuldade respiratória**, possivelmente obstrução ou comprometimento pulmonar grave.")
        elif score_dificuldade >= 2:
            st.warning("⚠️ Indícios mistos, com elementos de dificuldade respiratória. Monitore e procure avaliação se piorar.")
            st.markdown("🔎 Relacionados: **dificuldade respiratória** e/ou **falta de ar**.")
        else:
            st.success("✅ Mais compatível com **falta de ar subjetiva**.")
            st.markdown("🔎 Relacionados: **falta de ar**, geralmente associada a ansiedade, esforço físico ou condicionamento.")

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Visão":
    st.subheader("👁️ Teste Visual com Dificuldade Progressiva")

    st.markdown("Você verá 5 números com níveis diferentes de visibilidade. Tente identificar todos que conseguir. Eles variam do mais visível até o mais apagado.")

    # Apenas gerar os números uma vez por teste
    if "numeros_visuais" not in st.session_state:
        todos_numeros = random.sample(range(10, 99), 5)
        st.session_state.numeros_visuais = [str(n) for n in todos_numeros]
        st.session_state.contrastes = ["#000000", "#666666", "#999999", "#BBBBBB", "#DDDDDD"]

    # Montar HTML com os 5 números e seus contrastes
    html_numeros = "<div style='font-size:16px; letter-spacing:12px;'>"
    for num, cor in zip(st.session_state.numeros_visuais, st.session_state.contrastes):
        html_numeros += f"<span style='color:{cor}'>{num}</span>  "
    html_numeros += "</div>"

    st.markdown(html_numeros, unsafe_allow_html=True)

    resposta = st.text_input("Quais números você conseguiu enxergar? (Separe por espaço)").strip()

    if st.button("Verificar resposta visual"):
        resposta_usuario = resposta.split()
        corretos = [n for n in resposta_usuario if n in st.session_state.numeros_visuais]
        st.success(f"Você identificou corretamente {len(corretos)} número(s): {', '.join(corretos) if corretos else 'nenhum'}")

        if len(corretos) == 5:
            st.info("✅ Sua visão está excelente neste teste.")
        elif len(corretos) >= 4:
            st.warning("⚠️ Pode haver alguma dificuldade de percepção visual em baixo contraste.")
            st.markdown("🔎 Possíveis sintoma relacionado: **Dor ou olho vermelho,Sensibilidade à luz ou som**")
        else:
            st.error("🚨 Dificuldade significativa. Considere procurar um oftalmologista.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Dor ou olho vermelho,Sensibilidade à luz ou som,Alterações visuais súbitas**")

        if st.button("Refazer teste visual"):
            for key in ["numeros_visuais", "contrastes"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Toque Rápido (10s)":
    st.subheader("👆 Toque Rápido (10 segundos)")

    idade = st.session_state.get("idade")
    if idade is None:
        faixa = "adulto"
    elif idade <= 12:
        faixa = "crianca"
    elif idade >= 67:
        faixa = "idoso"
    else:
        faixa = "adulto"

    # cortes por faixa etária: [baixo, comum_max]
    # <baixo -> lento; entre baixo e comum_max -> comum; >comum_max -> muito bom
    cortes = {
        "crianca": [18, 45],
        "adulto":  [20, 40],
        "idoso":   [15, 35],
    }
    c_baixo, c_comum_max = cortes[faixa]

    st.markdown("Mede **destreza/velocidade motora fina**: quantos cliques consegue fazer em **10 segundos**.")

    if "tap_inicio" not in st.session_state:
        st.session_state.tap_inicio = None
        st.session_state.tap_contagem = 0

    cols = st.columns(2)
    with cols[0]:
        if st.session_state.tap_inicio is None:
            if st.button("Iniciar 10s"):
                st.session_state.tap_inicio = time.time()
                st.session_state.tap_contagem = 0
                st.rerun()
        else:
            decorrido = time.time() - st.session_state.tap_inicio
            restante = max(0, 10 - int(decorrido))
            st.info(f"Cronômetro: {restante} s")
            if restante == 0:
                st.success("Tempo encerrado!")
    with cols[1]:
        if st.session_state.tap_inicio is not None and (time.time() - st.session_state.tap_inicio) < 10:
            if st.button("Clique!"):
                st.session_state.tap_contagem += 1
                st.rerun()
        else:
            st.button("Clique!", disabled=True)

    st.metric("Cliques contabilizados", st.session_state.tap_contagem)

    if st.session_state.tap_inicio is None and st.session_state.tap_contagem > 0:
        total = st.session_state.tap_contagem
        if total < c_baixo:
            st.error("🚨 Abaixo do esperado para a sua faixa etária.")
            st.markdown("🔎 Relacionados: **Formigamento ou perda de força,tremores ou movimentos involuntários**")
        elif total <= c_comum_max:
            st.success("✅ Faixa comum para a sua faixa etária.")
        else:
            st.info("💪 Desempenho acima do comum para a sua faixa.")

    if st.button("Refazer teste (Toque Rápido)"):
        for k in ["tap_inicio", "tap_contagem"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Reflexo Seletivo":
    st.subheader("✋ Teste de Reflexo Seletivo – Clique apenas quando aparecer o número 7")
    st.write("Você verá 10 números. Clique **somente** quando aparecer o número 7.")

    if "clique_reflexo" not in st.session_state:
        numeros = [random.randint(0, 9) for _ in range(9)]  # gera 9 aleatórios
        numeros.append(7)  # garante que pelo menos 1 seja 7
        random.shuffle(numeros)  # embaralha a posição do 7
        st.session_state.clique_reflexo = {
            "numeros": numeros,
            "respostas": [],
            "indice": 0
    }


    dados = st.session_state.clique_reflexo
    total = len(dados["numeros"])

    if dados["indice"] < total:
        atual = dados["numeros"][dados["indice"]]
        st.markdown(f"### Número mostrado: **{atual}**")
        st.markdown(f"Rodada {dados['indice'] + 1} de {total}")

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Clique se for 7", key=f"clicar_{dados['indice']}"):
                clicou = (atual == 7)
                dados["respostas"].append(("clicou", atual))
                dados["indice"] += 1
                st.rerun()
        with col2:
            if st.button("Ignorar", key=f"ignorar_{dados['indice']}"):
                dados["respostas"].append(("ignorou", atual))
                dados["indice"] += 1
                st.rerun()
    else:
        st.subheader("📊 Resultado do Teste")

        cliques_certos = sum(1 for acao, n in dados["respostas"] if acao == "clicou" and n == 7)
        cliques_errados = sum(1 for acao, n in dados["respostas"] if acao == "clicou" and n != 7)
        deixou_passar = sum(1 for acao, n in dados["respostas"] if acao == "ignorou" and n == 7)
        total_7 = dados["numeros"].count(7)

        st.write(f"Números 7 apresentados: {total_7}")
        st.write(f"Cliques corretos: {cliques_certos}")
        st.write(f"Cliques errados (falsos positivos): {cliques_errados}")
        st.write(f"Números 7 ignorados (erros por omissão): {deixou_passar}")

        if cliques_errados == 0 and deixou_passar == 0:
            st.success("✅ Excelente! Atenção e reflexos muito bons.")
        elif cliques_errados <= 1 and deixou_passar <= 1:
            st.info("⚠️ Bom desempenho, mas pode melhorar atenção seletiva.")
            st.markdown("🔎 Sintomas relacionados: **Ansiedade, Agitação, Tremores**")
        else:
            st.warning("🔄 Atenção baixa ou reflexo impreciso. Praticar foco seletivo pode ajudar.")
            st.markdown("🔎 Sintomas relacionados: **Confusão mental, Agitação intensa, Comportamento estranho à normalidade**")

        if st.button("Refazer teste"):
            del st.session_state["clique_reflexo"]
            st.rerun()

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Respiração":
    st.subheader("🌬️ Teste de Frequência Respiratória")

    st.markdown("Este teste avalia sua frequência respiratória. Respire normalmente.")

    if "cronometro_ativo" not in st.session_state:
        st.session_state.cronometro_ativo = False
        st.session_state.resp_contagem = None

    if not st.session_state.cronometro_ativo:
        if st.button("Iniciar contagem de 30 segundos"):
            st.session_state.cronometro_ativo = True
            st.rerun()
    else:
        st.info("⏳ Conte mentalmente suas respirações por 30 segundos...")
        time.sleep(30)
        st.session_state.cronometro_ativo = False
        st.rerun()

    if not st.session_state.cronometro_ativo and st.session_state.resp_contagem is None:
        resp = st.number_input("Quantas respirações você contou em 30 segundos?", min_value=0, max_value=50, step=1)
        if st.button("Verificar resultado"):
            st.session_state.resp_contagem = resp * 2  # transforma em respirações por minuto
            st.rerun()

    if st.session_state.resp_contagem is not None:
        freq = st.session_state.resp_contagem
        st.subheader(f"📈 Sua frequência respiratória: **{freq} respirações por minuto**")

        idade = st.session_state.get("idade", 30)

        # Define intervalo normal baseado na idade
        if idade < 12:
            normal = (18, 30)
            faixa = "crianças"
        elif idade < 60:
            normal = (12, 20)
            faixa = "adultos"
        else:
            normal = (12, 22)
            faixa = "idosos"

        st.markdown(f"🔎 Para a faixa etária de **{faixa}**, espera-se entre **{normal[0]} e {normal[1]} respirações por minuto**.")

        if freq < normal[0]:
            st.warning(f"📉 Sua frequência está **abaixo do esperado para sua faixa etária ({faixa})**.")
            st.markdown("🔎 Isso pode indicar **bradipneia** — respiração mais lenta do que o normal, comum em certos quadros neurológicos, sedação, ou problemas respiratórios.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Dificuldade respiratória, Falta de ar, Confusão mental, Hipotensão ou colapso, e Desmaio ou tontura**")
        elif normal[0] <= freq <= normal[1]:
            st.success(f"✅ Sua frequência está **dentro do intervalo esperado para {faixa}**.")
            st.markdown("🫁 Respiração em ritmo normal indica boa função respiratória no repouso.")
        else:
            st.warning(f"📈 Sua frequência está **acima do esperado para sua faixa etária ({faixa})**.")
            st.markdown("🔎 Isso pode indicar **taquipneia** — respiração acelerada, comum em febres, ansiedade, anemia ou problemas pulmonares.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Dificuldade respiratória, falta de ar, ansiedade ou agitação intensa, dor no peito e febre**")


        if st.button("Refazer teste respiratório"):
            for key in ["cronometro_ativo", "resp_contagem"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Cardíaco":
    st.subheader("❤️ Teste de Frequência Cardíaca pós-esforço")

    st.markdown("Este teste simula uma avaliação leve da resposta do seu coração ao esforço. Você fará 1 minuto de movimento e depois medirá seus batimentos por 15 segundos.")

    if "etapa_cardio" not in st.session_state:
        st.session_state.etapa_cardio = 0
        st.session_state.batimentos_15s = None
        st.session_state.frequencia_final = None

    if st.session_state.etapa_cardio == 0:
        if st.button("Iniciar o esforço (1 minuto de senta e levanta)"):
            st.session_state.etapa_cardio = 1
            st.rerun()

    elif st.session_state.etapa_cardio == 1:
        st.info("⏳ Faça o movimento de sentar e levantar por **1 minuto**. Em seguida, você medirá seus batimentos por 15 segundos.")
        time.sleep(60)
        st.session_state.etapa_cardio = 2
        st.rerun()

    elif st.session_state.etapa_cardio == 2:
        st.success("✅ Agora, sente-se e **coloque a mão no peito**. Prepare-se para contar os batimentos por 15 segundos.")
        if st.button("Iniciar cronômetro de 15 segundos"):
            st.session_state.etapa_cardio = 3
            st.rerun()

    elif st.session_state.etapa_cardio == 3:
        st.info("⏳ Conte seus batimentos por 15 segundos...")
        time.sleep(15)
        st.session_state.etapa_cardio = 4
        st.rerun()

    elif st.session_state.etapa_cardio == 4:
        st.success("⏱️ Tempo encerrado!")
        batimentos = st.number_input("Quantos batimentos você contou em 15 segundos?", min_value=0, max_value=100, step=1)
        if st.button("Ver resultado"):
            st.session_state.batimentos_15s = batimentos
            st.session_state.frequencia_final = batimentos * 4
            st.session_state.etapa_cardio = 5
            st.rerun()

    elif st.session_state.etapa_cardio == 5:
        fc = st.session_state.frequencia_final
        st.subheader(f"📈 Sua frequência cardíaca estimada: **{fc} bpm**")

        idade = st.session_state.get("idade", 30)
        imc = st.session_state.get("imc", 22)
        riscos = st.session_state.get("grupos_risco_refinados", [])
        obeso = imc >= 30
        risco_card = "cardíaca" in riscos

        # Avaliação básica
        if idade < 12:
            lim_sup = 110
        elif idade <= 39:
            lim_sup = 100
        elif idade <= 59:
            lim_sup = 105
        else:
            lim_sup = 110

        # Penalidades
        if obeso:
            lim_sup -= 3
        if risco_card:
            lim_sup -= 5

        st.markdown(f"🔎 Limite superior esperado para sua faixa: **{lim_sup} bpm**")

        if fc < 60:
            st.warning("📉 Frequência abaixo do normal. Pode indicar **bradicardia**, ou boa adaptação cardiovascular. Avaliar junto a sintomas.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Palpitações ou batimentos cardíacos acelerados, Sensação de desmaio, Hipotensão ou colapso.**")
        elif fc <= lim_sup:
            st.success("✅ Frequência dentro do esperado após esforço leve. Boa resposta cardíaca.")
        elif fc <= lim_sup + 10:
            st.warning("⚠️ Leve taquicardia. Pode estar relacionada ao esforço, ansiedade ou baixa adaptação ao exercício.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Ansiedade ou agitação intensa, Palpitações**")
        else:
            st.error("🚨 Frequência muito acima do esperado. Considere procurar um médico, especialmente se houver sintomas associados.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Palpitações, Dor no peito, Falta de ar, Hipertensão não controlada (caso haja futuro mapeamento)**")

        if st.button("Refazer teste cardíaco"):
            for key in ["etapa_cardio", "batimentos_15s", "frequencia_final"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Urinário":
    st.subheader("💧 Teste Informal de Frequência Urinária")

    st.markdown("Este teste avalia seu padrão diário de urina para identificar possíveis sinais de alteração na função renal ou urinária.")

    freq = st.selectbox("Quantas vezes você urina por dia (em média)?", [
        "Menos de 4 vezes", "4 a 7 vezes", "8 a 10 vezes", "Mais de 10 vezes"
    ])

    nocturia = st.radio("Você acorda à noite para urinar?", ["Não", "1 vez", "2 vezes ou mais"])

    jato = st.radio("Você tem alguma dificuldade para iniciar ou interromper o jato de urina?", ["Não", "Leve", "Moderada", "Grave"])

    if st.button("Ver resultado"):
        score = 0

        # Frequência
        if freq == "Menos de 4 vezes" or freq == "Mais de 10 vezes":
            score += 1

        # Noctúria
        if nocturia == "2 vezes ou mais":
            score += 1

        # Jato urinário
        if jato in ["Moderada", "Grave"]:
            score += 1

        st.markdown("---")
        st.subheader("📊 Avaliação")

        if score == 0:
            st.success("✅ Nenhum sinal de alteração evidente no padrão urinário.")
        elif score == 1:
            st.warning("⚠️ Leve alteração no padrão urinário. Mantenha atenção.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Alterações urinárias**")
        else:
            st.error("🚨 Alterações urinárias percebidas. Considere procurar um médico urologista ou clínico.")
            st.markdown("🔎 Possíveis sintomas relacionado: **Alterações urinárias + Retenção ou incontinência urinária (Depende de qual foi a alteração percebida)**")
        
        if st.button("Refazer teste urinário"):
            st.rerun()

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Força da Mão":
    st.subheader("✊ Teste de Força de Pegada Manual (ambas as mãos)")

    st.markdown("""
    Este teste avalia a resistência muscular de **cada mão separadamente**.  
    Use uma **garrafa PET de 600ml cheia de água** (ou equivalente de 0,5 a 1kg).  
    Segure a garrafa com o braço estendido ao lado do corpo, **sem apoiar**, durante 1 minuto.

    Vamos começar pela **mão direita**, depois repetir com a esquerda.
    """)

    if "etapa_pega" not in st.session_state:
        st.session_state.etapa_pega = "direita"  # etapas: 'direita' → 'direita_result' → 'esquerda' → 'esquerda_result' → 'fim'
        st.session_state.resultado_pega = {}

    if st.session_state.etapa_pega in ["direita", "esquerda"]:
        lado = st.session_state.etapa_pega
        if st.button(f"Iniciar teste com a mão {lado} (1 minuto)"):
            st.session_state.etapa_pega = f"{lado}_timer"
            st.rerun()

    elif st.session_state.etapa_pega.endswith("_timer"):
        lado = st.session_state.etapa_pega.replace("_timer", "")
        st.info(f"⏳ Segure a garrafa com a mão **{lado}** por 1 minuto.")
        time.sleep(60)
        st.session_state.etapa_pega = f"{lado}_result"
        st.rerun()

    elif st.session_state.etapa_pega.endswith("_result"):
        lado = st.session_state.etapa_pega.replace("_result", "")
        terminou = st.radio(f"Você conseguiu segurar com a mão {lado} por 60 segundos?", ["Sim", "Não"], key=f"term_{lado}")
        sentiu = st.multiselect(f"Durante o tempo, com a mão {lado}, você sentiu:", ["Tremor", "Formigamento", "Dor", "Nenhum"], key=f"sent_{lado}")

        if st.button(f"Salvar resultado da mão {lado}"):
            score = 0
            if terminou == "Não":
                score += 1
            if any(s in ["Tremor", "Formigamento", "Dor"] for s in sentiu):
                score += 1
            st.session_state.resultado_pega[lado] = score

            # Avança etapa
            if lado == "direita":
                st.session_state.etapa_pega = "esquerda"
            else:
                st.session_state.etapa_pega = "fim"
            st.rerun()

    elif st.session_state.etapa_pega == "fim":
        st.subheader("📊 Resultado Final – Força das Mãos")

        score_dir = st.session_state.resultado_pega.get("direita", 0)
        score_esq = st.session_state.resultado_pega.get("esquerda", 0)

        def interpreta(score, lado):
            if score == 0:
                return f"✅ **Mão {lado.capitalize()}**: Força e resistência preservadas."
            elif score == 1:
                return f"⚠️ **Mão {lado.capitalize()}**: Leve fadiga ou sintoma. Pode ser normal, mas vale acompanhar."
                st.markdown("🔎 Possíveis sintomas relacionado: **Formigamento ou perda de força, Tremores ou movimentos involuntários**")
            else:
                return f"🚨 **Mão {lado.capitalize()}**: Sinais de fraqueza ou desconforto. Recomenda-se avaliação profissional."
                st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força, Tremores ou movimentos involuntários, Comportamento estranho à normalidade**")

        st.markdown(interpreta(score_dir, "direita"))
        st.markdown(interpreta(score_esq, "esquerda"))

        if abs(score_dir - score_esq) >= 2:
            st.warning("⚖️ Diferença importante entre as mãos. Pode indicar desequilíbrio muscular.")

        if st.button("Refazer teste das mãos"):
            for key in ["etapa_pega", "resultado_pega"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Hidratação":
    st.subheader("💦 Teste de Hidratação pela Pele (Turgor Cutâneo)")

    st.markdown("""
    Vamos fazer um teste **simples** pra saber se o seu corpo pode estar desidratado.

    ###  O que você vai fazer:
    1. Estique o braço com a palma da mão virada pra baixo.
    2. Use os dedos da outra mão para **beliscar levemente a pele do dorso da mão** (a parte de cima).
    3. Puxe a pele pra cima e segure por **2 segundos**.
    4. Depois, **solte** e observe:
        - A pele voltou imediatamente ao normal?
        - Ou ficou enrugada, demorada pra voltar?

    Quando estiver pronto, clique no botão abaixo para começar o cronômetro de 2 segundos.
    """)

    if "etapa_hidrat" not in st.session_state:
        st.session_state.etapa_hidrat = 0

    if st.session_state.etapa_hidrat == 0:
        if st.button("📌 Iniciar cronômetro de 2 segundos e beliscar a pele"):
            st.session_state.etapa_hidrat = 1
            st.rerun()

    elif st.session_state.etapa_hidrat == 1:
        st.info("⏳ Mantenha a pele puxada por 2 segundos...")
        time.sleep(2)
        st.success("✅ Agora solte e observe!")
        st.session_state.etapa_hidrat = 2
        st.rerun()

    elif st.session_state.etapa_hidrat == 2:
        resultado = st.radio(
            "O que aconteceu quando você soltou a pele?",
            [
                "A pele voltou imediatamente ao normal",
                "A pele ficou enrugada ou demorou pra voltar"
            ]
        )

        if st.button("Ver resultado"):
            st.subheader("📊 Avaliação")

            if resultado == "A pele voltou imediatamente ao normal":
                st.success("✅ Ótimo! Sua hidratação parece estar boa.")
                st.markdown("Pele bem hidratada geralmente volta rapidamente ao normal após ser puxada.")
            else:
                st.error("🚨 Pode haver sinais de desidratação.")
                st.markdown("Pele que demora pra voltar ao normal pode ser sinal de que você está com pouca água no corpo. **Beba água** e fique de olho.")
                st.markdown("🔎 Possíveis sintomas relacionados: **Temperatura muito baixa, Sensação de desmaio, Confusão mental**")

            if st.button("Refazer teste de hidratação"):
                del st.session_state.etapa_hidrat
                st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Coordenação Fina":
    st.subheader("✍️ Teste de Coordenação Fina – Espiral com a mão não dominante")

    st.markdown("""
    Este teste avalia sua **coordenação motora fina**. Você vai desenhar uma espiral usando a **mão que você menos usa** (geralmente a esquerda para destros, e vice-versa).

    ### Como fazer:
    1. Pegue papel e caneta.
    2. Com a mão não dominante, tente desenhar uma espiral.
    3. Depois desenhe outra com a mão dominante.
    4. Compare os dois resultados.

    Quando terminar, responda as perguntas abaixo.
    """)

    tremor = st.radio("O desenho com a mão não dominante saiu com muito tremor?", ["Não", "Leve", "Moderado", "Grave"])
    comparacao = st.radio("Comparado com a mão dominante, a diferença foi...", ["Pequena", "Moderada", "Muito grande"])

    if st.button("Ver resultado"):
        if tremor == "Grave" or comparacao == "Muito grande":
            st.error("🚨 Pode haver alteração significativa na coordenação fina. Se isso for incomum, procure orientação médica.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários**")
        elif tremor in ["Moderado"] or comparacao == "Moderada":
            st.warning("⚠️ Coordenação não dominante reduzida. Normal em alguns casos, mas vale observar.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários**")
        else:
            st.success("✅ Coordenação fina preservada. Diferença entre as mãos dentro do esperado.")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Equilíbrio":
    st.subheader("🦶 Teste de Equilíbrio com Olhos Fechados")

    st.markdown("""
    Este teste avalia seu **equilíbrio neuromuscular**.

    ### Como fazer:
    1. Fique em pé, descalço, em um local seguro.
    2. Junte os pés, mantenha os braços ao lado do corpo.
    3. **Feche os olhos e tente ficar parado por 30 segundos.**

    Quando terminar, responda com sinceridade:
    """)

    conseguiu = st.radio("Você conseguiu manter o equilíbrio por 30 segundos?", ["Sim, sem problemas", "Sim, mas com desequilíbrio leve", "Não, precisei abrir os olhos ou me apoiar"])

    if st.button("Ver resultado"):
        if conseguiu == "Sim, sem problemas":
            st.success("✅ Equilíbrio adequado. Sistema neuromuscular estável.")
        elif conseguiu == "Sim, mas com desequilíbrio leve":
            st.warning("⚠️ Pequena instabilidade. Pode ser normal, mas vale observar em situações futuras.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários**")
        else:
            st.error("🚨 Dificuldade de equilíbrio aparente. Pode indicar alteração neurológica ou vestibular.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Tremores ou movimentos involuntários,Formigamento ou perda de força**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Campo Visual":
    st.subheader("👁️ Teste de Campo Visual – Dedos Laterais")

    st.markdown("""
    Este teste avalia se seu campo de visão periférica está normal.

    ### Como fazer:
    1. Fique em frente a um espelho ou peça ajuda de alguém.
    2. Cubra um dos olhos com a mão.
    3. Estique os braços para os lados e **mexa os dedos** devagar.
    4. Sem mover os olhos, veja até que ponto você consegue perceber o movimento dos dedos.

    Depois, repita com o outro olho.

    Agora, responda:
    """)

    campo = st.radio("Você percebeu movimento com os dedos bem abertos para os lados?", ["Sim, com os dois olhos", "Apenas com um olho", "Com dificuldade ou não percebi"])

    if st.button("Ver resultado"):
        if campo == "Sim, com os dois olhos":
            st.success("✅ Campo visual periférico normal.")
        elif campo == "Apenas com um olho":
            st.warning("⚠️ Diferença entre os olhos. Pode ser bom investigar.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Visão embaçada progressiva,perda progressiva de visão)**")
        else:
            st.error("🚨 Campo visual comprometido. Procure avaliação oftalmológica.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Visão embaçada progressiva,perda progressiva de visão)**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Percepção de Cores":
    st.subheader("🌈 Teste de Percepção de Cores")

    st.markdown("""
    Este teste serve para verificar se você percebe cores básicas e consegue diferenciar tons próximos.

    ### Instruções:
    Observe os quadrados coloridos abaixo e **diga quais cores você enxerga**.
    """)

    html = """
    <div style='display: flex; gap: 20px; font-size: 14px;'>
        <div style='background-color: red; width: 50px; height: 50px;'></div>
        <div style='background-color: green; width: 50px; height: 50px;'></div>
        <div style='background-color: blue; width: 50px; height: 50px;'></div>
        <div style='background-color: #E6B800; width: 50px; height: 50px;'></div>
        <div style='background-color: #00CED1; width: 50px; height: 50px;'></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    resposta = st.text_input("Digite as cores que você enxerga (Não diga tons,digite somente as cores) (separe por vírgulas)").lower()

    if st.button("Ver resultado"):
        cores_corretas = ["vermelho", "verde", "azul", "amarelo", "turquesa"]
        entrada = [c.strip() for c in resposta.split(",")]
        acertos = [c for c in entrada if c in cores_corretas]

        st.success(f"Você identificou corretamente {len(acertos)} cor(es): {', '.join(acertos)}")
        if len(acertos) == 5:
            st.info("✅ Percepção de cores aparentemente normal.")
        elif len(acertos) >= 3:
            st.warning("⚠️ Pode haver dificuldade com tons específicos.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Suspeita de daltonismo)**")
        else:
            st.error("🚨 Dificuldade significativa em distinguir cores. Pode ser bom investigar daltonismo.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Suspeita de daltonismo)**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Contagem em uma Respiração":
    st.subheader("🗣️ Contagem em uma Respiração (um fôlego)")

    idade = st.session_state.get("idade")
    if idade is None:
        faixa = "adulto"
    elif idade <= 12:
        faixa = "crianca"
    elif idade >= 67:
        faixa = "idoso"
    else:
        faixa = "adulto"

    # cortes por faixa etária
    # ordem: [limite_muito_baixo, limite_baixo, limite_ok]
    cortes = {
        "crianca": [8, 16, 26],
        "adulto":  [10, 20, 30],
        "idoso":   [8, 18, 26],
    }
    c = cortes[faixa]

    st.markdown("""
    **Como fazer:**
    1. Respire fundo, clique em **Iniciar**, e comece a contar em voz alta: "1, 2, 3, ..."
    2. Pare quando precisar inspirar de novo e digite o último número alcançado.
    """)

    if "onebreath_inicio" not in st.session_state:
        st.session_state.onebreath_inicio = None

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.onebreath_inicio is None:
            if st.button("Iniciar"):
                st.session_state.onebreath_inicio = time.time()
                st.rerun()
        else:
            st.info("Contando... fale em voz alta até precisar inspirar novamente.")
    with col2:
        terminou = st.button("Terminei")

    if terminou:
        st.session_state.onebreath_inicio = None
        st.rerun()

    contagem = st.number_input("Digite o último número que conseguiu falar em um fôlego:", min_value=0, step=1, value=0)

    if st.button("Ver resultado"):
        if contagem <= c[0]:
            st.error("🚨 Resultado baixo para a sua faixa etária.")
            st.markdown("🔎 Relacionados: **falta de ar, dificuldade respiratória, ansiedade ou agitação intensas**")
        elif contagem <= c[1]:
            st.warning("⚠️ Abaixo do ideal na sua faixa. Monitore.")
            st.markdown("🔎 Relacionados: **Falta de ar,ansiedade ou agitação intensas**")
        elif contagem <= c[2]:
            st.success("✅ Dentro do esperado para a sua faixa etária.")
        else:
            st.info("💪 Desempenho acima do esperado.")

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Recuperação Cardíaca":
    st.subheader("❤️ Teste de Recuperação da Frequência Cardíaca")

    st.markdown("""
    Este teste avalia **como o seu coração se recupera após um esforço leve**.

    ### Instruções:
    1. Suba e desça um lance de escada ou marche parado por 1 minuto.
    2. Após terminar, **sente-se e descanse 1 minuto**.
    3. Após o descanso, conte seus batimentos por 15 segundos.
    """)

    idade = st.session_state.get("idade", 30)
    imc = st.session_state.get("imc", 22)
    risco = "cardíaca" in st.session_state.get("grupos_risco_refinados", [])

    bpm15 = st.number_input("Quantos batimentos você contou em 15 segundos após o descanso?", min_value=0, max_value=100, step=1)

    if st.button("Avaliar recuperação cardíaca"):
        bpm = bpm15 * 4
        limite = 100 if idade < 40 else 105
        if imc >= 30:
            limite -= 3
        if risco:
            limite -= 5

        st.subheader(f"📈 FC estimada: {bpm} bpm")
        st.markdown(f"🔎 Limite esperado ajustado: **{limite} bpm**")

        if bpm <= limite:
            st.success("✅ Boa recuperação cardíaca após esforço leve.")
        elif bpm <= limite + 10:
            st.warning("⚠️ Recuperação mais lenta do que o ideal.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dor no peito,queimação no peito**")
        else:
            st.error("🚨 Frequência alta mesmo após 1 min de descanso. Atenção recomendada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dor no peito,queimação no peito,palpitações ou batimentos acelerados**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Palpitações":
    st.subheader("💓 Teste de Palpitações com a Mão no Peito")

    st.markdown("""
    Este teste ajuda a perceber se há **batimentos irregulares** ou acelerados.

    ### Instruções:
    1. Sente-se em silêncio por 1 minuto.
    2. Coloque a mão no lado esquerdo do peito.
    3. Perceba como está seu coração: ritmo, força e regularidade dos batimentos.

    Depois, responda:
    """)

    ritmo = st.radio("O ritmo dos batimentos estava:", ["Regular", "Levemente irregular", "Muito irregular"])
    forca = st.radio("A força dos batimentos estava:", ["Normal", "Muito forte", "Muito fraca", "Variando"])
    sensacao = st.radio("Você sentiu desconforto ou batimentos acelerados sem razão?", ["Não", "Sim"])

    if st.button("Ver resultado"):
        risco = "cardíaca" in st.session_state.get("grupos_risco_refinados", [])
        alerta = 0
        if ritmo != "Regular":
            alerta += 1
        if forca != "Normal":
            alerta += 1
        if sensacao == "Sim":
            alerta += 1
        if risco:
            alerta += 1

        if alerta == 0:
            st.success("✅ Nada anormal foi percebido. Frequência e força cardíaca normais.")
        elif alerta == 1:
            st.warning("⚠️ Sinais leves. Pode ser bom repetir o teste em outro momento.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dor no peito,palpitações ou batimentos acelerados**")
        else:
            st.error("🚨 Sinais de alteração cardíaca percebidos. Procure avaliação especializada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dor no peito,queimação no peito,palpitações ou batimentos acelerados**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Apneia Simples":
    st.subheader("🌬️ Teste de Apneia Simples (Prender a Respiração)")

    st.markdown("""
    Este teste verifica sua **capacidade pulmonar e conforto respiratório**.

    ### Como fazer:
    1. Respire fundo.
    2. Prenda a respiração quando clicar no botão abaixo.
    3. Segure o máximo que conseguir **sem forçar**.
    4. Quando não aguentar mais, solte o ar e clique no botão de parar.

    **OBS**: pare imediatamente se sentir tontura ou mal-estar.
    """)

    if "apneia_inicio" not in st.session_state:
        st.session_state.apneia_inicio = None
        st.session_state.apneia_duracao = None

    if st.session_state.apneia_inicio is None:
        if st.button("Iniciar contagem (prender respiração agora)"):
            st.session_state.apneia_inicio = time.time()
            st.rerun()
    else:
        if st.button("Soltei o ar (parar)"):
            fim = time.time()
            st.session_state.apneia_duracao = round(fim - st.session_state.apneia_inicio)
            st.session_state.apneia_inicio = None
            st.rerun()

    if st.session_state.apneia_duracao is not None:
        tempo = st.session_state.apneia_duracao
        st.subheader(f"🕒 Você segurou a respiração por **{tempo} segundos**")

        if tempo < 15:
            st.error("🚨 Capacidade respiratória muito baixa. Isso pode indicar disfunção ou ansiedade.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dificuldade respiratória,falta de ar,ansiedade ou agitação intensos**")
        elif tempo < 25:
            st.warning("⚠️ Capacidade respiratória abaixo do ideal.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,dificuldade respiratória**")
        elif tempo < 40:
            st.success("✅ Capacidade respiratória dentro do esperado.")
        else:
            st.info("💪 Excelente resistência respiratória. Parabéns!")

        if st.button("Refazer teste de apneia"):
            for key in ["apneia_inicio", "apneia_duracao"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Sopro Sustentado":
    st.subheader("🫁 Teste do Sopro Sustentado – Som 'Fffff'")

    st.markdown("""
    Este teste verifica sua **força e controle respiratório**.

    ### Como fazer:
    1. Respire fundo.
    2. Ao clicar no botão abaixo, **solte o ar fazendo o som contínuo “Ffffff…”**.
    3. Continue o som o máximo que puder.  
    4. Assim que parar, clique no botão “Parei”.

    **Dica**: imagine que você está tentando apagar uma vela com o som "ffff".
    """)

    if "sopro_inicio" not in st.session_state:
        st.session_state.sopro_inicio = None
        st.session_state.sopro_tempo = None

    if st.session_state.sopro_inicio is None:
        if st.button("Começar sopro"):
            st.session_state.sopro_inicio = time.time()
            st.rerun()
    else:
        if st.button("Parei o som"):
            fim = time.time()
            st.session_state.sopro_tempo = round(fim - st.session_state.sopro_inicio)
            st.session_state.sopro_inicio = None
            st.rerun()

    if st.session_state.sopro_tempo is not None:
        t = st.session_state.sopro_tempo
        st.subheader(f"📏 Duração do sopro: **{t} segundos**")

        if t < 10:
            st.error("🚨 Força respiratória abaixo do esperado.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,dificuldade respiratória,falta de ar**")
        elif t < 20:
            st.warning("⚠️ Capacidade moderada. Pode ser melhorada com treino respiratório.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Dificuldade respiratória,ansiedade e agitação intensos**")
        else:
            st.success("✅ Boa capacidade pulmonar e controle respiratório.")

        if st.button("Refazer teste do sopro"):
            for key in ["sopro_inicio", "sopro_tempo"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Enchimento Capilar":
    st.subheader("🩸 Teste de Enchimento Capilar (Unha)")

    st.markdown("""
    Este teste simples avalia a **circulação periférica**.

    ### Como fazer:
    1. Pressione a **unha do polegar** por 5 segundos até ela ficar branca.
    2. Solte e **conte em segundos quanto tempo leva para voltar à cor rosada.**

    Depois, insira o tempo abaixo:
    """)

    tempo = st.number_input("Quantos segundos demorou para voltar à cor normal?", min_value=0, max_value=10, step=1)

    if st.button("Ver resultado"):
        if tempo <= 2:
            st.success("✅ Circulação periférica normal.")
        elif tempo <= 3:
            st.warning("⚠️ Enchimento capilar levemente prolongado. Pode ser normal, mas merece atenção.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Mãos e pés frios e arroxeados)**")
        else:
            st.error("🚨 Circulação lenta. Pode indicar desidratação, vasoconstrição ou problema circulatório.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Mãos e pés frios e arroxeados)**")

        if st.button("Refazer teste capilar"):
            st.rerun()
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Varizes":
    st.subheader("🦵 Teste de Peso nas Pernas (Possível Sinal de Varizes)")

    st.markdown("""
    Este teste serve para observar se você apresenta **sinais precoces de varizes ou má circulação nas pernas**.

    ### Como fazer:
    1. Fique **parado em pé**, sem andar, por **2 minutos**, sem se apoiar.
    2. Observe se sente **peso, desconforto, formigamento ou dor** nas pernas.

    Em seguida, responda:
    """)

    sintomas = st.multiselect("Durante os 2 minutos em pé parado, você sentiu:", [
        "Peso nas pernas", "Inchaço", "Formigamento", "Dor", "Nenhum sintoma"
    ])

    idade = st.session_state.get("idade", 30)
    imc = st.session_state.get("imc", 22)

    if st.button("Ver resultado"):
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
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,dor na perna ou dificuldade pra caminhar**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Subir Escada com Uma Perna":
    st.subheader("🦿 Teste de Força Unilateral (Subir Escada com Uma Perna)")

    st.markdown("""
    Este teste avalia a **força e equilíbrio de cada perna separadamente**.

    ### Como fazer:(**Teste de risco,se considerar-se possivelmente inapto para o teste NÃO FAÇA)
    1. Fique próximo de uma escada ou degrau firme.
    2. Tente **subir com apenas uma perna**, sem se apoiar nas mãos.
    3. Desça com cuidado.
    4. Repita com a outra perna.

    Agora, responda:
    """)

    direita = st.radio("Você conseguiu subir com a perna direita?", ["Sim", "Com dificuldade", "Não"], key="escada_dir")
    esquerda = st.radio("Você conseguiu subir com a perna esquerda?", ["Sim", "Com dificuldade", "Não"], key="escada_esq")

    if st.button("Ver resultado"):
        def nota(resp):
            return 0 if resp == "Sim" else (1 if resp == "Com dificuldade" else 2)

        score = nota(direita) + nota(esquerda)

        if score == 0:
            st.success("✅ Força e equilíbrio nas pernas preservados.")
        elif score <= 2:
            st.warning("⚠️ Leve dificuldade percebida. Pode indicar desequilíbrio muscular.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,dor ou dificuldade pra caminhar**")
        else:
            st.error("🚨 Dificuldade significativa. Avaliação profissional pode ser indicada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,trauma ou queda,dor ou dificuldade pra caminhar**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Levantar do Chão":
    st.subheader("🧍‍♂️ Teste de Mobilidade: Levantar do Chão sem Apoio")

    st.markdown("""
    Este teste avalia **mobilidade, força e controle corporal**.

    ### Como fazer:
    1. Sente-se no chão, com as pernas cruzadas ou semiflexionadas.
    2. Tente **levantar-se sem usar as mãos**, apenas com apoio nas pernas.
    3. Se precisar, use as mãos **o mínimo possível**.

    Depois, responda:
    """)

    apoio = st.radio("Para se levantar do chão, você usou:", [
        "Apenas as pernas (sem mãos)",
        "Uma das mãos",
        "Ambas as mãos ou precisei de apoio externo"
    ])

    idade = st.session_state.get("idade", 30)

    if st.button("Ver resultado"):
        if apoio == "Apenas as pernas (sem mãos)":
            st.success("✅ Excelente mobilidade e força funcional.")
        elif apoio == "Uma das mãos":
            st.warning("⚠️ Leve dificuldade funcional. Normal em algumas pessoas.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força**")
        else:
            st.error("🚨 Mobilidade comprometida. Pode indicar fraqueza ou limitação funcional.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Formigamento ou perda de força,dor na perna ou dificuldade pra caminhar**")

        if idade > 60 and apoio != "Apenas as pernas (sem mãos)":
            st.markdown("👴 Em pessoas acima de 60 anos, esse tipo de teste é um forte preditor de risco de quedas.")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Cor da Urina":
    st.subheader("💧 Teste Visual da Cor da Urina")

    st.markdown("""
    A cor da urina pode indicar **nível de hidratação e funcionamento dos rins**.

    ### Como fazer:
    Observe sua urina na próxima ida ao banheiro e escolha abaixo a cor mais próxima.
    """)

    cor = st.radio("Qual cor mais se parece com a sua urina?", [
        "Transparente ou amarelo-claro",
        "Amarelo forte",
        "Amarelo escuro ou âmbar",
        "Laranja ou marrom",
        "Vermelha ou com sangue visível"
    ])

    if st.button("Ver resultado"):
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
            st.markdown("🔎 Possíveis sintomas relacionados: **Infecção urinária,dor ou dificuldade ao urinar**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Pele e Coceira":
    st.subheader("🧴 Autoavaliação de Manchas ou Coceiras na Pele")

    st.markdown("""
    A pele pode mostrar sinais de **alergias, infecções ou problemas circulatórios**.

    ### Como fazer:
    Observe o corpo (braços, pernas, tronco, rosto) e responda:
    """)

    alteracoes = st.multiselect("Você percebeu recentemente:", [
        "Manchas vermelhas ou escuras",
        "Coceira frequente",
        "Descamação ou ressecamento excessivo",
        "Lesões que não cicatrizam",
        "Nada disso"
    ])

    if st.button("Ver resultado"):
        if not alteracoes or "Nada disso" in alteracoes:
            st.success("✅ Nenhuma alteração cutânea perceptível no momento.")
        elif "Lesões que não cicatrizam" in alteracoes:
            st.error("🚨 Lesões persistentes precisam ser avaliadas por um dermatologista.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Lesões na pele,infecção em ferida**")
            st.markdown("🔎 Possíveis sintomas relacionados: **Manchas anormais na pele, Infecção em ferida,lesões na pele, alergia cutânea**")
        elif len(alteracoes) >= 2:
            st.warning("⚠️ Múltiplos sinais de alteração cutânea. Fique atento e monitore a evolução.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Coceira, Infecção em ferida,lesões na pele,alergia cutânea**")
        else:
            st.info("🔎 Pequena alteração percebida. Se persistir por dias, procure um profissional.")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Digestão":
    st.subheader("🍽️ Teste de Sensações Pós-Refeição")

    st.markdown("""
    Este teste verifica se você apresenta sintomas digestivos frequentes.

    ### Após uma refeição comum, você sente:
    """)

    sintomas = st.multiselect("Marque os sintomas que você costuma sentir:", [
        "Azia ou queimação no peito",
        "Empachamento (sensação de peso)",
        "Arroto frequente",
        "Inchaço abdominal ou gases",
        "Nada disso"
    ])

    if st.button("Ver resultado"):
        if not sintomas or "Nada disso" in sintomas:
            st.success("✅ Digestão aparentemente normal.")
        elif len(sintomas) == 1:
            st.info("🔎 Sintoma isolado. Observe se repete com frequência.")
        elif len(sintomas) == 2:
            st.warning("⚠️ Sinais de desconforto digestivo recorrente. Pode estar ligado à alimentação.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Gases,dor abdominal**")
        else:
            st.error("🚨 Múltiplos sintomas digestivos. Avaliação médica pode ser indicada.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Gases,dor abdominal,diarreia,náusea e enjoo**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Ritmo Intestinal":
    st.subheader("🚽 Teste de Ritmo Intestinal")

    st.markdown("""
    O ritmo das evacuações é um importante sinal de **saúde digestiva**.

    ### Como é o seu padrão?
    """)

    freq = st.radio("Quantas vezes por semana você evacua (defeca)?", [
        "Todos os dias", "4 a 6 vezes por semana", "1 a 3 vezes por semana", "Menos de 1 vez por semana"
    ])

    aspecto = st.radio("Como costuma ser a consistência das fezes?", [
        "Macias / normais", "Muito duras", "Muito moles ou líquidas", "Varia bastante"
    ])

    if st.button("Ver resultado"):
        risco = 0
        if freq in ["1 a 3 vezes por semana", "Menos de 1 vez por semana"]:
            risco += 1
        if aspecto in ["Muito duras", "Muito moles ou líquidas", "Varia bastante"]:
            risco += 1

        if risco == 0:
            st.success("✅ Ritmo e consistência normais. Ótimo!")
        elif risco == 1:
            st.warning("⚠️ Leve alteração no ritmo ou consistência. Observe nos próximos dias.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Diarreia**")
        else:
            st.error("🚨 Alterações importantes. Pode ser bom conversar com um profissional.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Diarreia,sangramento gastrointestinal,sangramento retal**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Energia Matinal":
    st.subheader("☕ Teste de Energia ao Acordar")

    st.markdown("""
    Esse teste ajuda a identificar **níveis de fadiga e alerta ao longo do dia**.

    ### Responda com sinceridade:
    """)

    sono = st.radio("Você costuma acordar...", [
        "Descansado(a) e disposto(a)",
        "Com leve cansaço",
        "Muito cansado(a), mesmo dormindo bem"
    ])

    cafe = st.radio("Você precisa de café ou estimulante para funcionar pela manhã?", ["Não", "Às vezes", "Todos os dias"])

    if st.button("Ver resultado"):
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

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Humor e Ansiedade":
    st.subheader("🧠 Teste de Humor e Pensamentos Acelerados")

    st.markdown("""Este teste ajuda a refletir sobre **aspectos emocionais e mentais recentes**.""")

    st.markdown(""" Como você tem se sentido nos últimos 7 dias?""")
    
    humor = st.slider("Numa escala de 0 a 10, como está seu humor geral?", 0, 10, 5)
    acelerado = st.radio("Você tem tido pensamentos acelerados ou dificuldade de desligar a mente?", ["Não", "Às vezes", "Sim, com frequência"])
    sono = st.radio("Tem dormido bem?", ["Sim", "Sono leve ou interrompido", "Insônia ou dificuldade para dormir"])

    if st.button("Ver resultado"):
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

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Humor na última semana":
    st.subheader("🧠 Avaliação de Humor nos Últimos 7 Dias")
    st.write("Pense em como você se sentiu em cada um dos últimos 7 dias. Avalie seu humor em uma escala de 1 a 5:")

    humor_dias = []
    for i in range(1, 8):
        nota = st.slider(f"Dia {i}", min_value=1, max_value=5, value=3, key=f"humor_dia_{i}")
        humor_dias.append(nota)

    if st.button("Ver resultado de humor"):
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
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Variação de Peso (Últimos 30 Dias)":
    st.subheader("⚖️ Variação de Peso nos Últimos 30 Dias")
    peso_atual = st.number_input("Digite seu peso atual (kg):", min_value=20.0, max_value=300.0, step=0.1)
    peso_passado = st.number_input("Digite seu peso de 30 dias atrás (kg):", min_value=20.0, max_value=300.0, step=0.1)

    if st.button("Ver resultado de variação"):
        variacao = peso_atual - peso_passado
        percentual = (abs(variacao) / peso_passado) * 100 if peso_passado != 0 else 0

        st.markdown(f"📉 Variação: **{variacao:.1f} kg** ({percentual:.1f}%)")

        if percentual < 2:
            st.success("✅ Variação dentro da faixa esperada.")
        elif percentual <= 5:
            st.info("⚠️ Pequena variação detectada. Fique atento(a).")
            st.markdown("🔎 Possíveis sintomas relacionados: **Náusea ou enjoo, Ansiedade ou agitação intensa, Comportamento estranho à normalidade**")
        else:
            st.warning("🚨 Variação significativa! Considere investigar causas clínicas ou comportamentais.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Náusea ou enjoo, Hiperglicemia, Hipoglicemia, Ansiedade ou agitação intensa, Comportamento estranho à normalidade**")
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Audição (Detecção de Som)":
    st.subheader("🔊 Teste de Detecção de Som")

    st.info("Use fones de ouvido. Ajuste o volume para um nível confortável.")

    if st.button("▶️ Tocar som de teste"):
        st.audio("https://raw.githubusercontent.com/brenaldo19/Sistemainteligenteaconselhamentomedico/main/bip_bip_1000Hz_4s.mp3", format="audio/mp3")  # Som leve de bip

    resposta = st.radio("Você conseguiu ouvir o som com clareza?", ["Sim", "Não", "Somente em um dos ouvidos"])
    if resposta != "":
        if resposta == "Não" or resposta == "Somente em um dos ouvidos":
            st.warning("⚠️ Sinal de Alteração na audição.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alteração na audição**")
        else:
            st.success("✅ Tudo certo com sua audição.")

elif opcao == "Autotestes para apuração de sintoma" and subteste ==  "Audição (Frequências Altas e Baixas)":
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

    resposta = st.radio("Você ouviu todos os sons com clareza?", ["Sim", "Não ouvi o grave (250 Hz)", "Não ouvi o médio", "Não ouvi o agudo (8000 Hz)"])
    if resposta != "Sim":
        st.warning("⚠️ Pode indicar perda auditiva seletiva.")
        st.markdown("🔎 Possíveis sintomas relacionados: **Alteração na audição**")
    else:
        st.success("✅ Sem alterações aparentes.")

def montar_mensagem_final(media_real, idade, imc, sexo, gravida, grupo_risco):
    media_esperada = calcular_media_esperada(idade, imc, sexo, gravida, grupo_risco)
    margem = media_esperada * 0.25
    limite_inferior = media_esperada - margem
    limite_superior = media_esperada + margem

    # Avaliação
    if media_real < limite_inferior:
        avaliacao = "⏱️ Seu tempo médio de reação foi **mais rápido** que o esperado para o seu perfil."
    elif media_real > limite_superior:
        avaliacao = "⏱️ Seu tempo médio de reação foi **mais lento** que o esperado para o seu perfil."
    else:
        avaliacao = "⏱️ Seu tempo médio de reação está **dentro da faixa saudável** para o seu perfil."

    # Construindo descrição do perfil
    if idade <= 7:
        faixa_idade = "crianças pequenas"
    elif idade <= 16:
        faixa_idade = "adolescentes"
    elif idade <= 35:
        faixa_idade = "jovens adultos"
    elif idade <= 58:
        faixa_idade = "adultos"
    else:
        faixa_idade = "pessoas idosas"

    if imc < 16:
        imc_descr = "baixo peso importante"
    elif imc < 30:
        imc_descr = "IMC dentro do intervalo saudável"
    else:
        imc_descr = "IMC acima do ideal"

    perfil = f"🧬 Perfil estimado: {faixa_idade}, sexo {sexo.lower()}, {imc_descr}"
    if gravida:
        perfil += ", gestante"

    return f"{avaliacao}\n\n{perfil}"

    # --- RESULTADO FINAL ---
    if st.session_state.tentativa > 9:
        st.markdown("---")
        st.subheader("📊 Resultados Finais")

        for i, r in enumerate(st.session_state.resultados, start=1):
            st.write(f"{i}️⃣: ⏱️ {r:.2f} segundos")

        media_usuario = sum(st.session_state.resultados) / len(st.session_state.resultados)
        st.success(f"🏁 Média final: **{media_usuario:.2f} segundos**")
    mensagem_avaliacao = avaliar_resultado(media_real, idade, imc, sexo, gravida, grupo_risco)
    st.markdown(mensagem_avaliacao)

# Funções já existentes



def calcular_cor_final(cores, sintomas, sistemas_sintomas):
    ordem_cores = ["verde", "amarelo", "laranja", "vermelho"]

    # 1. Encontra a cor mais grave
    cor_base = max(cores, key=lambda c: ordem_cores.index(c))

    # 2. Conta sintomas por sistema
    contador_por_sistema = {}
    for sistema, lista in sistemas_sintomas.items():
        sintomas_sistema = [s.lower() for s in lista]
        contador = sum(1 for s in sintomas if s.lower() in sintomas_sistema)
        contador_por_sistema[sistema] = contador

    # 3. Aplica regras de reforço
    reforco = 0
    for sistema, qtd in contador_por_sistema.items():
        if sistema in ["neurológico", "cardíaco"]:
            if qtd >= 3:
                reforco = max(reforco, 2)
            elif qtd == 2:
                reforco = max(reforco, 1)
        elif qtd >= 3:
            reforco = max(reforco, 1)

    # 4. Ajusta a cor final
    idx = ordem_cores.index(cor_base)
    cor_final = ordem_cores[min(idx + reforco, len(ordem_cores) - 1)]

    return cor_final


# >>> MOTOR DE FLUXOGRAMAS (DEVE VIR ANTES DA ETAPA 3) <<<
FLUXOS = {}  # catálogo pode começar vazio

def coletar_respostas_fluxo(sintoma_label):
    chave = normalizar(sintoma_label)
    cfg = FLUXOS.get(chave)
    if not cfg:
        return None  # este sintoma não usa o motor novo

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
        elif tipo == "checkbox":
            score += sum(opcoes.get(x, 0.0) for x in (r or []))
        elif tipo == "multiselect":
            score += sum(opcoes.get(x, 0.0) for x in (r or []))

    cor_base = score_para_cor(score, cfg["mapeamento_cor"])

    min_cor = None
    for regra in cfg.get("regras_excecao", []):
        cond = regra["se"]
        ok = True
        for k, v in cond.items():
            resp = respostas.get(k)
            if isinstance(v, list):  # precisa conter algum desses valores
                if not resp:
                    ok = False
                elif isinstance(resp, list):
                    if not any(x in resp for x in v):
                        ok = False
                else:
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
    # retorna os labels humanos de todos os fluxos
    out = []
    for k, cfg in FLUXOS.items():
        lbl = cfg.get("label")
        if not lbl:
            # fallback: tenta “des-normalizar” algo legível
            lbl = k.replace("_", " ").title()
        out.append(lbl)
    return out

def eh_fluxo(label):
    # diz se um label selecionado existe como fluxo
    return normalizar(label) in FLUXOS



FLUXOS = {}

# --- Fluxograma: ---
FLUXOS[normalizar("Inchaço dos linfonodos")] = {
    "label": "Inchaço dos linfonodos",
    "perguntas": [
        {
            "id": "febre_peso",
            "label": "Há febre ou perda de peso recente?",
            "tipo": "radio",
            "opcoes": {
                "Febre alta (≥ 38,5°C) OU perda de peso > 10% em 6 meses": 1.8,
                "Febre baixa (37,8–38,4°C) OU perda de peso moderada": 0.9,
                "Sem febre e sem perda de peso": 0.0
            }
        },
        {
            "id": "dor_inflamacao",
            "label": "O linfonodo está doloroso ou com sinais de inflamação (vermelho/quente)?",
            "tipo": "radio",
            "opcoes": {
                "Doloroso com vermelhidão/calor": 1.0,
                "Doloroso, sem vermelhidão": 0.5,
                "Sem dor/inflamação": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo percebe o inchaço?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 1.2,
                "Entre 2 e 4 semanas": 0.6,
                "Menos de 2 semanas": 0.2
            }
        },
        {
            "id": "localizacao",
            "label": "Onde estão os linfonodos inchados?",
            "tipo": "radio",
            "opcoes": {
                "Generalizado (em mais de uma região do corpo)": 1.2,
                "Localizado (apenas uma região)": 0.4
            }
        },
        {
            "id": "tamanho",
            "label": "Tamanho aproximado do maior linfonodo:",
            "tipo": "radio",
            "opcoes": {
                "≥ 2 cm": 1.2,
                "1 a 2 cm": 0.5,
                "< 1 cm": 0.2
            }
        },
        {
            "id": "consistencia_mobilidade",
            "label": "Como ele parece ao toque?",
            "tipo": "radio",
            "opcoes": {
                "Duro e fixo (pouco móvel)": 1.6,
                "Borracha/móvel": 0.4,
                "Macio": 0.1
            }
        },
        {
            "id": "sintomas_associados",
            "label": "Sintomas associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Suor noturno": 0.8,
                "Coceira no corpo (prurido) sem explicação": 0.4,
                "Cansaço/fadiga persistente": 0.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Infecção ou ferida recente perto do local": 0.4,
                "Uso crônico de corticoide ou quimioterapia": 0.7,
                "Imunossupressão/HIV": 0.9
            }
        }
    ],
    "regras_excecao": [
        {"se": {"febre_peso": "Febre alta (≥ 38,5°C) OU perda de peso > 10% em 6 meses", "duracao": "Mais de 4 semanas"}, "min_cor": "laranja"},
        {"se": {"tamanho": "≥ 2 cm", "consistencia_mobilidade": "Duro e fixo (pouco móvel)"}, "min_cor": "laranja"},
        {"se": {"localizacao": "Generalizado (em mais de uma região do corpo)", "febre_peso": ["Febre alta (≥ 38,5°C) OU perda de peso > 10% em 6 meses", "Febre baixa (37,8–38,4°C) OU perda de peso moderada"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (4.0, "laranja"),
        (2.2, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Nódulo na mama (conservador, com sinais específicos moderados)
FLUXOS[normalizar("Nódulo na mama")] = {
    "label": "Nódulo na mama",
    "perguntas": [
        {
            "id": "caracteristica",
            "label": "Qual a característica principal do nódulo?",
            "tipo": "radio",
            "opcoes": {
                "Nódulo crescente ou com secreção": 1.8,
                "Nódulo duro, fixo ou irregular": 1.6,
                "Nódulo doloroso, mas recente": 1.0,
                "Pequeno nódulo móvel, sem dor": 0.8
            }
        },
        {
            "id": "tempo",
            "label": "Há quanto tempo você notou o nódulo?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 1.0,
                "Entre 2 e 4 semanas": 0.6,
                "Menos de 2 semanas": 0.3
            }
        },
        {
            "id": "alteracoes_pele",
            "label": "Há alterações na pele sobre o nódulo?",
            "tipo": "radio",
            "opcoes": {
                "Retração da pele ou aspecto de casca de laranja": 1.2,
                "Vermelhidão ou calor local": 0.7,   # leve redução
                "Sem alterações visíveis": 0.0
            }
        },
        {
            "id": "secrecao_mamilo",
            "label": "Há secreção pelo mamilo?",
            "tipo": "radio",
            "opcoes": {
                "Com sangue": 1.5,
                "Transparente ou leitosa (fora do período de lactação)": 0.9,  # leve redução
                "Sem secreção": 0.0
            }
        },
        {
            "id": "sinais_locais_associados",
            "label": "Sinais locais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Nódulo em axila do mesmo lado": 0.7,
                "Alteração recente do mamilo (inversão/ferida)": 0.8,
                "Aumento de volume/assimetria súbita da mama": 0.6,
                "Dor não cíclica persistente": 0.4
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico familiar de câncer de mama": 1.1,   # leve redução
                "Uso prolongado de terapia hormonal": 0.5,     # leve redução
                "Imunossupressão": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"caracteristica": "Nódulo crescente ou com secreção", "tempo": "Mais de 4 semanas"}, "min_cor": "laranja"},
        {"se": {"caracteristica": "Nódulo duro, fixo ou irregular", "alteracoes_pele": "Retração da pele ou aspecto de casca de laranja"}, "min_cor": "laranja"},
        {"se": {"secrecao_mamilo": "Com sangue"}, "min_cor": "laranja"},
        {"se": {"sinais_locais_associados": ["Nódulo em axila do mesmo lado"], "caracteristica": "Nódulo duro, fixo ou irregular"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.5, "vermelho"),
        (4.0, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Nódulo testicular (conservador, com sinais específicos moderados)
FLUXOS[normalizar("Nódulo testicular")] = {
    "label": "Nódulo testicular",
    "perguntas": [
        {
            "id": "caracteristica",
            "label": "Qual a característica principal do nódulo?",
            "tipo": "radio",
            "opcoes": {
                "Nódulo firme e indolor, perceptível há dias": 1.7,  # leve redução
                "Nódulo doloroso ou com inchaço": 0.9,               # leve redução
                "Mudança recente no tamanho do testículo": 0.9,      # leve redução
                "Sensação de caroço pequeno e móvel": 0.7            # leve redução
            }
        },
        {
            "id": "tempo",
            "label": "Há quanto tempo você notou o nódulo?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 0.9,   # leve redução
                "Entre 2 e 4 semanas": 0.6,
                "Menos de 2 semanas": 0.3
            }
        },
        {
            "id": "sinais_associados_especificos",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Endurecimento de parte do testículo": 0.8,
                "Aumento rápido do volume testicular": 0.9,
                "Sensação de peso no escroto": 0.5,
                "Dor surda em baixo-ventre/virilha": 0.6,
                "Aumento de mamas ou sensibilidade mamilar": 0.5
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico familiar de câncer testicular": 1.1,  # leve redução
                "Criptorquidia (testículo não descido)": 0.9,    # leve redução
                "Imunossupressão": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"caracteristica": "Nódulo firme e indolor, perceptível há dias", "tempo": "Mais de 4 semanas"}, "min_cor": "laranja"},
        {"se": {"sinais_associados_especificos": ["Aumento rápido do volume testicular"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados_especificos": ["Endurecimento de parte do testículo"], "tempo": "Mais de 4 semanas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Dor nos testículos (conservador)
FLUXOS[normalizar("Dor nos testículos")] = {
    "label": "Dor nos testículos",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Quando a dor começou?",
            "tipo": "radio",
            "opcoes": {
                "Início súbito, forte, há menos de 6 horas": 1.8,
                "Início súbito, forte, há mais de 6 horas": 1.5,
                "Início gradual, moderada": 1.0,
                "Dor leve e esporádica": 0.5
            }
        },
        {
            "id": "localizacao",
            "label": "Onde sente a dor?",
            "tipo": "radio",
            "opcoes": {
                "Apenas em um testículo": 0.6,
                "Nos dois testículos": 0.8,
                "Difusa no baixo-ventre/virilha": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Inchaço visível": 0.8,
                "Vermelhidão ou calor no escroto": 0.8,
                "Náusea ou vômito junto da dor": 0.9,
                "Febre": 0.7
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de trauma na região": 0.6,
                "Criptorquidia (testículo não descido)": 0.9,
                "Infecção urinária recente": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio": "Início súbito, forte, há menos de 6 horas"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Náusea ou vômito junto da dor"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Secreção mamilar (conservador)
FLUXOS[normalizar("Secreção mamilar")] = {
    "label": "Secreção mamilar",
    "perguntas": [
        {
            "id": "tipo_secrecao",
            "label": "Qual o tipo da secreção?",
            "tipo": "radio",
            "opcoes": {
                "Com sangue": 1.8,
                "Transparente ou leitosa (fora da amamentação)": 1.2,
                "Amarelada ou esverdeada": 0.8,
                "Aquosa clara": 0.5
            }
        },
        {
            "id": "quantidade",
            "label": "A secreção é:",
            "tipo": "radio",
            "opcoes": {
                "Contínua ou espontânea (sem apertar)": 1.0,
                "Apenas quando comprimida": 0.5
            }
        },
        {
            "id": "lado",
            "label": "De qual lado ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Apenas em uma mama": 0.7,
                "Em ambas as mamas": 0.5
            }
        },
        {
            "id": "sinais_locais",
            "label": "Sinais locais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Retração do mamilo": 0.9,
                "Ferida ou crosta no mamilo": 0.8,
                "Nódulo palpável na mama": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico familiar de câncer de mama": 1.1,
                "Uso prolongado de terapia hormonal": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"tipo_secrecao": "Com sangue"}, "min_cor": "laranja"},
        {"se": {"sinais_locais": ["Nódulo palpável na mama"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.5, "vermelho"),
        (4.0, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Dor nos testículos (conservador)
FLUXOS[normalizar("Dor nos testículos")] = {
    "label": "Dor nos testículos",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Quando a dor começou?",
            "tipo": "radio",
            "opcoes": {
                "Início súbito, forte, há menos de 6 horas": 1.8,
                "Início súbito, forte, há mais de 6 horas": 1.5,
                "Início gradual, moderada": 1.0,
                "Dor leve e esporádica": 0.5
            }
        },
        {
            "id": "localizacao",
            "label": "Onde sente a dor?",
            "tipo": "radio",
            "opcoes": {
                "Apenas em um testículo": 0.6,
                "Nos dois testículos": 0.8,
                "Difusa no baixo-ventre/virilha": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Inchaço visível": 0.8,
                "Vermelhidão ou calor no escroto": 0.8,
                "Náusea ou vômito junto da dor": 0.9,
                "Febre": 0.7
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de trauma na região": 0.6,
                "Criptorquidia (testículo não descido)": 0.9,
                "Infecção urinária recente": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio": "Início súbito, forte, há menos de 6 horas"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Náusea ou vômito junto da dor"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Secreção mamilar (conservador)
FLUXOS[normalizar("Secreção mamilar (Fora da amamentação)")] = {
    "label": "Secreção mamilar (Fora da amamentação)",
    "perguntas": [
        {
            "id": "tipo_secrecao",
            "label": "Qual o tipo da secreção?",
            "tipo": "radio",
            "opcoes": {
                "Com sangue": 1.8,
                "Transparente ou leitosa (fora da amamentação)": 1.2,
                "Amarelada ou esverdeada": 0.8,
                "Aquosa clara": 0.5
            }
        },
        {
            "id": "quantidade",
            "label": "A secreção é:",
            "tipo": "radio",
            "opcoes": {
                "Contínua ou espontânea (sem apertar)": 1.0,
                "Apenas quando comprimida": 0.5
            }
        },
        {
            "id": "lado",
            "label": "De qual lado ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Apenas em uma mama": 0.7,
                "Em ambas as mamas": 0.5
            }
        },
        {
            "id": "sinais_locais",
            "label": "Sinais locais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Retração do mamilo": 0.9,
                "Ferida ou crosta no mamilo": 0.8,
                "Nódulo palpável na mama": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico familiar de câncer de mama": 1.1,
                "Uso prolongado de terapia hormonal": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"tipo_secrecao": "Com sangue"}, "min_cor": "laranja"},
        {"se": {"sinais_locais": ["Nódulo palpável na mama"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.5, "vermelho"),
        (4.0, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Sangue no sêmen (hemospermia) — conservador
FLUXOS[normalizar("Sangue no sêmen")] = {
    "label": "Sangue no sêmen",
    "perguntas": [
        {
            "id": "frequencia",
            "label": "Com que frequência você notou sangue no sêmen?",
            "tipo": "radio",
            "opcoes": {
                "Em vários episódios recentes": 1.6,
                "Em 2–3 episódios": 1.2,
                "Apenas uma vez": 0.6
            }
        },
        {
            "id": "contexto",
            "label": "Houve algum evento relacionado?",
            "tipo": "radio",
            "opcoes": {
                "Após trauma ou procedimento urológico recente": 0.9,
                "Sem relação aparente": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sintomas associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Dor ao ejacular": 0.8,
                "Dor ou dificuldade ao urinar (ardor)": 0.7,
                "Febre": 0.7,
                "Sangue na urina": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "IST recente ou parceiro com IST": 0.9,
                "Idade acima de 40 anos": 0.6,
                "Histórico de prostatite": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"frequencia": "Em vários episódios recentes", "sinais_associados": ["Febre"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Sangue na urina"]}, "min_cor": "laranja"},
        {"se": {"contexto": "Após trauma ou procedimento urológico recente", "sinais_associados": ["Dor ao ejacular"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Trauma craniano
FLUXOS[normalizar("Trauma na cabeça")] = {
    "label": "Trauma na cabeça",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Qual foi a gravidade percebida do trauma?",
            "tipo": "radio",
            "opcoes": {
                "Batida forte com perda de consciência, vômito ou amnésia": 3.5,
                "Batida com dor de cabeça intensa e tontura": 2.0,
                "Batida leve com dor local": 1.0,
                "Topada leve, sem sintomas associados": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu a pancada?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24h": 1.0,
                "Entre 1 e 7 dias": 0.5,
                "Mais de 7 dias": 0.2
            }
        },
        {
            "id": "sintomas_associados",
            "label": "Sintomas associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Confusão mental ou fala enrolada": 1.5,
                "Alteração visual": 1.2,
                "Fraqueza em braço/perna": 1.5,
                "Sonolência excessiva": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Batida forte com perda de consciência, vômito ou amnésia"}, "min_cor": "vermelho"},
        {"se": {"gravidade": "Batida com dor de cabeça intensa e tontura"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Manchas anormais na pele
FLUXOS[normalizar("Manchas anormais na pele")] = {
    "label": "Manchas anormais na pele",
    "perguntas": [
        {
            "id": "aspecto",
            "label": "Qual é o aspecto da mancha?",
            "tipo": "radio",
            "opcoes": {
                "Mancha escura irregular com crescimento rápido": 3.5,
                "Ferida que não cicatriza com bordas elevadas": 2.5,
                "Mancha vermelha com descamação e coceira": 1.5,
                "Mancha clara e estável, sem outros sintomas": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo está presente?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 1.0,
                "Entre 2 e 4 semanas": 0.5,
                "Menos de 2 semanas": 0.2
            }
        },
        {
            "id": "alteracoes",
            "label": "Houve mudanças recentes na aparência?",
            "tipo": "radio",
            "opcoes": {
                "Mudou cor e tamanho rapidamente": 1.5,
                "Mudou lentamente": 0.7,
                "Sem mudanças perceptíveis": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"aspecto": "Mancha escura irregular com crescimento rápido"}, "min_cor": "vermelho"},
        {"se": {"aspecto": "Ferida que não cicatriza com bordas elevadas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# Fluxograma: Incontinência urinária
FLUXOS[normalizar("Incontinência urinária")] = {
    "label": "Incontinência urinária",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Qual é a gravidade do sintoma?",
            "tipo": "radio",
            "opcoes": {
                "Perda total de controle com dor ou febre": 3.5,
                "Urina escapando frequentemente sem aviso": 2.0,
                "Perda leve ao tossir ou se mexer": 1.0,
                "Pequenos escapes ocasionais sem desconforto": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo apresenta o sintoma?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 1.0,
                "Entre 2 e 4 semanas": 0.5,
                "Menos de 2 semanas": 0.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Infecção urinária recente": 0.8,
                "Cirurgia pélvica prévia": 0.7,
                "Parto vaginal múltiplo": 0.6,
                "Doença neurológica diagnosticada": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Perda total de controle com dor ou febre"}, "min_cor": "vermelho"},
        {"se": {"gravidade": "Urina escapando frequentemente sem aviso"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Coriza e espirros
FLUXOS[normalizar("Coriza e espirros")] = {
    "label": "Coriza e espirros",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Coriza intensa com dificuldade para respirar e febre alta": 3.5,
                "Espirros constantes e nariz muito entupido": 2.0,
                "Coriza leve com espirros ocasionais": 1.0,
                "Leve irritação nasal sem outros sintomas": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo os sintomas começaram?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 7 dias": 1.0,
                "Entre 2 e 7 dias": 0.5,
                "Menos de 2 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Falta de ar ao falar ou andar": 1.2,
                "Chiado no peito": 1.0,
                "Dor facial ou secreção amarela/verde": 0.9,
                "Lábios roxos": 1.5
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Asma ou DPOC": 1.0,
                "Alergia respiratória conhecida": 0.4,
                "Contato recente com pessoa doente": 0.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Coriza intensa com dificuldade para respirar e febre alta"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Lábios roxos", "Falta de ar ao falar ou andar"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Chiado no peito"], "fatores_risco": ["Asma ou DPOC"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Incontinência urinária em idosos
FLUXOS[normalizar("Incontinência urinária em idosos")] = {
    "label": "Incontinência urinária em idosos",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Qual é a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Perda total do controle urinário com febre ou confusão": 3.5,
                "Incontinência frequente e súbita, com ardência": 2.0,
                "Gotejamento ou perda leve ao se movimentar": 1.0,
                "Leves escapes ocasionais sem outros sintomas": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo isso ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 semanas": 1.0,
                "Entre 2 e 4 semanas": 0.5,
                "Menos de 2 semanas": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Dor/ardência ao urinar": 0.8,
                "Dor no baixo-ventre": 0.5,
                "Confusão ou sonolência": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Cateter vesical recente": 0.8,
                "Imobilidade ou queda recente": 0.5,
                "Início/ajuste de medicamento (diurético/sedativo)": 0.6,
                "Histórico de incontinência prévia": 0.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Perda total do controle urinário com febre ou confusão"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Febre", "Dor/ardência ao urinar"]}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Cateter vesical recente"], "sinais_associados": ["Febre"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Queda em idosos
FLUXOS[normalizar("Queda em idosos")] = {
    "label": "Queda em idosos",
    "perguntas": [
        {
            "id": "gravidade_queda",
            "label": "Como foi a queda?",
            "tipo": "radio",
            "opcoes": {
                "Queda com perda de consciência ou fratura": 3.5,
                "Queda com dor intensa ou dificuldade para se levantar": 2.0,
                "Queda leve com dor local e hematoma": 1.0,
                "Tombos esporádicos sem dor ou lesão": 0.0
            }
        },
        {
            "id": "cabeca",
            "label": "Houve batida na cabeça?",
            "tipo": "radio",
            "opcoes": {
                "Sim, bateu a cabeça": 1.2,
                "Não bateu a cabeça": 0.0
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Dor em quadril ou incapacidade de apoiar o peso": 1.2,
                "Uso de anticoagulante": 1.0,
                "Tontura persistente": 0.8,
                "Corte/laceração com sangramento": 0.6
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24h": 1.0,
                "Entre 1 e 7 dias": 0.5,
                "Mais de 7 dias": 0.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade_queda": "Queda com perda de consciência ou fratura"}, "min_cor": "vermelho"},
        {"se": {"cabeca": "Sim, bateu a cabeça", "sinais_associados": ["Uso de anticoagulante"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Dor em quadril ou incapacidade de apoiar o peso"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Delírio em idosos
FLUXOS[normalizar("Delírio em idosos")] = {
    "label": "Delírio em idosos",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual situação descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Desorientação súbita com agitação ou alucinações": 3.5,
                "Confusão mental com alteração de comportamento e/ou flutuação de consciência": 2.0,
                "Esquecimento leve e dificuldade para responder": 1.0,
                "Ligeira confusão passageira, mas estável": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Quando começaram as alterações?",
            "tipo": "radio",
            "opcoes": {
                "Nas últimas 24h": 1.0,
                "Há 2–7 dias": 0.6,
                "Há mais de 7 dias": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Urina com ardor/cheiro forte": 0.7,
                "Sonolência excessiva": 1.0,
                "Fala enrolada": 1.0,
                "Queda recente": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "Algum fator desencadeante se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Uso recente de sedativos/antialérgicos": 0.7,
                "Desidratação (boca seca, pouca urina)": 0.8,
                "Infecção conhecida (urina/pulmão)": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Desorientação súbita com agitação ou alucinações"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Fala enrolada", "Sonolência excessiva"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Febre"], "fatores": ["Infecção conhecida (urina/pulmão)"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Trauma grave
FLUXOS[normalizar("Trauma grave")] = {
    "label": "Trauma grave",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Qual foi a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Acidente com perda de consciência, fratura exposta ou sangramento grave": 3.5,
                "Queda ou impacto com dor intensa e possível fratura": 2.0,
                "Batida com dor localizada e hematoma": 1.0,
                "Pequeno impacto sem dor ou limitação": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu o trauma?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24h": 1.0,
                "Entre 1 e 7 dias": 0.5,
                "Mais de 7 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Deformidade evidente no membro": 1.2,
                "Incapacidade de apoiar o peso": 1.2,
                "Sangramento ativo": 1.5,
                "Ferida profunda/laceração extensa": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulante": 1.0,
                "Idade ≥ 65 anos": 0.6,
                "Trauma em múltiplas regiões (politrauma)": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Acidente com perda de consciência, fratura exposta ou sangramento grave"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Sangramento ativo"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Deformidade evidente no membro", "Incapacidade de apoiar o peso"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Dor de garganta
FLUXOS[normalizar("Dor de garganta")] = {
    "label": "Dor de garganta",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Dor forte com dificuldade de engolir e febre alta": 3.2,
                "Dor moderada com placas ou pus visível": 2.0,
                "Irritação leve e dificuldade discreta": 1.0,
                "Leve desconforto ao falar ou engolir": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo começou?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 4 dias": 0.9,
                "Entre 2 e 4 dias": 0.5,
                "Menos de 2 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Placas/pus nas amígdalas": 1.0,
                "Dificuldade para engolir saliva (baba)": 1.2,
                "Voz abafada ('batata quente')": 1.2,
                "Falta de ar": 1.2
            }
        },
        {
            "id": "fatores",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Contato estreito com pessoa doente": 0.4,
                "Imunossupressão": 0.8,
                "Ausência de tosse": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor forte com dificuldade de engolir e febre alta"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Dificuldade para engolir saliva (baba)", "Voz abafada ('batata quente')", "Falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Placas/pus nas amígdalas"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Dor de dente
FLUXOS[normalizar("Dor de dente")] = {
    "label": "Dor de dente",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Dor forte com inchaço no rosto ou febre": 3.2,
                "Dor intensa ao mastigar ou à noite": 2.0,
                "Dor leve com sensibilidade ao frio/quente": 1.0,
                "Leve incômodo eventual": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo sente essa dor?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 7 dias": 0.9,
                "Entre 2 e 7 dias": 0.5,
                "Menos de 2 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Secreção purulenta na gengiva": 1.0,
                "Trismo (dificuldade para abrir a boca)": 1.0,
                "Irradiação da dor para face/orelha": 0.6,
                "Gengiva muito inchada e dolorida": 0.7
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Diabetes descompensado": 0.8,
                "Imunossupressão": 0.8,
                "Extração/dente manipulado recente": 0.7
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor forte com inchaço no rosto ou febre"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Trismo (dificuldade para abrir a boca)"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Secreção purulenta na gengiva"], "duracao": "Mais de 7 dias"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Alteração na audição
FLUXOS[normalizar("Alteração na audição")] = {
    "label": "Alteração na audição",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Perda súbita da audição com zumbido ou dor": 3.5,
                "Diminuição importante da audição com secreção": 2.0,
                "Sensação de ouvido tampado leve": 1.0,
                "Alteração momentânea após barulho ou pressão": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo percebeu a alteração?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 48h": 1.0,
                "Entre 2 e 7 dias": 0.6,
                "Mais de 7 dias": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Vertigem intensa (rodação)": 1.2,
                "Secreção purulenta": 1.0,
                "Febre": 0.7,
                "Dor no ouvido importante": 0.8
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Exposição recente a barulho muito alto": 0.8,
                "Mudança de pressão (voo/mergulho)": 0.8,
                "Infecção respiratória recente": 0.6,
                "Entrada de água/trauma no ouvido": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Perda súbita da audição com zumbido ou dor"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Vertigem intensa (rodação)"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Secreção purulenta", "Febre"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Mordedura
FLUXOS[normalizar("Mordedura")] = {
    "label": "Mordedura",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Mordida profunda com sangramento e suspeita de raiva": 3.5,
                "Mordida com dor e sinais de infecção": 2.0,
                "Mordida superficial com inchaço": 1.0,
                "Pequeno arranhão sem dor": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu a mordida?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24h": 1.0,
                "Entre 1 e 3 dias": 0.6,
                "Mais de 3 dias": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Sangramento ativo difícil de estancar": 1.5,
                "Ferida profunda/laceração extensa": 1.0,
                "Secreção purulenta": 1.0,
                "Febre": 0.8
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Animal desconhecido/não vacinado": 1.2,
                "Mordida em mão/face/genitália": 1.0,
                "Diabetes ou imunossupressão": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Mordida profunda com sangramento e suspeita de raiva"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Sangramento ativo difícil de estancar"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Secreção purulenta"], "tempo": "Entre 1 e 3 dias"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Queimaduras
FLUXOS[normalizar("Queimaduras")] = {
    "label": "Queimaduras",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Queimadura extensa, com bolhas e pele escura": 3.5,
                "Queimadura moderada com bolhas e dor intensa": 2.0,
                "Queimadura pequena com vermelhidão e dor leve": 1.0,
                "Apenas vermelhidão passageira sem dor": 0.0
            }
        },
        {
            "id": "local",
            "label": "Qual local foi atingido?",
            "tipo": "radio",
            "opcoes": {
                "Face, mãos, pés, genitália ou grandes articulações": 1.2,
                "Outro local do corpo": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Bolhas grandes ou rompendo": 1.0,
                "Área escura/esbranquiçada (profunda)": 1.2,
                "Sinais de infecção (pus, piora da dor)": 1.0
            }
        },
        {
            "id": "mecanismo",
            "label": "Como aconteceu?",
            "tipo": "radio",
            "opcoes": {
                "Fogo/explosão/eletricidade/química": 1.2,
                "Líquido quente/sólido quente/sol": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Queimadura extensa, com bolhas e pele escura"}, "min_cor": "vermelho"},
        {"se": {"local": "Face, mãos, pés, genitália ou grandes articulações"}, "min_cor": "laranja"},
        {"se": {"mecanismo": "Fogo/explosão/eletricidade/química"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Ferida não-traumática
FLUXOS[normalizar("Ferida não-traumática")] = {
    "label": "Ferida não-traumática",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Ferida grande com secreção e mal cheiro": 3.0,
                "Ferida dolorosa com sinais de infecção": 2.0,
                "Ferida pequena com vermelhidão": 1.0,
                "Apenas uma mancha sem dor ou secreção": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Há quanto tempo está assim?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 2 semanas": 1.0,
                "Entre 3 e 14 dias": 0.6,
                "Menos de 3 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Aumento rápido do tamanho": 0.9,
                "Dor intensa ou mal cheiro": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Diabetes descompensado": 0.9,
                "Imobilidade ou pressão constante no local": 0.8,
                "Insuficiência venosa/arterial": 0.7
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Ferida grande com secreção e mal cheiro"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Dor intensa ou mal cheiro"]}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Diabetes descompensado"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Gases
FLUXOS[normalizar("Gases")] = {
    "label": "Gases",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o desconforto?",
            "tipo": "radio",
            "opcoes": {
                "Dor abdominal intensa com inchaço e sem alívio": 2.5,
                "Desconforto forte e barulhos intestinais altos": 1.5,
                "Flatulência frequente com leve dor": 1.0,
                "Gases leves, sem incômodo relevante": 0.0
            }
        },
        {
            "id": "tempo",
            "label": "Desde quando nota os sintomas?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 3 dias": 0.8,
                "Entre 24 e 72 horas": 0.5,
                "Menos de 24 horas": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos persistentes": 1.0,
                "Ausência de eliminação de gases/fezes": 1.2,
                "Febre": 0.7,
                "Sangue nas fezes": 1.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor abdominal intensa com inchaço e sem alívio"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Ausência de eliminação de gases/fezes"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Sangue nas fezes"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# Fluxograma: Sangramento retal
FLUXOS[normalizar("Sangramento retal")] = {
    "label": "Sangramento retal",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como foi o sangramento?",
            "tipo": "radio",
            "opcoes": {
                "Sangue vermelho vivo em grande quantidade": 3.5,
                "Sangue moderado com dor abdominal": 2.0,
                "Poucas gotas de sangue no papel higiênico": 1.0,
                "Sangramento leve e isolado": 0.2
            }
        },
        {
            "id": "tempo",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "Hoje": 1.0,
                "Há 2–7 dias": 0.6,
                "Há mais de 7 dias": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Tontura ou fraqueza": 1.0,
                "Dor anal intensa": 0.8,
                "Fezes pretas (melena)": 1.5,
                "Febre": 0.7
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulante": 1.0,
                "Cirrose/doença hepática": 0.9,
                "Constipação crônica": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Sangue vermelho vivo em grande quantidade"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Fezes pretas (melena)"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Tontura ou fraqueza"]}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Uso de anticoagulante"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
# -----------------------------
# CONFUSÃO MENTAL
# -----------------------------
# -----------------------------
# CONFUSÃO MENTAL
# -----------------------------
FLUXOS[normalizar("Confusão mental")] = {
    "label": "Confusão mental",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Desorientação completa e fala incoerente": 3.5,
                "Confusão mental com dificuldade de reconhecer pessoas ou lugares": 2.0,
                "Leve desatenção ou lapsos de memória": 1.0,
                "Ligeira distração sem prejuízo das atividades": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Início do quadro",
            "tipo": "radio",
            "opcoes": {
                "Início súbito (minutos a horas)": 1.3,
                "Instalação gradual (dias a semanas)": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Febre ou infecção recente": 1.0,
                "Dor de cabeça intensa ou rigidez na nuca": 1.3,
                "Fraqueza em um lado do corpo ou fala arrastada": 1.3,
                "Convulsão recente": 1.3,
                "Vômitos persistentes ou desidratação": 0.8
            }
        },
        {
            "id": "uso_substancias",
            "label": "Uso de substâncias/medicações",
            "tipo": "checkbox",
            "opcoes": {
                "Álcool/drogas recentemente": 0.8,
                "Início/ajuste de psicotrópicos (benzodiazepínicos/antidepressivos/antipsicóticos)": 0.8,
                "Hipoglicemiantes/insulina": 1.0
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Diabetes ou doença metabólica conhecida": 1.0,
                "Doença neurológica prévia (ex.: demência, AVC)": 1.0,
                "Imunossupressão": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Desorientação completa e fala incoerente"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Fraqueza em um lado do corpo ou fala arrastada", "Convulsão recente", "Dor de cabeça intensa ou rigidez na nuca"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Febre ou infecção recente"]}, "min_cor": "laranja"},
        {"se": {"uso_substancias": ["Hipoglicemiantes/insulina"]}, "min_cor": "laranja"},
        {"se": {"condicoes_risco": ["Idade ≤ 4 anos ou ≥ 67 anos", "Imunossupressão"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# PERDA DE CONSCIÊNCIA
# -----------------------------
FLUXOS[normalizar("Perda de consciência")] = {
    "label": "Perda de consciência",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Perda total de consciência recente sem recuperação": 3.5,
                "Desmaio com recuperação, mas com tontura persistente": 2.0,
                "Sensação de quase desmaio, mas sem queda": 1.0,
                "Nenhum episódio de perda de consciência": 0.0
            }
        },
        {
            "id": "mecanismo",
            "label": "Como aconteceu?",
            "tipo": "radio",
            "opcoes": {
                "Após dor torácica/palpitação/dispneia": 1.3,
                "Após esforço/calor/desidratação/ficar em pé por muito tempo": 0.8,
                "Durante mudança brusca de posição": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Trauma craniano durante a queda": 1.2,
                "Convulsões (movimentos involuntários, mordedura de língua, incontinência)": 1.3,
                "Palidez extrema, sudorese fria": 1.0,
                "Dor de cabeça intensa ao acordar do episódio": 1.0
            }
        },
        {
            "id": "historico",
            "label": "Histórico",
            "tipo": "checkbox",
            "opcoes": {
                "Episódios repetidos nos últimos 7 dias": 1.0,
                "Arritmia/Doença cardíaca conhecida": 1.3,
                "Uso de anticoagulante": 1.0
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Gravidez": 1.0,
                "Diabetes/Insulina ou hipoglicemiantes": 1.0,
                "Doença neurológica prévia": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Perda total de consciência recente sem recuperação"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Trauma craniano durante a queda", "Convulsões (movimentos involuntários, mordedura de língua, incontinência)"]}, "min_cor": "vermelho"},
        {"se": {"mecanismo": "Após dor torácica/palpitação/dispneia"}, "min_cor": "laranja"},
        {"se": {"historico": ["Arritmia/Doença cardíaca conhecida", "Uso de anticoagulante"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# HIPOTENSÃO
# -----------------------------
FLUXOS[normalizar("Hipotensão")] = {
    "label": "Hipotensão",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Pressão muito baixa com tontura e palidez extrema": 3.5,
                "Tontura ao levantar e fraqueza acentuada": 2.0,
                "Sensação de pressão baixa leve": 1.0,
                "Sem sintomas de pressão baixa": 0.0
            }
        },
        {
            "id": "sinais_de_choque",
            "label": "Sinais de choque/gravidade",
            "tipo": "checkbox",
            "opcoes": {
                "Pele fria/pegajosa, sudorese intensa": 1.2,
                "Batimento cardíaco muito acelerado": 1.0,
                "Confusão/sonolência": 1.2,
                "Redução do volume urinário": 0.8
            }
        },
        {
            "id": "possiveis_causas",
            "label": "Possíveis causas recentes",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos/diarreia/febre (perda de líquidos)": 1.0,
                "Sangramento aparente ou suspeito": 1.3,
                "Uso de anti-hipertensivos/diuréticos": 0.8,
                "Reação alérgica com inchaço/urticária/chiado": 1.3
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Doença cardíaca conhecida": 1.0,
                "Gravidez": 1.0,
                "Insuficiência renal/hepática": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Pressão muito baixa com tontura e palidez extrema"}, "min_cor": "vermelho"},
        {"se": {"sinais_de_choque": ["Pele fria/pegajosa, sudorese intensa", "Confusão/sonolência", "Pele muito pálida ou arroxeada"]}, "min_cor": "vermelho"},
        {"se": {"possiveis_causas": ["Sangramento aparente ou suspeito", "Reação alérgica com inchaço/urticária/chiado"]}, "min_cor": "vermelho"},
        {"se": {"condicoes_risco": ["Idade ≤ 4 anos ou ≥ 67 anos", "Doença cardíaca conhecida"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# HIPOGLICEMIA
# -----------------------------
FLUXOS[normalizar("Hipoglicemia")] = {
    "label": "Hipoglicemia",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Desmaio ou confusão com sudorese intensa": 3.5,
                "Tontura, tremores e fome súbita": 2.0,
                "Leve fraqueza ou irritação": 1.0,
                "Sem sintomas associados": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Início do quadro",
            "tipo": "radio",
            "opcoes": {
                "Início súbito, nos últimos minutos": 1.3,
                "Instalação mais lenta, em algumas horas": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados",
            "tipo": "checkbox",
            "opcoes": {
                "Uso recente de insulina ou remédio para diabetes": 1.2,
                "Jejum prolongado ou refeição atrasada": 0.8,
                "Atividade física intensa sem alimentação": 0.8
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Doença cardíaca conhecida": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Desmaio ou confusão com sudorese intensa"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Uso recente de insulina ou remédio para diabetes"]}, "min_cor": "laranja"},
        {"se": {"inicio": "Início súbito, nos últimos minutos"}, "min_cor": "laranja"},
        {"se": {"condicoes_risco": ["Idade ≤ 4 anos ou ≥ 67 anos"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# HIPERGLICEMIA
# -----------------------------
FLUXOS[normalizar("Hiperglicemia")] = {
    "label": "Hiperglicemia",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Sede intensa, urina excessiva e cansaço extremo": 3.5,
                "Mal-estar com enjoo e dor abdominal": 2.0,
                "Leve fraqueza e sede acima do normal": 1.0,
                "Sem sintomas associados": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Início do quadro",
            "tipo": "radio",
            "opcoes": {
                "Início súbito, em poucas horas": 1.0,
                "Progressivo, nos últimos dias": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados",
            "tipo": "checkbox",
            "opcoes": {
                "Esquecimento ou redução da dose de insulina/remédio": 1.2,
                "Infecção recente": 1.0,
                "Excesso de ingestão de carboidratos": 0.6
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Doença renal ou cardíaca": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Sede intensa, urina excessiva e cansaço extremo"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Infecção recente"]}, "min_cor": "laranja"},
        {"se": {"inicio": "Início súbito, em poucas horas"}, "min_cor": "laranja"},
        {"se": {"condicoes_risco": ["Doença renal ou cardíaca", "Idade ≤ 4 anos ou ≥ 67 anos"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# TEMPERATURA BAIXA
# -----------------------------
FLUXOS[normalizar("Temperatura baixa")] = {
    "label": "Temperatura baixa",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Extremidades frias com sonolência ou confusão": 3.5,
                "Calafrios e pele fria persistente": 2.0,
                "Sensação de frio sem outros sintomas": 1.0,
                "Temperatura normal para o ambiente": 0.0
            }
        },
        {
            "id": "exposicao",
            "label": "Exposição recente",
            "tipo": "radio",
            "opcoes": {
                "Exposição prolongada ao frio": 1.2,
                "Ambiente frio por pouco tempo": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Tremores intensos": 0.8,
                "Dificuldade para falar": 1.0,
                "Pele muito pálida ou arroxeada": 1.2
            }
        },
        {
            "id": "condicoes_risco",
            "label": "Condições de risco",
            "tipo": "checkbox",
            "opcoes": {
                "Idade ≤ 4 anos ou ≥ 67 anos": 1.2,
                "Doença cardíaca ou circulatória": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Extremidades frias com sonolência ou confusão"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Dificuldade para falar", "Pele muito pálida ou arroxeada"]}, "min_cor": "vermelho"},
        {"se": {"exposicao": "Exposição prolongada ao frio"}, "min_cor": "laranja"},
        {"se": {"condicoes_risco": ["Idade ≤ 4 anos ou ≥ 67 anos", "Doença cardíaca ou circulatória"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# DOR DURANTE A GRAVIDEZ
# -----------------------------
FLUXOS[normalizar("Dor durante a gravidez")] = {
    "label": "Dor durante a gravidez",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa com sangramento ou perda de líquido": 3.5,
                "Dor abdominal moderada e persistente": 2.0,
                "Desconforto leve e intermitente": 1.0,
                "Dor ocasional esperada para a gestação": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Início do quadro",
            "tipo": "radio",
            "opcoes": {
                "Início súbito": 1.3,
                "Início gradual": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 1.0,
                "Diminuição ou ausência de movimentos do bebê": 1.3,
                "Pressão alta recente": 1.2
            }
        },
        {
            "id": "historico",
            "label": "Histórico",
            "tipo": "checkbox",
            "opcoes": {
                "Complicações gestacionais anteriores": 1.0,
                "Gestação de risco": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa com sangramento ou perda de líquido"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Diminuição ou ausência de movimentos do bebê"]}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Pressão alta recente", "Febre"]}, "min_cor": "laranja"},
        {"se": {"inicio": "Início súbito"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# MOVIMENTOS FETAIS
# -----------------------------
FLUXOS[normalizar("Redução dos movimentos fetais")] = {
    "label": "Redução dos movimentos fetais",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como estão os movimentos do bebê?",
            "tipo": "radio",
            "opcoes": {
                "Nenhum movimento fetal percebido nas últimas horas": 3.5,
                "Redução clara nos movimentos habituais": 2.0,
                "Movimentos presentes, mas menos ativos que o normal": 1.0,
                "Movimentos normais para o estágio gestacional": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Quando percebeu essa mudança?",
            "tipo": "radio",
            "opcoes": {
                "Hoje": 1.3,
                "Nos últimos dias": 0.8
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados",
            "tipo": "checkbox",
            "opcoes": {
                "Sangramento vaginal": 1.3,
                "Dor abdominal": 1.2,
                "Perda de líquido pela vagina": 1.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Nenhum movimento fetal percebido nas últimas horas"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Perda de líquido pela vagina", "Sangramento vaginal"]}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Dor abdominal"]}, "min_cor": "laranja"},
        {"se": {"inicio": "Hoje"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# TRABALHO DE PARTO
# -----------------------------
FLUXOS[normalizar("Trabalho de parto")] = {
    "label": "Trabalho de parto",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como estão as contrações?",
            "tipo": "radio",
            "opcoes": {
                "Contrações intensas com sangramento ou bolsa rota": 3.5,
                "Contrações regulares e dolorosas há mais de 1 hora": 2.0,
                "Contrações leves e irregulares": 1.0,
                "Apenas sensação de pressão pélvica sem dor": 0.0
            }
        },
        {
            "id": "intervalo",
            "label": "Intervalo entre as contrações",
            "tipo": "radio",
            "opcoes": {
                "Menos de 5 minutos": 1.3,
                "Entre 5 e 10 minutos": 0.8,
                "Mais de 10 minutos": 0.4
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados",
            "tipo": "checkbox",
            "opcoes": {
                "Perda de líquido pela vagina": 1.3,
                "Sangramento intenso": 1.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Contrações intensas com sangramento ou bolsa rota"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Sangramento intenso", "Perda de líquido pela vagina"]}, "min_cor": "vermelho"},
        {"se": {"intervalo": "Menos de 5 minutos"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# FEBRE EM LACTENTE
# -----------------------------
FLUXOS[normalizar("Febre em lactente")] = {
    "label": "Febre em lactente",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o quadro principal?",
            "tipo": "radio",
            "opcoes": {
                "Febre alta persistente com prostração ou recusa alimentar": 3.5,
                "Febre alta mas bebê responde a estímulos": 2.0,
                "Febre leve com comportamento preservado": 1.0,
                "Febre passageira e sem outros sintomas": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Duração da febre",
            "tipo": "radio",
            "opcoes": {
                "Mais de 48 horas": 1.0,
                "Menos de 48 horas": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos persistentes": 1.0,
                "Respiração acelerada/dificuldade para respirar": 1.3,
                "Manchas anormais na pele": 1.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Febre alta persistente com prostração ou recusa alimentar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Respiração acelerada/dificuldade para respirar", "Manchas anormais na pele"]}, "min_cor": "vermelho"},
        {"se": {"duracao": "Mais de 48 horas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# CHORO PERSISTENTE
# -----------------------------
FLUXOS[normalizar("Choro persistente")] = {
    "label": "Choro persistente",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como é o choro?",
            "tipo": "radio",
            "opcoes": {
                "Choro inconsolável há mais de 2 horas com sinais de dor": 3.5,
                "Choro frequente e difícil de acalmar": 2.0,
                "Choro leve mas diferente do habitual": 1.0,
                "Choro normal para a idade": 0.0
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 1.0,
                "Dificuldade para mamar": 1.0,
                "Vômitos": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Choro inconsolável há mais de 2 horas com sinais de dor"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Febre", "Vômitos"]}, "min_cor": "laranja"},
        {"se": {"fatores": ["Dificuldade para mamar"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# -----------------------------
# ICTERÍCIA NEONATAL
# -----------------------------
FLUXOS[normalizar("Icterícia neonatal")] = {
    "label": "Icterícia neonatal",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é o grau de amarelado?",
            "tipo": "radio",
            "opcoes": {
                "Icterícia intensa em face e corpo com sonolência excessiva": 3.5,
                "Amarelado moderado até o abdome": 2.0,
                "Amarelado leve no rosto e olhos": 1.0,
                "Discreto e com melhora espontânea": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "Primeiras 24 horas de vida": 1.3,
                "Após 2º dia de vida": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Dificuldade para mamar": 1.0,
                "Fezes esbranquiçadas": 1.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Icterícia intensa em face e corpo com sonolência excessiva"}, "min_cor": "vermelho"},
        {"se": {"inicio": "Primeiras 24 horas de vida"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Fezes esbranquiçadas", "Dificuldade para mamar"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Dor no peito")] = {
    "label": "Dor no peito",
    "perguntas": [
        {
            "id": "inicio_associado",
            "label": "A dor começou junto com algum desses sintomas?",
            "tipo": "radio",
            "opcoes": {
                "Desmaio, confusão ou fraqueza súbita": 2.0,
                "Falta de ar intensa ou suor frio": 1.5,
                "Nenhum desses": 0.0
            }
        },
        {
            "id": "caracteristica",
            "label": "Como você descreveria a dor?",
            "tipo": "radio",
            "opcoes": {
                "Muito forte, aperto ou queimação intensa": 1.8,
                "Moderada e constante": 0.9,
                "Leve e intermitente": 0.2
            }
        },
        {
            "id": "irradia",
            "label": "A dor se espalha para outro local?",
            "tipo": "radio",
            "opcoes": {
                "Braço, mandíbula ou costas": 1.2,
                "Apenas no peito": 0.0
            }
        },
        {
            "id": "duracao",
            "label": "Quanto tempo dura o episódio de dor?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 20 minutos": 1.0,
                "Entre 5 e 20 minutos": 0.5,
                "Menos de 5 minutos": 0.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes fatores de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de infarto ou angina": 0.8,
                "Pressão alta, diabetes ou colesterol alto": 0.6,
                "Tabagismo": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio_associado": "Desmaio, confusão ou fraqueza súbita"}, "min_cor": "vermelho"},
        {"se": {"inicio_associado": "Falta de ar intensa ou suor frio", "caracteristica": "Muito forte, aperto ou queimação intensa"}, "min_cor": "vermelho"},
        {"se": {"irradia": "Braço, mandíbula ou costas", "caracteristica": "Muito forte, aperto ou queimação intensa"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.5, "vermelho"),
        (4.0, "laranja"),
        (2.0, "amarelo"),
        (0.0, "verde")
    ]
}
# --- QUEDA EM CRIANÇA ---
FLUXOS[normalizar("Queda em criança")] = {
    "label": "Queda em criança",
    "perguntas": [
        {
            "id": "local_bateu",
            "label": "Onde a criança bateu?",
            "tipo": "radio",
            "opcoes": {
                "Cabeça": 1.8,
                "Outro local": 0.4
            }
        },
        {
            "id": "sinais_graves",
            "label": "A criança apresentou algum destes sinais logo após a queda?",
            "tipo": "checkbox",
            "opcoes": {
                "Perda de consciência": 2.0,
                "Convulsão": 1.8,
                "Vômitos repetidos": 1.2,
                "Sangue/fluido saindo do ouvido ou nariz": 1.8
            }
        },
        {
            "id": "comportamento",
            "label": "Como está o comportamento da criança?",
            "tipo": "radio",
            "opcoes": {
                "Muito sonolenta/confusa": 1.2,
                "Normal": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"local_bateu": "Cabeça", "sinais_graves": ["Perda de consciência", "Convulsão"]}, "min_cor": "vermelho"},
        {"se": {"sinais_graves": ["Sangue/fluido saindo do ouvido ou nariz"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# --- VÔMITO EM CRIANÇA ---
FLUXOS[normalizar("Vômito em criança")] = {
    "label": "Vômito em criança",
    "perguntas": [
        {
            "id": "frequencia",
            "label": "Com que frequência está vomitando?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 5 vezes em 6h": 1.5,
                "De 3 a 5 vezes em 6h": 0.9,
                "Menos de 3 vezes": 0.3
            }
        },
        {
            "id": "aspecto",
            "label": "Como é o vômito?",
            "tipo": "radio",
            "opcoes": {
                "Com sangue ou verde-escuro": 2.0,
                "Com muco ou restos alimentares": 0.5,
                "Apenas líquido claro": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Febre alta": 1.0,
                "Letargia/confusão": 1.5,
                "Dificuldade para beber líquidos": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"aspecto": "Com sangue ou verde-escuro"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Letargia/confusão"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# --- DIARREIA EM CRIANÇA ---
FLUXOS[normalizar("Diarreia em criança")] = {
    "label": "Diarreia em criança",
    "perguntas": [
        {
            "id": "duracao",
            "label": "Há quanto tempo está com diarreia?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 5 dias": 1.2,
                "3 a 5 dias": 0.6,
                "Menos de 3 dias": 0.2
            }
        },
        {
            "id": "aspecto",
            "label": "Como está a aparência das fezes?",
            "tipo": "radio",
            "opcoes": {
                "Com sangue ou pretas": 2.0,
                "Muito aquosas": 1.0,
                "Normais para diarreia": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Febre alta": 1.0,
                "Letargia/confusão": 1.5,
                "Boca seca ou olhos fundos": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"aspecto": "Com sangue ou pretas"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Letargia/confusão"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# FALTA DE AR
# ===============================
FLUXOS[normalizar("Falta de ar")] = {
    "label": "Falta de ar",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Quão intensa está a falta de ar agora?",
            "tipo": "radio",
            "opcoes": {
                "Grave, com lábios roxos ou confusão": 2.0,
                "Moderada e constante": 1.2,
                "Leve, apenas aos esforços": 0.4,
                "Sem desconforto relevante": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "De repente (minutos/horas)": 1.3,
                "Foi piorando aos poucos (dias)": 0.5
            }
        },
        {
            "id": "sinais_associados",
            "label": "Algum desses sinais está junto?",
            "tipo": "checkbox",
            "opcoes": {
                "Lábios ou ponta dos dedos roxos": 1.8,
                "Dor no peito": 1.5,
                "Chiado no peito": 0.6,
                "Febre": 0.6
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições que você tem (selecione se houver):",
            "tipo": "multiselect",
            "opcoes": {
                "Asma/bronquite/DPOC": 0.8,
                "Doença cardíaca": 0.8,
                "Gravidez": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Grave, com lábios roxos ou confusão"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Lábios ou ponta dos dedos roxos"]}, "min_cor": "vermelho"},
        {"se": {"inicio": "De repente (minutos/horas)", "sinais_associados": ["Dor no peito"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# VÔMITO (GERAL)
# ===============================
FLUXOS[normalizar("Vômito")] = {
    "label": "Vômito",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Vômitos com sangue ou sinais de desidratação": 2.0,
                "Vômitos persistentes sem melhora": 1.2,
                "Ocasional, com outros sintomas leves": 0.6,
                "Vômito único e controlado": 0.0
            }
        },
        {
            "id": "frequencia",
            "label": "Com que frequência ocorreu nas últimas 6 horas?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 5 vezes": 1.2,
                "3 a 5 vezes": 0.6,
                "Menos de 3 vezes": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Dor abdominal forte e contínua": 1.0,
                "Febre alta (≥ 38,5°C)": 0.8,
                "Não consegue manter líquidos": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores de risco presentes?",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≥ 67 anos": 0.8,
                "Gravidez": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Vômitos com sangue ou sinais de desidratação"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Não consegue manter líquidos"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# TRAUMA OU QUEDA
# ===============================
FLUXOS[normalizar("Trauma ou queda")] = {
    "label": "Trauma ou queda",
    "perguntas": [
        {
            "id": "mecanismo",
            "label": "Como foi o trauma?",
            "tipo": "radio",
            "opcoes": {
                "Alto impacto (trânsito, queda >1,5 m)": 1.8,
                "Moderado (queda da própria altura com batida forte)": 1.0,
                "Leve (batida/escoriação sem impacto relevante)": 0.4
            }
        },
        {
            "id": "sintomas",
            "label": "O que está acontecendo agora?",
            "tipo": "checkbox",
            "opcoes": {
                "Sangramento importante que não para": 1.8,
                "Perda de consciência na hora do trauma": 2.0,
                "Dor intensa e localizada": 1.0,
                "Deformidade aparente (osso torto/inchadão)": 1.5
            }
        },
        {
            "id": "area",
            "label": "Qual região foi mais atingida?",
            "tipo": "radio",
            "opcoes": {
                "Cabeça/peito/barriga": 1.2,
                "Braços/pernas": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"sintomas": ["Perda de consciência na hora do trauma"]}, "min_cor": "vermelho"},
        {"se": {"sintomas": ["Sangramento importante que não para"]}, "min_cor": "vermelho"},
        {"se": {"sintomas": ["Deformidade aparente (osso torto/inchadão)", "Dor intensa e localizada"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DOR DE CABEÇA (CEFALÉIA)
# ===============================
FLUXOS[normalizar("Dor de cabeça")] = {
    "label": "Dor de cabeça",
    "perguntas": [
        {
            "id": "caracteristica",
            "label": "Como é a dor?",
            "tipo": "radio",
            "opcoes": {
                "Muito forte, súbita ou com visão turva": 2.0,
                "Moderada, com náusea ou sensibilidade à luz": 1.2,
                "Leve e intermitente": 0.4,
                "Rotineira, sem sintomas associados": 0.0
            }
        },
        {
            "id": "inicio",
            "label": "Como começou?",
            "tipo": "radio",
            "opcoes": {
                "De repente (em segundos/minutos)": 1.3,
                "Foi surgindo aos poucos": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Rigidez na nuca": 1.5,
                "Febre alta (≥ 38,5°C)": 1.0,
                "Fraqueza em um lado do corpo ou fala enrolada": 1.6
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições associadas (se houver):",
            "tipo": "multiselect",
            "opcoes": {
                "Gravidez": 0.8,
                "Hipertensão": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"caracteristica": "Muito forte, súbita ou com visão turva"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Rigidez na nuca"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Fraqueza em um lado do corpo ou fala enrolada"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DOR ABDOMINAL
# ===============================
FLUXOS[normalizar("Dor abdominal")] = {
    "label": "Dor abdominal",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a dor?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa e súbita com rigidez na barriga ou vômitos": 2.0,
                "Dor moderada com febre ou vômito persistente": 1.2,
                "Dor intermitente/localizada, sem sinais associados": 0.6,
                "Dor leve que melhora com repouso": 0.2
            }
        },
        {
            "id": "local",
            "label": "Onde dói mais?",
            "tipo": "radio",
            "opcoes": {
                "Lado direito inferior": 1.0,
                "Parte de cima do lado direito": 0.8,
                "Dor difusa (barriga toda)": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Sangue nas fezes ou no vômito": 1.5,
                "Barriga muito dura": 1.3,
                "Sem eliminar gases/fezes": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Gravidez": 0.8,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa e súbita com rigidez na barriga ou vômitos"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Sangue nas fezes ou no vômito", "Barriga muito dura"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Sem eliminar gases/fezes"], "quadro": "Dor moderada com febre ou vômito persistente"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# SANGRAMENTO ATIVO
# ===============================
FLUXOS[normalizar("Sangramento ativo")] = {
    "label": "Sangramento ativo",
    "perguntas": [
        {
            "id": "intensidade",
            "label": "Qual a intensidade agora?",
            "tipo": "radio",
            "opcoes": {
                "Sangramento intenso que não para": 2.0,
                "Sangramento moderado com tontura ou palidez": 1.2,
                "Sangramento controlado, mas com volume considerável": 0.6,
                "Sangramento pequeno e controlado": 0.0
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Palidez/pele fria": 1.0,
                "Batimento muito acelerado": 0.8,
                "Desmaio ou quase desmaio": 1.5
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum desses se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulante": 1.2,
                "Gestação/puerpério": 1.0,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"intensidade": "Sangramento intenso que não para"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Desmaio ou quase desmaio"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Uso de anticoagulante"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DESMAIO / TONTURA
# ===============================
FLUXOS[normalizar("Desmaio ou tontura")] = {
    "label": "Desmaio ou tontura",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Desmaio com perda de consciência prolongada": 2.0,
                "Desmaio com recuperação, mas com confusão ou palidez": 1.2,
                "Tontura ao levantar, sem outros sintomas": 0.6,
                "Sensação leve de desequilíbrio": 0.2
            }
        },
        {
            "id": "gatilho",
            "label": "O que desencadeou?",
            "tipo": "radio",
            "opcoes": {
                "Dor no peito/palpitação/falta de ar": 1.5,
                "Calor, ficar muito tempo em pé ou levantar rápido": 0.6,
                "Sem gatilho claro": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Houve algum destes?",
            "tipo": "checkbox",
            "opcoes": {
                "Trauma na queda (bateu a cabeça)": 1.3,
                "Suor frio e palidez intensa": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Histórico/condições:",
            "tipo": "multiselect",
            "opcoes": {
                "Arritmia/Doença cardíaca": 1.2,
                "Uso de anticoagulante": 0.8,
                "Diabetes com uso de insulina/hipoglicemiante": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Desmaio com perda de consciência prolongada"}, "min_cor": "vermelho"},
        {"se": {"gatilho": "Dor no peito/palpitação/falta de ar"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Trauma na queda (bateu a cabeça)"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Arritmia/Doença cardíaca"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# COMPORTAMENTO ESTRANHO
# ===============================
FLUXOS[normalizar("Comportamento estranho à normalidade")] = {
    "label": "Comportamento estranho à normalidade",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o comportamento?",
            "tipo": "radio",
            "opcoes": {
                "Alteração súbita de consciência, agressividade ou alucinação": 2.0,
                "Confusão mental com febre ou sinais de infecção": 1.4,
                "Desorientação leve, mas com lucidez parcial": 0.6,
                "Comportamento excêntrico, mas sem risco": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "De repente (minutos/horas)": 1.2,
                "Aos poucos (dias/semana)": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu junto:",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Rigidez na nuca": 1.5,
                "Uso recente de álcool/drogas ou remédios sedativos": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Demência/AVC prévio": 0.8,
                "Imunossupressão": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Alteração súbita de consciência, agressividade ou alucinação"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Rigidez na nuca"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Confusão mental com febre ou sinais de infecção"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DIFICULDADE RESPIRATÓRIA
# ===============================
FLUXOS[normalizar("Dificuldade respiratória")] = {
    "label": "Dificuldade respiratória",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Quão intensa está agora?",
            "tipo": "radio",
            "opcoes": {
                "Falta de ar intensa com lábios roxos, confusão ou chiado grave": 2.0,
                "Falta de ar moderada e contínua": 1.2,
                "Respiração acelerada sem desconforto extremo": 0.6,
                "Respiração leve com leve desconforto": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.3,
                "Gradual (dias)": 0.5
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Lábios/pontas dos dedos roxos": 1.8,
                "Dor no peito": 1.5,
                "Febre": 0.6
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições presentes:",
            "tipo": "multiselect",
            "opcoes": {
                "Asma/bronquite/DPOC": 0.8,
                "Doença cardíaca": 0.8,
                "Alergia conhecida": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Falta de ar intensa com lábios roxos, confusão ou chiado grave"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Lábios/pontas dos dedos roxos"]}, "min_cor": "vermelho"},
        {"se": {"inicio": "Súbito (minutos/horas)", "sinais_associados": ["Dor no peito"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DOR NAS COSTAS
# ===============================
FLUXOS[normalizar("Dor nas costas")] = {
    "label": "Dor nas costas",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a dor agora?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa e repentina com dificuldade para andar ou urinar": 2.0,
                "Dor forte persistente que não melhora com repouso": 1.2,
                "Dor moderada após esforço físico": 0.6,
                "Dor leve, localizada e controlável": 0.2
            }
        },
        {
            "id": "irradia",
            "label": "A dor desce para a perna (ciática)?",
            "tipo": "radio",
            "opcoes": {
                "Sim, com formigamento/fraqueza": 1.0,
                "Não": 0.0
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há sinais de alerta?",
            "tipo": "checkbox",
            "opcoes": {
                "Perda de urina/fezes ou dormência em sela": 1.6,
                "Febre": 0.8,
                "Trauma recente importante": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa e repentina com dificuldade para andar ou urinar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Perda de urina/fezes ou dormência em sela"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Trauma recente importante"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# REAÇÃO ALÉRGICA
# ===============================
FLUXOS[normalizar("Reação alérgica")] = {
    "label": "Reação alérgica",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Inchaço de rosto, lábios ou dificuldade para respirar": 2.0,
                "Coceira intensa com placas vermelhas pelo corpo": 1.2,
                "Erupções leves e localizadas": 0.6,
                "Alergia leve e sem sintomas sistêmicos": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu junto?",
            "tipo": "checkbox",
            "opcoes": {
                "Chiado no peito/falta de ar": 1.5,
                "Tontura/desmaio": 1.2,
                "Vômitos ou cólicas": 0.8
            }
        },
        {
            "id": "exposicao",
            "label": "Houve contato com possível causa?",
            "tipo": "radio",
            "opcoes": {
                "Alimento/remédio/picada de inseto recente": 0.8,
                "Sem exposição conhecida": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Inchaço de rosto, lábios ou dificuldade para respirar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Chiado no peito/falta de ar", "Tontura/desmaio"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# CONVULSÕES
# ===============================
FLUXOS[normalizar("Convulsão")] = {
    "label": "Convulsão",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor agora?",
            "tipo": "radio",
            "opcoes": {
                "Convulsão ativa ou recente sem recuperação da consciência": 2.0,
                "Convulsão recente com recuperação parcial, mas com confusão": 1.6,
                "Histórico de epilepsia com crise controlada": 0.8,
                "Tremores leves e consciente, sem perda de consciência": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Quanto tempo durou a crise?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 5 minutos": 1.5,
                "Entre 2 e 5 minutos": 0.8,
                "Menos de 2 minutos": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Trauma na cabeça durante a crise": 1.5,
                "Febre alta (≥ 38,5°C)": 1.0,
                "Gravidez": 0.8,
                "Uso de anticoagulante": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Convulsão ativa ou recente sem recuperação da consciência"}, "min_cor": "vermelho"},
        {"se": {"duracao": "Mais de 5 minutos"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Trauma na cabeça durante a crise"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Febre alta (≥ 38,5°C)"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.8, "laranja"),
        (1.9, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# ALTERAÇÕES URINÁRIAS
# ===============================
FLUXOS[normalizar("Alterações urinárias")] = {
    "label": "Alterações urinárias",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor agora?",
            "tipo": "radio",
            "opcoes": {
                "Urina com sangue ou incapacidade de urinar": 2.0,
                "Dor intensa ao urinar com febre": 1.4,
                "Ardência leve ou aumento de frequência": 0.6,
                "Urina normal com pequeno desconforto": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Dor nas costas (lado dos rins)": 1.2,
                "Calafrios ou mal-estar intenso": 0.8,
                "Urina turva e com odor forte": 0.4
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Gravidez": 1.0,
                "Homem ≥ 50 anos (próstata)": 0.8,
                "Cateter vesical recente": 0.8,
                "Cálculo renal prévio": 0.6,
                "Diabetes": 0.6
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo começaram os sintomas?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24 horas": 0.8,
                "2 a 7 dias": 0.4,
                "Mais de 7 dias": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Urina com sangue ou incapacidade de urinar"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Dor intensa ao urinar com febre", "sinais_associados": ["Dor nas costas (lado dos rins)"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Gravidez"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# FORMIGAMENTO / PERDA DE FORÇA
# ===============================
FLUXOS[normalizar("Formigamento ou perda de força")] = {
    "label": "Formigamento ou perda de força",
    "perguntas": [
        {
            "id": "quadro",
            "label": "O que está acontecendo?",
            "tipo": "radio",
            "opcoes": {
                "Perda súbita de força ou fala arrastada": 2.0,
                "Formigamento em um lado do corpo": 1.4,
                "Leve dormência nas mãos ou pés": 0.6,
                "Sensação leve e passageira": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.3,
                "Gradual (dias)": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Face caída de um lado": 1.6,
                "Dor de cabeça muito forte": 1.0,
                "Convulsão recente": 1.4
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulante": 1.0,
                "AVC ou AIT prévios": 0.8,
                "Hipertensão/Diabetes": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Perda súbita de força ou fala arrastada"}, "min_cor": "vermelho"},
        {"se": {"inicio": "Súbito (minutos/horas)", "sinais_associados": ["Face caída de um lado"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Convulsão recente"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# INCHAÇO
# ===============================
FLUXOS[normalizar("Inchaço incomum")] = {
    "label": "Inchaço incomum",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o inchaço?",
            "tipo": "radio",
            "opcoes": {
                "Inchaço súbito em uma perna com dor intensa": 2.0,
                "Inchaço generalizado com falta de ar": 1.6,
                "Inchaço leve no final do dia": 0.6,
                "Leve retenção sem desconforto": 0.2
            }
        },
        {
            "id": "local",
            "label": "Onde é mais evidente?",
            "tipo": "radio",
            "opcoes": {
                "Panturrilha/perna única": 1.2,
                "Ambas as pernas": 0.6,
                "Rosto/pálpebras/manhã": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algo junto?",
            "tipo": "checkbox",
            "opcoes": {
                "Dor na panturrilha/área quente e vermelha": 1.2,
                "Falta de ar": 1.5,
                "Ganho rápido de peso (dias)": 0.8
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum fator presente?",
            "tipo": "multiselect",
            "opcoes": {
                "Cirurgia ou imobilização recente": 1.0,
                "Pílula/terapia hormonal": 0.8,
                "Câncer ativo": 0.8,
                "Insuficiência cardíaca/renal": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Inchaço súbito em uma perna com dor intensa"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Inchaço generalizado com falta de ar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Cirurgia ou imobilização recente", "Pílula/terapia hormonal", "Câncer ativo"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# SANGRAMENTO VAGINAL
# ===============================
FLUXOS[normalizar("Sangramento vaginal")] = {
    "label": "Sangramento vaginal",
    "perguntas": [
        {
            "id": "gravidez",
            "label": "Está grávida?",
            "tipo": "radio",
            "opcoes": {
                "Sim": 1.6,
                "Não": 0.0,
                "Não sei": 0.6
            }
        },
        {
            "id": "intensidade",
            "label": "Como está o sangramento?",
            "tipo": "radio",
            "opcoes": {
                "Durante gravidez, com dor ou sangramento intenso": 2.0,
                "Abundante fora do ciclo com dor abdominal": 1.4,
                "Moderado e inesperado": 0.8,
                "Leve e esperado": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu algum destes?",
            "tipo": "checkbox",
            "opcoes": {
                "Tontura ou desmaio": 1.5,
                "Coágulos grandes": 0.8,
                "Febre": 0.6
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo está sangrando?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 7 dias": 0.8,
                "2 a 7 dias": 0.4,
                "Menos de 2 dias": 0.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"intensidade": "Durante gravidez, com dor ou sangramento intenso"}, "min_cor": "vermelho"},
        {"se": {"intensidade": "Abundante fora do ciclo com dor abdominal"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Tontura ou desmaio"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# LESÕES NA PELE
# ===============================
FLUXOS[normalizar("Lesões na pele")] = {
    "label": "Lesões na pele",
    "perguntas": [
        {
            "id": "aspecto",
            "label": "Como são as lesões?",
            "tipo": "radio",
            "opcoes": {
                "Púrpuras, vermelhas escuras ou com febre alta": 2.0,
                "Erupções espalhadas com coceira intensa": 1.2,
                "Manchas leves e pequenas": 0.6,
                "Pequenas irritações de contato": 0.2
            }
        },
        {
            "id": "extensao",
            "label": "Qual a extensão?",
            "tipo": "radio",
            "opcoes": {
                "Corpo todo ou grandes áreas": 1.0,
                "Limitadas a uma região": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Febre alta (≥ 38,5°C)": 1.0,
                "Inchaço de lábios/rosto ou falta de ar": 1.8,
                "Dor intensa na pele": 0.8
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores atuais:",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de remédio novo": 0.8,
                "Infecção recente": 0.6,
                "Imunossupressão": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"aspecto": "Púrpuras, vermelhas escuras ou com febre alta"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Inchaço de lábios/rosto ou falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Uso de remédio novo"], "extensao": "Corpo todo ou grandes áreas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DOR OU OLHO VERMELHO
# ===============================
FLUXOS[normalizar("Dor ou olho vermelho")] = {
    "label": "Dor ou olho vermelho",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual é a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Dor ocular intensa ou perda súbita da visão": 2.0,
                "Olhos vermelhos com secreção e sensibilidade à luz": 1.2,
                "Irritação leve com ardência": 0.6,
                "Olhos secos ou cansados": 0.2
            }
        },
        {
            "id": "fatores_agressores",
            "label": "Teve algo que possa ter causado?",
            "tipo": "radio",
            "opcoes": {
                "Trauma químico/poeira/impacto": 1.4,
                "Uso de lentes de contato": 0.8,
                "Sem fator conhecido": 0.0
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Visão embaçada ou halos ao redor da luz": 1.0,
                "Inchaço nas pálpebras": 0.6,
                "Dor de cabeça e náusea": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor ocular intensa ou perda súbita da visão"}, "min_cor": "vermelho"},
        {"se": {"fatores_agressores": "Trauma químico/poeira/impacto"}, "min_cor": "vermelho"},
        {"se": {"fatores_agressores": "Uso de lentes de contato", "quadro": "Olhos vermelhos com secreção e sensibilidade à luz"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}
# ===============================
# Dor na perna e dificuldade pra caminhar
# ===============================
FLUXOS[normalizar("Dor na perna e dificuldade pra caminhar")] = {
    "label": "Dor na perna e dificuldade pra caminhar",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor agora?",
            "tipo": "radio",
            "opcoes": {
                "Dor súbita com inchaço, vermelhidão ou dificuldade de mover a perna": 2.0,
                "Dor intensa após queda ou lesão recente": 1.4,
                "Dor moderada, persistente, mas ainda consegue caminhar": 0.6,
                "Dor leve e passageira, sem sinais visíveis": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados (selecione se houver):",
            "tipo": "checkbox",
            "opcoes": {
                "Inchaço localizado e quente": 1.2,
                "Vermelhidão marcada": 0.8,
                "Formigamento ou fraqueza na perna": 0.8
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores de risco recentes:",
            "tipo": "multiselect",
            "opcoes": {
                "Imobilização/cirurgia recente": 1.0,
                "Uso de anticoncepcional/hormônios": 0.8,
                "História de trombose/câncer": 0.8,
                "Idade ≥ 67 anos": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor súbita com inchaço, vermelhidão ou dificuldade de mover a perna"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Dor intensa após queda ou lesão recente"}, "min_cor": "laranja"},
        {"se": {"sinais": ["Inchaço localizado e quente"]}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Imobilização/cirurgia recente", "História de trombose/câncer"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# INTOXICAÇÃO
# ===============================
FLUXOS[normalizar("Sinais de intoxicação ou envenenamento")] = {
    "label": "Sinais de intoxicação ou envenenamento",
    "perguntas": [
        {
            "id": "quadro",
            "label": "O que aconteceu?",
            "tipo": "radio",
            "opcoes": {
                "Ingestão de substância tóxica com confusão, vômito ou inconsciência": 2.0,
                "Ingestão suspeita com sintomas moderados (náusea, tontura)": 1.2,
                "Ingestão leve com sintomas leves (enjoo leve, dor de barriga)": 0.6,
                "Ingestão pequena com sintomas ausentes ou mínimos": 0.2
            }
        },
        {
            "id": "agente",
            "label": "Qual o possível agente?",
            "tipo": "radio",
            "opcoes": {
                "Produto de limpeza/agrotóxico": 1.5,
                "Remédio em dose alta": 1.2,
                "Álcool/drogas": 0.8,
                "Desconhecido": 0.4
            }
        },
        {
            "id": "tempo",
            "label": "Quando foi a ingestão?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 1 hora": 1.0,
                "Entre 1 e 6 horas": 0.6,
                "Mais de 6 horas": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos repetidos": 1.0,
                "Sonolência/confusão": 1.2,
                "Convulsão": 1.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Ingestão de substância tóxica com confusão, vômito ou inconsciência"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Convulsão"]}, "min_cor": "vermelho"},
        {"se": {"agente": "Produto de limpeza/agrotóxico"}, "min_cor": "vermelho"},
        {"se": {"tempo": "Menos de 1 hora", "quadro": "Ingestão suspeita com sintomas moderados (náusea, tontura)"} , "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# Dor no pescoço ou rigidez na nuca
# ===============================
FLUXOS[normalizar("Dor no pescoço ou rigidez na nuca")] = {
    "label": "Dor no pescoço ou rigidez na nuca",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa com febre, vômito ou confusão": 2.0,
                "Rigidez importante com dor de cabeça forte": 1.4,
                "Dor moderada após esforço físico ou posição ruim": 0.6,
                "Dor leve e localizada, sem outros sintomas": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Formigamento/fraqueza nos braços": 1.0,
                "Trauma recente (acidente/queda)": 1.2,
                "Febre alta (≥ 38,5°C)": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa com febre, vômito ou confusão"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Rigidez importante com dor de cabeça forte"} , "min_cor": "laranja"},
        {"se": {"sinais": ["Trauma recente (acidente/queda)"]}, "min_cor": "laranja"},
        {"se": {"sinais": ["Formigamento/fraqueza nos braços"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# Alterações visuais súbitas
# ===============================
FLUXOS[normalizar("Alterações visuais súbitas")] = {
    "label": "Alterações visuais súbitas",
    "perguntas": [
        {
            "id": "quadro",
            "label": "O que está acontecendo com a visão?",
            "tipo": "radio",
            "opcoes": {
                "Perda súbita da visão ou visão muito turva de um lado": 2.0,
                "Visão dupla ou embaçada com dor de cabeça ou náusea": 1.4,
                "Leve embaçamento ou dificuldade temporária pra focar": 0.6,
                "Cansaço visual leve, sem perda ou dor": 0.2
            }
        },
        {
            "id": "lado",
            "label": "Afeta um olho ou os dois?",
            "tipo": "radio",
            "opcoes": {
                "Um olho": 0.8,
                "Dois olhos": 0.4
            }
        },
        {
            "id": "fatores",
            "label": "Houve algum destes fatores?",
            "tipo": "radio",
            "opcoes": {
                "Trauma químico/impacto recente": 1.6,
                "Uso de lentes de contato": 0.8,
                "Sem fator conhecido": 0.0
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Dor ocular intensa": 1.2,
                "Halos ao redor da luz/visão embaçada": 0.8,
                "Dor de cabeça forte": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Perda súbita da visão ou visão muito turva de um lado"}, "min_cor": "vermelho"},
        {"se": {"fatores": "Trauma químico/impacto recente"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Dor ocular intensa"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Visão dupla ou embaçada com dor de cabeça ou náusea"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# ENGASGO
# ===============================
FLUXOS[normalizar("Engasgo ou obstrução das vias aéreas")] = {
    "label": "Engasgo ou obstrução das vias aéreas",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está agora?",
            "tipo": "radio",
            "opcoes": {
                "Engasgo com tosse ineficaz, lábios roxos ou dificuldade extrema": 2.0,
                "Tosse persistente com respiração ofegante": 1.4,
                "Tossiu, mas respira normalmente agora": 0.6,
                "Episódio leve e isolado, sem sinais atuais": 0.2
            }
        },
        {
            "id": "objeto",
            "label": "Suspeita de objeto/alimento preso?",
            "tipo": "radio",
            "opcoes": {
                "Sim, objeto pequeno (moeda/brinquedo)": 1.4,
                "Sim, alimento": 0.8,
                "Não sei": 0.4,
                "Não": 0.0
            }
        },
        {
            "id": "idade",
            "label": "Qual a faixa etária?",
            "tipo": "radio",
            "opcoes": {
                "Bebê (< 1 ano)": 0.8,
                "Criança (1–12 anos)": 0.4,
                "Adolescente/adulto": 0.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Engasgo com tosse ineficaz, lábios roxos ou dificuldade extrema"}, "min_cor": "vermelho"},
        {"se": {"objeto": "Sim, objeto pequeno (moeda/brinquedo)"} , "min_cor": "vermelho"},
        {"se": {"quadro": "Tosse persistente com respiração ofegante"} , "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# ferimentos ou cortes com objetos
# ===============================
FLUXOS[normalizar("ferimentos ou cortes com objetos")] = {
    "label": "Ferimentos ou cortes com objetos",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como é o ferimento?",
            "tipo": "radio",
            "opcoes": {
                "Corte profundo com sangramento intenso e exposição de tecidos": 2.0,
                "Ferida moderada com sangramento que demora a parar": 1.2,
                "Ferida pequena, mas com sinais de infecção (pus, vermelhidão)": 0.8,
                "Corte leve, limpo e controlado": 0.2
            }
        },
        {
            "id": "local",
            "label": "Onde foi o corte?",
            "tipo": "radio",
            "opcoes": {
                "Face, mãos, genitália ou grandes articulações": 1.2,
                "Outro local do corpo": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais/fatores associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Sangramento que não para": 1.6,
                "Mordida animal/humana": 1.4,
                "Sujeira/contaminação no ferimento": 1.0,
                "Corpo estranho visível": 1.0,
                "Perda de sensibilidade no local": 1.0
            }
        },
        {
            "id": "vacina_tetano",
            "label": "Vacina do tétano está em dia?",
            "tipo": "radio",
            "opcoes": {
                "Não sei/atrasada": 0.8,
                "Em dia": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Corte profundo com sangramento intenso e exposição de tecidos"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Sangramento que não para"]}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Mordida animal/humana", "Sujeira/contaminação no ferimento", "Corpo estranho visível"]}, "min_cor": "laranja"},
        {"se": {"vacina_tetano": "Não sei/atrasada"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# Corpo estranho nos olhos,ouvidos ou nariz
# ===============================
FLUXOS[normalizar("Corpo estranho nos olhos,ouvidos ou nariz")] = {
    "label": "Corpo estranho nos olhos,ouvidos ou nariz",
    "perguntas": [
        {
            "id": "local",
            "label": "Onde está o corpo estranho?",
            "tipo": "radio",
            "opcoes": {
                "Via aérea (garganta/traqueia)": 1.8,
                "Nariz": 1.2,
                "Ouvido": 1.0,
                "Olho": 1.4
            }
        },
        {
            "id": "quadro",
            "label": "Como está a situação agora?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa ou secreção com febre": 2.0,
                "Desconforto moderado e persistente": 1.2,
                "Leve irritação, sem dor ou sinais de infecção": 0.6,
                "Presença confirmada, mas sem sintomas": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Algum destes sinais está presente?",
            "tipo": "checkbox",
            "opcoes": {
                "Dificuldade para respirar/deglutir": 1.8,
                "Secreção com mau cheiro": 1.0,
                "Vermelhidão/inchaço importante": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"local": "Via aérea (garganta/traqueia)"} , "min_cor": "vermelho"},
        {"se": {"sinais": ["Dificuldade para respirar/deglutir"]}, "min_cor": "vermelho"},
        {"se": {"local": "Olho", "quadro": "Dor intensa ou secreção com febre"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Desconforto moderado e persistente"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}
# ===============================
# Dor ou dificuldade ao urinar
# ===============================
FLUXOS[normalizar("Dor ou dificuldade ao urinar")] = {
    "label": "Dor ou dificuldade ao urinar",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor agora?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa com sangue na urina ou febre": 2.0,
                "Ardência moderada com urgência e desconforto abdominal": 1.2,
                "Ardência leve ou aumento de frequência urinária": 0.6,
                "Leve desconforto, sem outros sintomas": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum desses sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Dor nas costas (lado dos rins)": 1.2,
                "Náusea ou vômito": 0.6,
                "Urina turva e com odor forte": 0.4
            }
        },
        {
            "id": "fatores_risco",
            "label": "Algum destes se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Gravidez": 1.0,
                "Homem ≥ 50 anos (próstata)": 0.8,
                "Cateter vesical recente": 0.8,
                "Cálculo renal prévio": 0.6,
                "Diabetes": 0.6
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo começaram os sintomas?",
            "tipo": "radio",
            "opcoes": {
                "Menos de 24 horas": 0.6,
                "2 a 7 dias": 0.4,
                "Mais de 7 dias": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa com sangue na urina ou febre"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Ardência moderada com urgência e desconforto abdominal", "sinais_associados": ["Dor nas costas (lado dos rins)"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Gravidez"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# ANSIEDADE / AGITAÇÃO
# ===============================
FLUXOS[normalizar("Ansiedade ou agitação intensas")] = {
    "label": "Ansiedade ou agitação intensas",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a crise agora?",
            "tipo": "radio",
            "opcoes": {
                "Agitação extrema com risco de autoagressão ou agressividade": 2.0,
                "Crise intensa com falta de ar, tremores ou choro incontrolável": 1.2,
                "Ansiedade moderada com pensamentos acelerados": 0.6,
                "Sensação leve de nervosismo ou tensão": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Aparecem juntos:",
            "tipo": "checkbox",
            "opcoes": {
                "Dor no peito ou palpitações": 1.0,
                "Tontura ou sensação de desmaio": 0.8,
                "Insônia prolongada (≥ 3 noites)": 0.4
            }
        },
        {
            "id": "fatores_risco",
            "label": "Há algum destes?",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de transtorno de ansiedade/pânico": 0.6,
                "Uso recente de álcool/drogas/estimulantes": 0.8,
                "Suspensão recente de benzodiazepínico": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Agitação extrema com risco de autoagressão ou agressividade"}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Suspensão recente de benzodiazepínico"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# DIARREIA (GERAL)
# ===============================
FLUXOS[normalizar("Diarreia")] = {
    "label": "Diarreia",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual cenário se encaixa melhor?",
            "tipo": "radio",
            "opcoes": {
                "Diarreia intensa com sangue ou sinais de desidratação": 2.0,
                "Várias evacuações líquidas com febre ou dor abdominal": 1.2,
                "Episódio isolado de diarreia sem outros sintomas": 0.6,
                "Fezes amolecidas por curto período": 0.2
            }
        },
        {
            "id": "frequencia",
            "label": "Quantas evacuações nas últimas 6 horas?",
            "tipo": "radio",
            "opcoes": {
                "≥ 6": 1.0,
                "3 a 5": 0.6,
                "1 a 2": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos repetidos": 1.0,
                "Febre alta (≥ 38,5°C)": 0.8,
                "Boca seca/olhos fundos (desidratação)": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≥ 67 anos": 0.6,
                "Imunossupressão": 0.8,
                "Viagem recente/água/ alimento suspeito": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Diarreia intensa com sangue ou sinais de desidratação"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Boca seca/olhos fundos (desidratação)"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# SENSAÇÃO DE DESMAIO
# ===============================
FLUXOS[normalizar("Sensação de desmaio")] = {
    "label": "Sensação de desmaio",
    "perguntas": [
        {
            "id": "quadro",
            "label": "O que você está sentindo?",
            "tipo": "radio",
            "opcoes": {
                "Fraqueza súbita com visão turva e suor frio": 2.0,
                "Tontura persistente com sensação de queda iminente": 1.2,
                "Sensação leve de cabeça vazia ou instabilidade": 0.6,
                "Episódio pontual que já passou": 0.2
            }
        },
        {
            "id": "gatilho",
            "label": "O que desencadeou?",
            "tipo": "radio",
            "opcoes": {
                "Dor no peito/palpitação/falta de ar": 1.5,
                "Calor, ficar muito tempo em pé ou levantar rápido": 0.6,
                "Sem gatilho claro": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu junto:",
            "tipo": "checkbox",
            "opcoes": {
                "Palidez e suor frio": 0.8,
                "Trauma na queda (bateu a cabeça)": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Histórico/condições:",
            "tipo": "multiselect",
            "opcoes": {
                "Arritmia/doença cardíaca": 1.2,
                "Diabetes (insulina/hipoglicemiante)": 0.8,
                "Uso de anticoagulante": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Fraqueza súbita com visão turva e suor frio"}, "min_cor": "vermelho"},
        {"se": {"gatilho": "Dor no peito/palpitação/falta de ar"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Trauma na queda (bateu a cabeça)"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Arritmia/doença cardíaca"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.5, "laranja"),
        (1.8, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# PALPITAÇÕES
# ===============================
FLUXOS[normalizar("Palpitações")] = {
    "label": "Palpitações",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como estão os batimentos?",
            "tipo": "radio",
            "opcoes": {
                "Batimentos acelerados com dor no peito ou falta de ar": 2.0,
                "Palpitações intensas e persistentes, sem outros sintomas": 1.2,
                "Batimentos rápidos ocasionais, mas sem desconforto": 0.6,
                "Sensação leve que passa rapidamente": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Duração do episódio atual:",
            "tipo": "radio",
            "opcoes": {
                "Mais de 20 minutos": 1.0,
                "5 a 20 minutos": 0.6,
                "Menos de 5 minutos": 0.2
            }
        },
        {
            "id": "fatores",
            "label": "Possíveis fatores associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Desmaio ou quase desmaio": 1.5,
                "Dor torácica": 1.0,
                "Uso de estimulantes (cafeína/energético)": 0.4
            }
        },
        {
            "id": "riscos",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Doença cardíaca/Arritmia prévia": 1.2,
                "Tireóide desregulada": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Batimentos acelerados com dor no peito ou falta de ar"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Desmaio ou quase desmaio"]}, "min_cor": "vermelho"},
        {"se": {"riscos": ["Doença cardíaca/Arritmia prévia"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}
# ===============================
# Dor nas articulações
# ===============================
FLUXOS[normalizar("Dor nas articulações")] = {
    "label": "Dor nas articulações",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Dor súbita com inchaço e dificuldade de movimentar": 2.0,
                "Dor intensa após trauma ou inflamação visível": 1.4,
                "Dor moderada que piora com o uso": 0.6,
                "Dor leve que melhora com repouso": 0.2
            }
        },
        {
            "id": "local",
            "label": "Quantas articulações estão afetadas?",
            "tipo": "radio",
            "opcoes": {
                "Várias articulações": 0.8,
                "Apenas uma": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Vermelhidão intensa e calor local": 1.0,
                "Febre (≥ 38,5°C)": 1.0,
                "Deformidade visível": 1.2
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Trauma recente": 0.8,
                "Prótese articular": 1.0,
                "Doença reumática conhecida": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor súbita com inchaço e dificuldade de movimentar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Deformidade visível"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Febre (≥ 38,5°C)"], "local": "Apenas uma"}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Prótese articular"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# COCEIRA (PRURIDO)
# ===============================
FLUXOS[normalizar("Coceira na pele")] = {
    "label": "Coceira na pele",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Coceira intensa com placas vermelhas e inchaço": 2.0,
                "Coceira forte que não alivia, atrapalha o sono": 1.2,
                "Coceira moderada e localizada": 0.6,
                "Coceira leve, passageira": 0.2
            }
        },
        {
            "id": "extensao",
            "label": "Qual a extensão das lesões?",
            "tipo": "radio",
            "opcoes": {
                "Espalhadas pelo corpo": 0.8,
                "Apenas em uma área": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Inchaço de lábios/rosto ou falta de ar": 1.8,
                "Feridas por coçar demais": 0.6,
                "Febre": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "Possível causa recente:",
            "tipo": "radio",
            "opcoes": {
                "Alimento/remédio/picada": 0.8,
                "Produto químico/pele muito seca": 0.4,
                "Sem causa clara": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Coceira intensa com placas vermelhas e inchaço"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Inchaço de lábios/rosto ou falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Coceira forte que não alivia, atrapalha o sono", "extensao": "Espalhadas pelo corpo"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# QUEIMAÇÃO NO PEITO
# ===============================
FLUXOS[normalizar("Queimação no peito")] = {
    "label": "Queimação no peito",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual cenário se encaixa melhor?",
            "tipo": "radio",
            "opcoes": {
                "Queimação forte com náusea ou suor frio": 2.0,
                "Desconforto moderado que piora ao deitar": 1.2,
                "Ardência leve após comer alimentos pesados": 0.6,
                "Sensação leve, ocasional, sem outros sintomas": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "De repente (minutos/horas)": 1.3,
                "Após refeições/à noite": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Apareceu junto:",
            "tipo": "checkbox",
            "opcoes": {
                "Dor que irradia para braço/mandíbula": 1.5,
                "Falta de ar": 1.2,
                "Azia/retorno de ácido à garganta": 0.6
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Doença cardíaca prévia": 1.2,
                "Idade ≥ 67 anos": 0.6,
                "Obesidade/refluxo conhecido": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Queimação forte com náusea ou suor frio"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Dor que irradia para braço/mandíbula", "Falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"inicio": "De repente (minutos/horas)", "fatores_risco": ["Doença cardíaca prévia"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.4, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# Alteração na fala
# ===============================
FLUXOS[normalizar("Alteração na fala")] = {
    "label": "Alteração na fala",
    "perguntas": [
        {
            "id": "quadro",
            "label": "O que está acontecendo?",
            "tipo": "radio",
            "opcoes": {
                "Perda súbita da fala ou fala arrastada": 2.0,
                "Dificuldade de encontrar palavras ou formar frases": 1.4,
                "Fala lenta ou confusa, mas consegue se expressar": 0.6,
                "Leve hesitação, mas sem prejuízo da comunicação": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.3,
                "Gradual (dias/semana)": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Fraqueza em um lado do corpo": 1.6,
                "Boca/face caída de um lado": 1.6,
                "Dor de cabeça muito forte": 1.0,
                "Convulsão": 1.6
            }
        },
        {
            "id": "riscos",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Arritmia/doença cardíaca": 1.0,
                "Hipertensão/Diabetes": 0.6,
                "AVC/AIT prévios": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Perda súbita da fala ou fala arrastada"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Fraqueza em um lado do corpo", "Boca/face caída de um lado", "Convulsão"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.4, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# Dor no ouvido
# ===============================
FLUXOS[normalizar("Dor no ouvido")] = {
    "label": "Dor no ouvido",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a dor?",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa com febre ou secreção purulenta": 2.0,
                "Dor forte e contínua, sem melhora com analgésico": 1.2,
                "Dor leve com coceira ou zumbido": 0.6,
                "Desconforto discreto que vai e volta": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Ocorreu também:",
            "tipo": "checkbox",
            "opcoes": {
                "Saída de líquido amarelado/esverdeado": 1.0,
                "Dor ao mastigar/abrir a boca": 0.6,
                "Perda de audição": 1.0
            }
        },
        {
            "id": "fatores",
            "label": "Possível causa:",
            "tipo": "radio",
            "opcoes": {
                "Resfriado recente/mergulho/voo": 0.6,
                "Objeto no ouvido/trauma": 1.2,
                "Sem fator conhecido": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa com febre ou secreção purulenta"}, "min_cor": "vermelho"},
        {"se": {"fatores": "Objeto no ouvido/trauma"}, "min_cor": "laranja"},
        {"se": {"sinais_associados": ["Perda de audição"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.6, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# SENSIBILIDADE À LUZ/SOM
# ===============================
FLUXOS[normalizar("Sensibilidade à luz ou som")] = {
    "label": "Sensibilidade à luz ou som",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Quão forte está a sensibilidade?",
            "tipo": "radio",
            "opcoes": {
                "Sensibilidade intensa com dor de cabeça e náusea": 2.0,
                "Incômodo moderado que piora em ambientes claros ou barulhentos": 1.2,
                "Leve desconforto ao sol ou com sons agudos": 0.6,
                "Sensação leve e eventual": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.2,
                "Aos poucos (dias)": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Rigidez na nuca": 1.5,
                "Febre (≥ 38,5°C)": 1.0,
                "Distúrbios visuais (pontos/auras)": 0.8
            }
        },
        {
            "id": "fatores",
            "label": "Fatores relacionados:",
            "tipo": "radio",
            "opcoes": {
                "Enxaqueca conhecida": 0.8,
                "Uso recente de remédio novo": 0.6,
                "Sem fator conhecido": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Sensibilidade intensa com dor de cabeça e náusea"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Rigidez na nuca"]}, "min_cor": "vermelho"},
        {"se": {"inicio": "Súbito (minutos/horas)", "sinais_associados": ["Febre (≥ 38,5°C)"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.3, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}


# ===============================
# INCHAÇO EM OLHOS/FACE
# ===============================
FLUXOS[normalizar("Inchaço nos olhos ou face")] = {
    "label": "Inchaço nos olhos ou face",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual situação descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Inchaço com dor intensa, febre ou fechamento dos olhos": 2.0,
                "Inchaço moderado com vermelhidão e coceira": 1.2,
                "Inchaço leve sem dor, após alergia ou trauma": 0.6,
                "Inchaço pequeno e passageiro": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Visão embaçada": 0.8,
                "Secreção ocular amarela/esverdeada": 0.8,
                "Falta de ar ou lábios/rosto ficando roxos": 1.8
            }
        },
        {
            "id": "fatores",
            "label": "O que pode ter causado?",
            "tipo": "radio",
            "opcoes": {
                "Alergia (alimento/remédio/picada)": 0.8,
                "Trauma local": 0.6,
                "Sem fator conhecido": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Inchaço com dor intensa, febre ou fechamento dos olhos"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Falta de ar ou lábios/rosto ficando roxos"]}, "min_cor": "vermelho"},
        {"se": {"fatores": "Alergia (alimento/remédio/picada)", "quadro": "Inchaço moderado com vermelhidão e coceira"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# SANGRAMENTO NASAL
# ===============================
FLUXOS[normalizar("Sangramento nasal")] = {
    "label": "Sangramento nasal",
    "perguntas": [
        {
            "id": "intensidade",
            "label": "Como está o sangramento?",
            "tipo": "radio",
            "opcoes": {
                "Sangramento intenso que não para com pressão direta": 2.0,
                "Sangramento moderado que reaparece durante o dia": 1.2,
                "Sangramento leve após esforço ou espirro": 0.6,
                "Sangramento isolado e já controlado": 0.2
            }
        },
        {
            "id": "fatores",
            "label": "Algum desses fatores presentes?",
            "tipo": "checkbox",
            "opcoes": {
                "Uso de anticoagulante": 1.0,
                "Trauma nasal recente": 0.8,
                "Pressão alta descontrolada": 0.8,
                "Ar muito seco/resfriado": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo começou?",
            "tipo": "radio",
            "opcoes": {
                "Agora e não para há > 15 min": 1.2,
                "Hoje, com episódios intermitentes": 0.6,
                "Episódio único ontem ou antes": 0.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"intensidade": "Sangramento intenso que não para com pressão direta"}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Uso de anticoagulante"]}, "min_cor": "laranja"},
        {"se": {"duracao": "Agora e não para há > 15 min"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}
# ===============================
# 1) NÁUSEA
# ===============================
FLUXOS[normalizar("Náusea ou enjoo")] = {
    "label": "Náusea ou enjoo",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o enjoo agora?",
            "tipo": "radio",
            "opcoes": {
                "Náusea constante com vômito e mal-estar": 2.0,
                "Enjoo forte que impede alimentação": 1.2,
                "Enjoo leve e intermitente": 0.6,
                "Desconforto passageiro após alimentação": 0.2
            }
        },
        {
            "id": "frequencia_vomitos",
            "label": "Vômitos nas últimas 6 horas:",
            "tipo": "radio",
            "opcoes": {
                "≥ 4 episódios": 1.2,
                "2 a 3 episódios": 0.6,
                "0 a 1 episódio": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Há algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Boca seca/urina escura (desidratação)": 1.2,
                "Febre (≥ 38,5°C)": 0.8,
                "Dor abdominal forte": 1.0
            }
        },
        {
            "id": "fatores",
            "label": "Situações recentes:",
            "tipo": "multiselect",
            "opcoes": {
                "Alimento suspeito/viagem recente": 0.6,
                "Uso de remédio novo/álcool": 0.6,
                "Gravidez": 0.8
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo está assim?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 48 horas": 0.8,
                "Entre 24 e 48 horas": 0.4,
                "Menos de 24 horas": 0.2
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Náusea constante com vômito e mal-estar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Boca seca/urina escura (desidratação)", "Dor abdominal forte"]}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Gravidez"], "frequencia_vomitos": "≥ 4 episódios"}, "min_cor": "laranja"},
        {"se": {"duracao": "Mais de 48 horas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 2) Dor no ombro ou braço
# ===============================
FLUXOS[normalizar("Dor no ombro ou braço")] = {
    "label": "Dor no ombro ou braço",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Dor irradiando do peito ou com formigamento": 2.0,
                "Dor intensa com limitação de movimento": 1.2,
                "Dor moderada após esforço": 0.6,
                "Dor leve que melhora com repouso": 0.2
            }
        },
        {
            "id": "lateralidade",
            "label": "Onde dói mais?",
            "tipo": "radio",
            "opcoes": {
                "Ombro esquerdo/braço esquerdo": 0.8,
                "Ombro/braço direito": 0.4,
                "Ambos": 0.6
            }
        },
        {
            "id": "sinais",
            "label": "Apareceu junto:",
            "tipo": "checkbox",
            "opcoes": {
                "Falta de ar ou suor frio": 1.5,
                "Dor no peito": 1.5,
                "Inchaço/hematoma após trauma": 0.8,
                "Dormência/fraqueza no braço": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Doença cardíaca prévia": 1.2,
                "Idade ≥ 67 anos": 0.6,
                "Diabetes/Hipertensão": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor irradiando do peito ou com formigamento"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Falta de ar ou suor frio", "Dor no peito"]}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Inchaço/hematoma após trauma", "Dormência/fraqueza no braço"]}, "min_cor": "laranja"},
        {"se": {"fatores_risco": ["Doença cardíaca prévia"], "lateralidade": "Ombro esquerdo/braço esquerdo"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.3, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 3) ALERGIA CUTÂNEA
# ===============================
FLUXOS[normalizar("Alergia cutânea")] = {
    "label": "Alergia cutânea",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a pele?",
            "tipo": "radio",
            "opcoes": {
                "Lesão com inchaço e coceira intensa": 2.0,
                "Mancha vermelha espalhada com descamação": 1.2,
                "Irritação leve e localizada": 0.6,
                "Lesão pequena e assintomática": 0.2
            }
        },
        {
            "id": "extensao",
            "label": "Qual a extensão?",
            "tipo": "radio",
            "opcoes": {
                "Espalhada pelo corpo": 0.8,
                "Apenas em uma área": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Inchaço de lábios/rosto ou falta de ar": 1.8,
                "Febre": 0.6,
                "Dor/ardor importantes": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "O que pode ter causado?",
            "tipo": "radio",
            "opcoes": {
                "Alimento/remédio/picada": 0.8,
                "Produto químico/novo cosmético": 0.6,
                "Sem fator claro": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Lesão com inchaço e coceira intensa"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Inchaço de lábios/rosto ou falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Mancha vermelha espalhada com descamação", "extensao": "Espalhada pelo corpo"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 4) SANGRAMENTO GASTROINTESTINAL
# ===============================
FLUXOS[normalizar("Sangramento gastrointestinal")] = {
    "label": "Sangramento gastrointestinal",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está o sangramento nas fezes?",
            "tipo": "radio",
            "opcoes": {
                "Fezes com sangue vivo ou pretas com mal-estar": 2.0,
                "Sangue moderado sem dor intensa": 1.2,
                "Pequena presença de sangue isolada": 0.6,
                "Observação leve e sem sintomas associados": 0.2
            }
        },
        {
            "id": "frequencia",
            "label": "Com que frequência apareceu?",
            "tipo": "radio",
            "opcoes": {
                "Em todas/maioria das evacuações": 1.0,
                "Em algumas evacuações": 0.6,
                "Apenas uma vez": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Tontura/fraqueza": 1.0,
                "Dor abdominal forte": 1.0,
                "Vômitos com sangue": 1.6
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulante/AAS": 1.0,
                "Álcool em excesso": 0.6,
                "Doença hepática conhecida": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Fezes com sangue vivo ou pretas com mal-estar"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Vômitos com sangue"]}, "min_cor": "vermelho"},
        {"se": {"riscos": ["Uso de anticoagulante/AAS"], "frequencia": "Em todas/maioria das evacuações"}, "min_cor": "laranja"},
        {"se": {"sinais": ["Tontura/fraqueza"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.4, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 5) CORPO ESTRANHO NA GARGANTA
# ===============================
FLUXOS[normalizar("Corpo estranho na garganta")] = {
    "label": "Corpo estranho na garganta",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está agora?",
            "tipo": "radio",
            "opcoes": {
                "Corpo estranho preso com dificuldade para respirar ou engolir": 2.0,
                "Desconforto com dor ao engolir": 1.2,
                "Sensação de algo preso, mas respira normalmente": 0.6,
                "Episódio leve e já resolvido": 0.2
            }
        },
        {
            "id": "tipo_objeto",
            "label": "O que pode ter sido engolido?",
            "tipo": "radio",
            "opcoes": {
                "Bateria/moeda/objeto cortante": 1.8,
                "Espinha de peixe/fragmento pequeno": 1.0,
                "Comida comum": 0.4,
                "Não sabe": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Saliva escorrendo/incapaz de engolir": 1.6,
                "Voz abafada/rouquidão súbita": 1.2,
                "Dor no peito ao engolir": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Corpo estranho preso com dificuldade para respirar ou engolir"}, "min_cor": "vermelho"},
        {"se": {"tipo_objeto": "Bateria/moeda/objeto cortante"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Saliva escorrendo/incapaz de engolir"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Desconforto com dor ao engolir"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.4, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 6) ICTERÍCIA
# ===============================
FLUXOS[normalizar("Icterícia")] = {
    "label": "Icterícia",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a coloração da pele/olhos?",
            "tipo": "radio",
            "opcoes": {
                "Icterícia intensa com dor abdominal ou vômito": 2.0,
                "Pele amarelada com febre ou cansaço": 1.2,
                "Amarelado leve, sem sintomas associados": 0.6,
                "Coloração discreta e passageira": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "Há menos de 48 horas": 0.8,
                "Entre 2 e 7 dias": 0.6,
                "Há mais de 7 dias": 0.8
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Urina muito escura": 0.8,
                "Fezes claras (acinzentadas)": 1.2,
                "Coceira no corpo": 0.6
            }
        },
        {
            "id": "fatores",
            "label": "Algum destes se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de álcool/medicamento recente": 0.6,
                "Hepatite conhecida/contato de risco": 0.8,
                "Cálculo na vesícula conhecido": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Icterícia intensa com dor abdominal ou vômito"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Fezes claras (acinzentadas)"]}, "min_cor": "vermelho"},
        {"se": {"inicio": "Há menos de 48 horas", "quadro": "Pele amarelada com febre ou cansaço"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 7) DIFICULDADE PARA ENGOLIR
# ===============================
FLUXOS[normalizar("Dificuldade para engolir")] = {
    "label": "Dificuldade para engolir",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Qual opção descreve melhor?",
            "tipo": "radio",
            "opcoes": {
                "Não consegue engolir líquidos ou saliva": 2.0,
                "Dor e dificuldade ao engolir sólidos": 1.2,
                "Leve desconforto para engolir": 0.6,
                "Sensação passageira ao engolir": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Início do problema:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.2,
                "Aos poucos (dias/semana)": 0.4
            }
        },
        {
            "id": "sinais",
            "label": "Apareceu junto:",
            "tipo": "checkbox",
            "opcoes": {
                "Saliva escorrendo/incapaz de engolir": 1.6,
                "Dor no peito/queimação": 0.8,
                "Perda de peso recente": 0.8
            }
        },
        {
            "id": "fatores",
            "label": "Possíveis causas:",
            "tipo": "radio",
            "opcoes": {
                "Engoliu espinha/objeto": 1.2,
                "Infecção de garganta recente": 0.6,
                "Sem fator claro": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Não consegue engolir líquidos ou saliva"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Saliva escorrendo/incapaz de engolir"]}, "min_cor": "vermelho"},
        {"se": {"fatores": "Engoliu espinha/objeto"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.3, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 8) TREMores
# ===============================
FLUXOS[normalizar("Tremores ou movimentos invouluntários")] = {
    "label": "Tremores ou movimentos invouluntários",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está agora?",
            "tipo": "radio",
            "opcoes": {
                "Tremores com perda de consciência ou força": 2.0,
                "Movimentos anormais contínuos com dificuldade para parar": 1.2,
                "Tremores leves em repouso": 0.6,
                "Episódio isolado e breve": 0.2
            }
        },
        {
            "id": "inicio",
            "label": "Quando começou?",
            "tipo": "radio",
            "opcoes": {
                "De repente (minutos/horas)": 1.0,
                "Aos poucos (dias/meses)": 0.4
            }
        },
        {
            "id": "sinais",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Confusão/sonolência após o episódio": 1.0,
                "Dor de cabeça forte": 0.8,
                "Queda/trauma associado": 1.0
            }
        },
        {
            "id": "fatores",
            "label": "O que pode ter contribuído?",
            "tipo": "multiselect",
            "opcoes": {
                "Álcool/droga/abstinência": 0.8,
                "Uso/suspensão de remédio (ex.: benzodiazepínico)": 1.0,
                "Febre/infecção recente": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Tremores com perda de consciência ou força"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Movimentos anormais contínuos com dificuldade para parar"}, "min_cor": "laranja"},
        {"se": {"sinais": ["Queda/trauma associado"]}, "min_cor": "laranja"},
        {"se": {"fatores": ["Uso/suspensão de remédio (ex.: benzodiazepínico)"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.8, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 9) RETENÇÃO URINÁRIA
# ===============================
FLUXOS[normalizar("Retenção urinária")] = {
    "label": "Retenção urinária",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está para urinar?",
            "tipo": "radio",
            "opcoes": {
                "Não urina há muitas horas com dor e distensão abdominal": 2.0,
                "Jato fraco com sensação de bexiga cheia": 1.2,
                "Urina com dificuldade, mas consegue aliviar": 0.6,
                "Pequena alteração, mas sem desconforto": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo está assim?",
            "tipo": "radio",
            "opcoes": {
                "≥ 12 horas": 1.0,
                "6 a 11 horas": 0.6,
                "< 6 horas": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Tem algo junto?",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Sangue na urina": 1.0,
                "Dor lombar (lado dos rins)": 1.0
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Homem ≥ 50 anos (próstata)": 0.8,
                "Uso de anticolinérgico/opióide": 0.8,
                "Cirurgia ou cateter recente": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Não urina há muitas horas com dor e distensão abdominal"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Sangue na urina", "Dor lombar (lado dos rins)"]}, "min_cor": "laranja"},
        {"se": {"riscos": ["Cirurgia ou cateter recente"]}, "min_cor": "laranja"},
        {"se": {"duracao": "≥ 12 horas"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.2, "laranja"),
        (1.6, "amarelo"),
        (0.0, "verde")
    ]
}

# ===============================
# 10) INFECÇÃO EM FERIDA
# ===============================
FLUXOS[normalizar("Infecção em ferida")] = {
    "label": "Infecção em ferida",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a ferida?",
            "tipo": "radio",
            "opcoes": {
                "Ferida com pus, inchaço, dor e febre": 2.0,
                "Vermelhidão intensa e secreção local": 1.2,
                "Leve vermelhidão sem dor": 0.6,
                "Cicatrização normal com alteração mínima": 0.2
            }
        },
        {
            "id": "extensao",
            "label": "Qual a extensão da vermelhidão?",
            "tipo": "radio",
            "opcoes": {
                "Espalha além das bordas da ferida": 1.0,
                "Restrita às bordas": 0.4
            }
        },
        {
            "id": "sinais",
            "label": "Tem algum destes sinais?",
            "tipo": "checkbox",
            "opcoes": {
                "Mau cheiro/tecido escuro": 1.2,
                "Febre (≥ 38,5°C)": 0.8,
                "Listras vermelhas subindo pela pele": 1.2
            }
        },
        {
            "id": "fatores",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Diabetes/uso de corticoide": 0.8,
                "Mordida animal/humana": 1.2,
                "Atraso na vacina do tétano": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Ferida com pus, inchaço, dor e febre"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Listras vermelhas subindo pela pele", "Mau cheiro/tecido escuro"]}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Mordida animal/humana"]}, "min_cor": "laranja"},
        {"se": {"fatores": ["Atraso na vacina do tétano"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.2, "vermelho"),
        (3.4, "laranja"),
        (1.7, "amarelo"),
        (0.0, "verde")
    ]
}
FLUXOS[normalizar("Febre")] = {
    "label": "Febre",
    "perguntas": [
        {
            "id": "temperatura",
            "label": "Qual é a temperatura medida?",
            "tipo": "radio",
            "opcoes": {
                "≥ 40°C": 2.0,
                "38,5°C a 39,9°C": 1.0,
                "37,8°C a 38,4°C": 0.4
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo está com febre?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 7 dias": 1.5,
                "3 a 7 dias": 0.8,
                "Menos de 3 dias": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Confusão mental": 1.8,
                "Rigidez na nuca": 1.5,
                "Falta de ar intensa": 1.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"temperatura": "≥ 40°C", "sinais_associados": ["Confusão mental"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Rigidez na nuca", "Falta de ar intensa"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
FLUXOS[normalizar("Delírio ou alucinações")] = {
    "label": "Delírio ou alucinações",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Quando começaram os sintomas?",
            "tipo": "radio",
            "opcoes": {
                "Início súbito nas últimas 24h": 2.0,
                "Progressivo há dias/semanas": 0.9,
                "Intermitente há meses": 0.4
            }
        },
        {
            "id": "comportamento",
            "label": "Como está o comportamento?",
            "tipo": "radio",
            "opcoes": {
                "Agitação intensa/violência": 1.8,
                "Ansiedade/agitação moderada": 0.9,
                "Calmo/cooperativo": 0.2
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Febre alta": 1.2,
                "Rigidez na nuca": 1.8,
                "Cefaleia intensa": 1.0,
                "Confusão/desorientação": 1.6,
                "Uso recente de álcool/drogas ou abstinência": 1.2,
                "Idoso (>65 anos) ou criança": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"sinais_associados": ["Rigidez na nuca"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Confusão/desorientação"]}, "min_cor": "laranja"},
        {"se": {"comportamento": "Agitação intensa/violência"}, "min_cor": "laranja"},
        {"se": {"inicio": "Início súbito nas últimas 24h", "sinais_associados": ["Febre alta"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Perda de memória")] = {
    "label": "Perda de memória",
    "perguntas": [
        {
            "id": "tipo_memoria",
            "label": "Qual tipo de perda de memória?",
            "tipo": "radio",
            "opcoes": {
                "Súbita recente (horas/dias)": 2.0,
                "Progressiva (semanas/meses)": 0.9,
                "Eventual/esquecimentos leves": 0.3
            }
        },
        {
            "id": "deficits",
            "label": "Há outros déficits neurológicos?",
            "tipo": "checkbox",
            "opcoes": {
                "Fraqueza/queda de força em um lado": 2.0,
                "Alteração na fala": 1.8,
                "Alteração visual súbita": 1.6,
                "Cefaleia intensa/pior da vida": 1.5,
                "Convulsão": 2.0
            }
        },
        {
            "id": "fatores",
            "label": "Fatores associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Trauma craniano recente": 1.6,
                "Uso de sedativos/álcool": 0.8,
                "Febre": 0.8,
                "Idoso (>65 anos)": 0.6,
                "Doenças prévias (hipotireoidismo, depressão)": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"tipo_memoria": "Súbita recente (horas/dias)", "deficits": ["Fraqueza/queda de força em um lado", "Alteração na fala", "Alteração visual súbita"]}, "min_cor": "vermelho"},
        {"se": {"deficits": ["Convulsão"]}, "min_cor": "vermelho"},
        {"se": {"fatores": ["Trauma craniano recente"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Insônia")] = {
    "label": "Insônia",
    "perguntas": [
        {
            "id": "duracao",
            "label": "Há quanto tempo está com insônia?",
            "tipo": "radio",
            "opcoes": {
                "Há menos de 1 semana": 0.3,
                "Entre 1–4 semanas": 0.6,
                "Há mais de 1 mês": 0.9
            }
        },
        {
            "id": "impacto",
            "label": "Qual o impacto funcional?",
            "tipo": "radio",
            "opcoes": {
                "Incapaz de trabalhar/estudar/dirigir": 1.2,
                "Prejuízo moderado no dia a dia": 0.7,
                "Leve/sem grande impacto": 0.2
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Ideação suicida": 2.0,
                "Humor elevado/energia excessiva (mania)": 1.5,
                "Ansiedade intensa/pânico": 0.9,
                "Apneia suspeita (ronco/pausas respiratórias)": 1.2,
                "Dor crônica": 0.6,
                "Uso de estimulantes (cafeína/anfetaminas)": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Ideação suicida"]}, "min_cor": "vermelho"},
        {"se": {"associados": ["Humor elevado/energia excessiva (mania)"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Apneia suspeita (ronco/pausas respiratórias)"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Sonolência excessiva")] = {
    "label": "Sonolência excessiva",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Quão intensa é a sonolência?",
            "tipo": "radio",
            "opcoes": {
                "Dorme durante conversas/dirigindo": 1.8,
                "Adormece em atividades passivas": 1.0,
                "Apenas cansaço ao longo do dia": 0.4
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas",
            "tipo": "radio",
            "opcoes": {
                "Súbito nas últimas 24–48h": 1.2,
                "Progressivo (semanas/meses)": 0.6
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Confusão/desorientação": 1.6,
                "Cefaleia matinal": 0.8,
                "Ronco alto/pausas respiratórias (apneia)": 1.2,
                "Uso de sedativos/álcool": 0.8,
                "Febre": 0.7,
                "Fraqueza/déficit focal": 1.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Confusão/desorientação", "Fraqueza/déficit focal"]}, "min_cor": "vermelho"},
        {"se": {"gravidade": "Dorme durante conversas/dirigindo"}, "min_cor": "laranja"},
        {"se": {"associados": ["Ronco alto/pausas respiratórias (apneia)"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Aumento súbito de sede ou fome")] = {
    "label": "Aumento súbito de sede ou fome",
    "perguntas": [
        {
            "id": "poliuria",
            "label": "Como está a urina?",
            "tipo": "radio",
            "opcoes": {
                "Urina em excesso (poliúria) e à noite": 1.5,
                "Leve aumento da frequência": 0.6,
                "Sem mudanças": 0.1
            }
        },
        {
            "id": "perda_peso",
            "label": "Houve perda de peso recente?",
            "tipo": "radio",
            "opcoes": {
                "Perda >5% em 1 mês": 1.2,
                "Perda leve (<5%)": 0.6,
                "Sem perda": 0.1
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Náusea/vômitos": 1.0,
                "Respiração rápida/cheiro de frutas (suspeita de cetoacidose)": 2.0,
                "Visão turva": 0.8,
                "Tremor/sudorese/confusão (hipoglicemia)": 1.8,
                "Infecção recente (febre/infecção urinária/pele)": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"sinais_associados": ["Respiração rápida/cheiro de frutas (suspeita de cetoacidose)"]}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Tremor/sudorese/confusão (hipoglicemia)"]}, "min_cor": "laranja"},
        {"se": {"poliuria": "Urina em excesso (poliúria) e à noite", "perda_peso": "Perda >5% em 1 mês"}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
FLUXOS[normalizar("Perda súbita de coordenação")] = {
    "label": "Perda súbita de coordenação",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Quando começou a perda de coordenação?",
            "tipo": "radio",
            "opcoes": {
                "Início súbito (minutos/horas)": 2.0,
                "Início em até 48h": 1.2,
                "Instalação lenta (dias/semanas)": 0.6
            }
        },
        {
            "id": "deficits_associados",
            "label": "Há outros déficits neurológicos?",
            "tipo": "checkbox",
            "opcoes": {
                "Fraqueza em um lado do corpo": 2.0,
                "Alteração na fala": 1.8,
                "Alteração visual súbita": 1.6,
                "Cefaleia muito intensa/pior da vida": 1.5,
                "Perda de sensibilidade/formigamentos": 1.0
            }
        },
        {
            "id": "fatores_risco",
            "label": "Fatores e contexto",
            "tipo": "checkbox",
            "opcoes": {
                "Trauma craniano recente": 1.6,
                "Uso de anticoagulantes": 1.4,
                "Pressão muito alta medida em casa": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio": "Início súbito (minutos/horas)", "deficits_associados": ["Fraqueza em um lado do corpo", "Alteração na fala", "Alteração visual súbita"]}, "min_cor": "vermelho"},
        {"se": {"deficits_associados": ["Cefaleia muito intensa/pior da vida"]}, "min_cor": "vermelho"},
        {"se": {"fatores_risco": ["Trauma craniano recente", "Uso de anticoagulantes"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Calafrios")] = {
    "label": "Calafrios",
    "perguntas": [
        {
            "id": "febre",
            "label": "Há febre associada?",
            "tipo": "radio",
            "opcoes": {
                "Febre ≥ 39°C": 1.6,
                "Febre 38–38,9°C": 1.0,
                "Sem febre": 0.2
            }
        },
        {
            "id": "frequencia",
            "label": "Frequência dos calafrios",
            "tipo": "radio",
            "opcoes": {
                "Várias vezes ao dia": 0.8,
                "Diários": 0.6,
                "Eventuais": 0.2
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Confusão/desorientação": 1.6,
                "Pressão baixa/tontura ao levantar": 1.4,
                "Dor ao urinar/urina turva": 0.9,
                "Tosse com catarro/dor torácica": 1.0,
                "Ferida com vermelhidão/calor/saída de pus": 1.0,
                "Calafrios após viagem/área endêmica": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Confusão/desorientação", "Pressão baixa/tontura ao levantar"]}, "min_cor": "vermelho"},
        {"se": {"febre": "Febre ≥ 39°C", "associados": ["Tosse com catarro/dor torácica", "Dor ao urinar/urina turva"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Ferida com vermelhidão/calor/saída de pus"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Sudorese noturna")] = {
    "label": "Sudorese noturna",
    "perguntas": [
        {
            "id": "duracao",
            "label": "Há quanto tempo ocorre?",
            "tipo": "radio",
            "opcoes": {
                "≥ 4 semanas": 1.0,
                "1–3 semanas": 0.6,
                "< 1 semana": 0.3
            }
        },
        {
            "id": "quantidade",
            "label": "Intensidade",
            "tipo": "radio",
            "opcoes": {
                "Encharca roupa/lençol": 1.0,
                "Moderada (troca de roupa)": 0.6,
                "Leve": 0.2
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Febre": 0.8,
                "Perda de peso não intencional": 1.2,
                "Tosse há > 2 semanas": 1.0,
                "Tosse com sangue": 1.6,
                "Inchaço dos linfonodos": 1.2,
                "Palpitações/ansiedade": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Tosse com sangue"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Perda de peso não intencional", "Inchaço dos linfonodos"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Perda de peso súbita")] = {
    "label": "Perda de peso súbita",
    "perguntas": [
        {
            "id": "magnitude",
            "label": "Quanto perdeu de peso?",
            "tipo": "radio",
            "opcoes": {
                "> 5% em 1 mês": 1.4,
                "3–5% em 1 mês": 1.0,
                "< 3% em 1 mês": 0.4
            }
        },
        {
            "id": "apetite",
            "label": "Como está o apetite?",
            "tipo": "radio",
            "opcoes": {
                "Muito diminuído": 0.8,
                "Normal": 0.3,
                "Aumentado (muita fome)": 0.6
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Sede/urinar muito": 1.0,
                "Náusea/vômitos persistentes": 1.0,
                "Diarreia crônica": 0.8,
                "Dificuldade para engolir (progressiva)": 1.4,
                "Fezes pretas (melena) ou sangue nas fezes": 1.6,
                "Febre e/ou sudorese noturna": 1.0,
                "Tremor/taquicardia/intolerância ao calor": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Fezes pretas (melena) ou sangue nas fezes"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Dificuldade para engolir (progressiva)"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Náusea/vômitos persistentes"]}, "min_cor": "amarelo"},
        {"se": {"apetite": "Aumentado (muita fome)", "associados": ["Sede/urinar muito"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Dor durante relação sexual")] = {
    "label": "Dor durante relação sexual",
    "perguntas": [
        {
            "id": "tipo_dor",
            "label": "Como é a dor?",
            "tipo": "radio",
            "opcoes": {
                "Dor pélvica intensa e súbita": 1.6,
                "Dor profunda recorrente": 1.0,
                "Dor superficial/queimação na entrada": 0.6
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Sangramento após a relação": 1.2,
                "Febre": 1.0,
                "Corrimento com odor/desconforto": 0.8,
                "Náusea/vômitos": 0.6,
                "Atraso menstrual/possível gestação": 1.2,
                "Dor testicular (em homens)": 1.2
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Início súbito recente": 1.0,
                "Semanas a meses": 0.6,
                "Há anos": 0.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"tipo_dor": "Dor pélvica intensa e súbita", "associados": ["Atraso menstrual/possível gestação"]}, "min_cor": "vermelho"},
        {"se": {"associados": ["Febre", "Corrimento com odor/desconforto"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Sangramento após a relação"]}, "min_cor": "amarelo"},
        {"se": {"associados": ["Dor testicular (em homens)"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Suspeita de daltonismo")] = {
    "label": "Suspeita de daltonismo",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Quando percebeu a alteração de cores?",
            "tipo": "radio",
            "opcoes": {
                "Desde a infância (sempre foi assim)": 0.1,
                "Percebi há meses/anos": 0.3,
                "Início súbito (dias/semanas)": 1.4
            }
        },
        {
            "id": "lateralidade",
            "label": "A alteração é em um ou nos dois olhos?",
            "tipo": "radio",
            "opcoes": {
                "Um olho apenas": 1.0,
                "Ambos os olhos": 0.4,
                "Não consigo dizer": 0.3
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados",
            "tipo": "checkbox",
            "opcoes": {
                "Dor ocular": 1.6,
                "Queda de acuidade visual": 1.6,
                "Fotofobia": 0.8,
                "Cefaleia": 0.6,
                "Olho vermelho": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio": "Início súbito (dias/semanas)", "associados": ["Dor ocular", "Queda de acuidade visual"]}, "min_cor": "vermelho"},
        {"se": {"lateralidade": "Um olho apenas", "associados": ["Olho vermelho", "Dor ocular"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}
FLUXOS[normalizar("Ausência de menstruação")] = {
    "label": "Ausência de menstruação",
    "perguntas": [
        {
            "id": "tempo",
            "label": "Há quanto tempo está sem menstruar?",
            "tipo": "radio",
            "opcoes": {
                "Atraso ≥ 4 semanas": 1.2,
                "Atraso de 1 a 3 semanas": 0.6,
                "Alguns dias": 0.2
            }
        },
        {
            "id": "possivel_gravidez",
            "label": "Há possibilidade de gravidez?",
            "tipo": "radio",
            "opcoes": {
                "Sim": 1.0,
                "Não": 0.0
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Dor abdominal intensa": 1.4,
                "Sangramento vaginal": 1.6,
                "Tontura/desmaio": 1.4,
                "Febre": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"possivel_gravidez": "Sim", "sinais_associados": ["Sangramento vaginal"]}, "min_cor": "vermelho"},
        {"se": {"possivel_gravidez": "Sim", "sinais_associados": ["Dor abdominal intensa"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Menstruação excessiva")] = {
    "label": "Menstruação excessiva",
    "perguntas": [
        {
            "id": "quantidade",
            "label": "Quantos absorventes/fraldas são usados por dia?",
            "tipo": "radio",
            "opcoes": {
                "≥ 8 totalmente encharcados": 1.8,
                "5–7 encharcados": 1.2,
                "Menos de 5": 0.5
            }
        },
        {
            "id": "duracao",
            "label": "Duração do sangramento",
            "tipo": "radio",
            "opcoes": {
                "≥ 8 dias": 1.2,
                "5–7 dias": 0.8,
                "Menos de 5 dias": 0.4
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Tontura/desmaio": 1.4,
                "Palidez intensa": 1.2,
                "Dor abdominal intensa": 0.8,
                "Febre": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quantidade": "≥ 8 totalmente encharcados", "sinais_associados": ["Tontura/desmaio"]}, "min_cor": "vermelho"},
        {"se": {"quantidade": "≥ 8 totalmente encharcados", "sinais_associados": ["Palidez intensa"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Tosse")] = {
    "label": "Tosse",
    "perguntas": [
        {
            "id": "duracao",
            "label": "Há quanto tempo está com tosse?",
            "tipo": "radio",
            "opcoes": {
                "≥ 3 semanas": 1.2,
                "1–2 semanas": 0.8,
                "< 1 semana": 0.4
            }
        },
        {
            "id": "caracteristica",
            "label": "Tipo de tosse",
            "tipo": "radio",
            "opcoes": {
                "Com sangue": 1.8,
                "Produtiva (com catarro)": 0.8,
                "Seca": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Falta de ar": 1.4,
                "Dor torácica": 1.4,
                "Febre": 1.0,
                "Perda de peso": 1.0,
                "Sudorese noturna": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"caracteristica": "Com sangue"}, "min_cor": "laranja"},
        {"se": {"caracteristica": "Com sangue", "associados": ["Falta de ar", "Dor torácica"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Hemorragia gengival intensa")] = {
    "label": "Hemorragia gengival intensa",
    "perguntas": [
        {
            "id": "frequencia",
            "label": "Com que frequência ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Diária": 1.0,
                "Semanal": 0.6,
                "Eventual": 0.3
            }
        },
        {
            "id": "duracao",
            "label": "Duração do sangramento",
            "tipo": "radio",
            "opcoes": {
                "≥ 10 minutos": 1.2,
                "5–9 minutos": 0.8,
                "< 5 minutos": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Hematomas frequentes": 1.2,
                "Sangramentos em outros locais": 1.4,
                "Febre": 0.6,
                "Cansaço extremo": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": ["Sangramentos em outros locais"]}, "min_cor": "laranja"},
        {"se": {"associados": ["Hematomas frequentes", "Cansaço extremo"]}, "min_cor": "amarelo"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Edema inexplicado")] = {
    "label": "Edema inexplicado",
    "perguntas": [
        {
            "id": "localizacao",
            "label": "Onde está o inchaço?",
            "tipo": "radio",
            "opcoes": {
                "Um lado do corpo apenas": 1.4,
                "Ambos os lados": 0.6,
                "Rosto/pálpebras": 1.0
            }
        },
        {
            "id": "velocidade",
            "label": "Velocidade de aparecimento",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.6,
                "Em poucos dias": 1.0,
                "Progressivo em semanas": 0.6
            }
        },
        {
            "id": "associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Falta de ar": 1.6,
                "Dor no peito": 1.6,
                "Febre": 0.8,
                "Vermelhidão/dor local": 1.2,
                "Aumento súbito de peso": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"velocidade": "Súbito (minutos/horas)", "associados": ["Falta de ar", "Dor no peito"]}, "min_cor": "vermelho"},
        {"se": {"localizacao": "Um lado apenas", "associados": ["Vermelhidão/dor local"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Mãos ou pés frios e arroxeados")] = {
    "label": "Mãos ou pés frios e arroxeados",
    "perguntas": [
        {
            "id": "frequencia",
            "label": "Com que frequência ocorre?",
            "tipo": "radio",
            "opcoes": {
                "Sempre, mesmo em clima quente": 1.6,
                "Principalmente em dias frios": 1.0,
                "Apenas ocasionalmente": 0.4
            }
        },
        {
            "id": "duracao",
            "label": "Há quanto tempo percebe isso?",
            "tipo": "radio",
            "opcoes": {
                "Mais de 1 mês": 1.2,
                "Entre 1–4 semanas": 0.8,
                "Menos de 1 semana": 0.3
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Dormência ou formigamento": 1.0,
                "Dor ao movimentar os dedos": 1.2,
                "Mudança de cor ao frio (branco/azul/vermelho)": 1.0,
                "Feridas nas extremidades": 1.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"sinais_associados": ["Feridas nas extremidades"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Perda progressiva da visão")] = {
    "label": "Perda progressiva da visão",
    "perguntas": [
        {
            "id": "velocidade",
            "label": "Em quanto tempo piorou a visão?",
            "tipo": "radio",
            "opcoes": {
                "Semanas a meses": 1.0,
                "Mais de 1 ano": 0.6,
                "Poucos dias": 1.4
            }
        },
        {
            "id": "olhos_afetados",
            "label": "Quantos olhos foram afetados?",
            "tipo": "radio",
            "opcoes": {
                "Um olho": 1.2,
                "Ambos os olhos": 0.8
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Dor ocular": 1.4,
                "Olho vermelho": 1.0,
                "Sensibilidade à luz (fotofobia)": 0.8,
                "Halos ao redor de luzes": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"velocidade": "Poucos dias", "sinais_associados": ["Dor ocular"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

FLUXOS[normalizar("Visão embaçada progressiva")] = {
    "label": "Visão embaçada progressiva",
    "perguntas": [
        {
            "id": "tempo",
            "label": "Há quanto tempo está embaçada?",
            "tipo": "radio",
            "opcoes": {
                "Semanas a meses": 0.8,
                "Mais de 1 ano": 0.5,
                "Poucos dias": 1.0
            }
        },
        {
            "id": "olhos_afetados",
            "label": "Quantos olhos foram afetados?",
            "tipo": "radio",
            "opcoes": {
                "Um olho": 1.0,
                "Ambos os olhos": 0.6
            }
        },
        {
            "id": "sinais_associados",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Cefaleia": 0.8,
                "Dificuldade para focar": 0.6,
                "Piora à noite": 0.6,
                "Alterações de cores": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"tempo": "Poucos dias", "sinais_associados": ["Cefaleia"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (3.5, "vermelho"),
        (2.0, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

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

    dic = dicionario_sintomas()
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
        cor_final = classificar_combinacao(
            sintomas=[s.lower() for s in st.session_state["sintomas_escolhidos"]],
            cores=cores_geradas
        )

        # --- ajuste conservador (idade/gravidez etc.) ---
        gravidez = str(st.session_state.get("gravida", "")).strip().lower() in ["sim", "true", "1"]
        idade_paciente = st.session_state.get("idade")
        ajuste_niveis = calcular_ajuste_por_fatores_conservador(
            sintomas_escolhidos=st.session_state["sintomas_escolhidos"],
            cores_individuais=cores_geradas,
            sintoma_para_sistema=sintoma_para_sistema,
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
