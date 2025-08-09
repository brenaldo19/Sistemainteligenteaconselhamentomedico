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
        "alergia cutânea", "reação alérgica", "lesões na pele", "manchas na pele", "coceira na pele", "inchaço incomum"
    ],
    "oftalmologico": [
        "alterações visuais súbitas", "dor ou olho vermelho", "inchaço nos olhos ou face",
        "corpo estranho nos olhos, ouvidos ou nariz"
    ],
    "otorrino": [
        "dor no ouvido", "coriza e espirros", "sangramento nasal", "alteração auditiva", "dificuldade pra engolir", "corpo estranho na garganta"
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

    Muitos recorrem a bancos de pesquisa, como o Google, quando se sentem doentes — não por ignorância, mas por desespero diante de um sistema de saúde que fecha as portas para quem não tem cartão de crédito. Este sistema foi criado para tentar atenuar, ainda que minimamente, essa desigualdade, oferecendo, de forma ética e responsável, um aconselhamento inteligente, confiável e acessível. Não porque somos melhores, mas sim porque somos iguais.

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
            "Náusea ou vômito junto da dor": "Enjoo ou vômitos ocorrendo junto com a dor testicular.",
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
        "Sensibilidade intensa": "Luz ou som causam dor ou mal-estar forte.",
        "Incômodo moderado": "Incomoda, mas ainda é tolerável."
        }
    },

"Dor no ouvido": {
    "definicao": "Dor localizada dentro do ouvido, podendo estar acompanhada de secreção ou zumbido.",
    "popular": "Quando o ouvido dói, sai alguma coisa de dentro, faz barulho estranho ou não melhora com remédio.",
    "clinico": "Otalgia",
    "termos": {
        "Secreção purulenta": "Sai líquido grosso e amarelo ou esverdeado do ouvido.",
        "Sem melhora com analgésico": "A dor continua mesmo após tomar remédio comum.",
        "Zumbido": "Barulho constante no ouvido, como apito ou chiado."
        }
    },

"Alterações na fala": {
    "definicao": "Mudança na forma de falar, que pode ficar lenta, confusa ou arrastada.",
    "popular": "Quando a pessoa começa a falar estranho, enrolado ou muito devagar, como se tivesse bêbada ou confusa.",
    "clinico": "Disartria ou afasia",
    "termos": {
        "Fala arrastada": "As palavras saem devagar e desconexas.",
        "Fala lenta ou confusa": "Parece esquecer as palavras ou trocar por outras."
        }
    },

"Alterações visuais súbitas": {
    "definicao": "Mudança repentina na forma de enxergar, com visão turva, dupla ou embaçada.",
    "popular": "Quando a vista escurece, dobra ou embaça do nada, dificultando enxergar mesmo por pouco tempo.",
    "clinico": "Alteração visual aguda",
    "termos": {
        "Visão muito turva": "Tudo fica embaçado como se estivesse com catarata.",
        "Visão dupla ou embaçada": "Vê dois objetos ou tudo com contorno borrado.",
        "Dificuldade temporária pra focar": "Fica difícil ler ou olhar para um ponto específico por um tempo."
        }
    },

"Queimação no peito": {
    "definicao": "Sensação de ardência ou calor no peito, geralmente após alimentação.",
    "popular": "Aquela sensação de fogo no meio do peito, que piora depois de comer ou deitar.",
    "clinico": "Refluxo gastroesofágico ou dispepsia",
    "termos": {
        "Suor frio": "Começa a suar mesmo estando frio, geralmente com mal-estar.",
        "Após comer alimentos pesados": "Sente a queimação logo depois de uma refeição gordurosa.",
        "Piora ao deitar": "Deitado, o sintoma se intensifica ou sobe até a garganta."
        }
    },

"Coceira na pele": {
    "definicao": "Sensação que provoca vontade de coçar, podendo estar associada a lesões.",
    "popular": "Quando a pele começa a coçar muito, com ou sem manchas vermelhas. Às vezes não passa nem com creme ou banho.",
    "clinico": "Prurido cutâneo",
    "termos": {
        "Placas vermelhas": "Manchas grandes e avermelhadas que coçam.",
        "Não alivia": "A coceira não melhora com nada.",
        "Localizada": "Apenas em uma parte do corpo."
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
        "Fechamento dos olhos": "A pálpebra incha tanto que o olho quase não abre.",
        "Alergia ou trauma": "Começou após coçar muito ou depois de uma batida."
        }
    },

"Ansiedade ou agitação intensas": {
    "definicao": "Estado de excitação ou preocupação extrema, com sintomas físicos ou comportamentais.",
    "popular": "Quando a pessoa fica muito agitada, com o coração disparado, falta de ar, tremores ou até ideias confusas.",
    "clinico": "Crise de ansiedade ou agitação psicomotora",
    "termos": {
        "Agitação extrema com risco de autoagressão ou agressividade": "Perde o controle, pode se machucar ou agredir outros.",
        "Crise intensa com falta de ar, tremores ou choro incontrolável": "Mistura de sintomas físicos e emocionais, como se fosse desmaiar.",
        "Pensamentos acelerados": "Mente não para, com muitos pensamentos ao mesmo tempo."
        }
    },

"Alterações urinárias": {
    "definicao": "Mudança na frequência, volume ou capacidade de urinar.",
    "popular": "Quando vai ao banheiro muitas vezes ou simplesmente não consegue fazer xixi, mesmo com vontade.",
    "clinico": "Disúria, poliúria ou retenção",
    "termos": {
        "Incapacidade de urinar": "Não consegue fazer xixi, mesmo forçando.",
        "Aumento de frequência": "Sente vontade de urinar toda hora, com pouco volume."
        }
    },

"Corpo estranho nos olhos, ouvidos ou nariz": {
    "definicao": "Entrada de objeto ou substância em cavidades sensoriais, com ou sem sintomas.",
    "popular": "Quando algo entra no olho, nariz ou ouvido — como sujeira, grão ou inseto — e pode causar dor, secreção ou febre.",
    "clinico": "Presença de corpo estranho em cavidade sensorial",
    "termos": {
        "Secreção com febre": "Sai líquido e tem febre junto, sinal de infecção.",
        "Presença confirmada, mas sem sintomas": "O objeto está lá, mas não está doendo nem incomodando."
        }
    },

"Ferimentos ou cortes com objetos": {
    "definicao": "Lesão na pele causada por faca, vidro, objetos pontiagudos ou cortantes.",
    "popular": "Quando a pessoa se corta com algo e o ferimento pode ser leve ou profundo, com risco de infecção.",
    "clinico": "Laceração ou corte",
    "termos": {
        "Corte profundo": "Atinge camadas mais profundas da pele, sangra bastante.",
        "Exposição de tecidos": "Dá pra ver carne ou gordura por baixo do corte.",
        "Sinais de infecção (pus, vermelhidão)": "Mostra que o corte inflamou ou infeccionou.",
        "Corte leve, limpo e controlado": "Pequeno, sem sangramento forte e fácil de limpar."
        }
    },

"Engasgo ou obstrução das vias aéreas": {
    "definicao": "Dificuldade de respirar causada por algo bloqueando a passagem do ar.",
    "popular": "Quando algo entala e a pessoa não consegue respirar direito, nem tossir com força.",
    "clinico": "Obstrução das vias aéreas superiores",
    "termos": {
        "Engasgo com tosse ineficaz": "Tenta tossir, mas o ar não sai e a tosse é fraca.",
        "Respiração ofegante": "Respira com esforço e dificuldade."
        }
    },

"Sinais de intoxicação ou envenenamento": {
    "definicao": "Efeitos provocados por substâncias tóxicas ingeridas, inaladas ou em contato com a pele.",
    "popular": "Quando a pessoa bebe, come ou entra em contato com algo que pode fazer mal, como produto de limpeza ou veneno.",
    "clinico": "Intoxicação exógena",
    "termos": {
        "Substância tóxica": "Produto que pode causar dano ao corpo, como álcool em gel, remédio ou veneno.",
        "Ingestão suspeita": "Acredita-se que a pessoa pode ter consumido algo perigoso, mesmo sem certeza."
        }
    },

    "Retenção urinária": {
    "definicao": "Dificuldade ou incapacidade de urinar completamente, mesmo com sensação de bexiga cheia.",
    "popular": "Quando a pessoa sente vontade de fazer xixi, mas não consegue ou sai só um pouco, mesmo com a bexiga cheia.",
    "clinico": "Retenção urinária aguda ou crônica",
    "termos": {
        "Distensão abdominal": "Barriga inchada ou dura por causa da bexiga cheia.",
        "Jato fraco com sensação de bexiga cheia": "Sai pouco xixi e continua a vontade, como se não tivesse aliviado."
        }
    },

"Tremores ou movimentos involuntários": {
    "definicao": "Movimentos que o corpo faz sozinho, sem controle consciente, podendo ser leves ou fortes.",
    "popular": "Quando a mão ou o corpo começa a tremer sem motivo ou faz movimentos esquisitos sozinho, sem conseguir parar.",
    "clinico": "Movimentos involuntários ou tremores",
    "termos": {
        "Movimentos anormais": "Movimentos inesperados, como sacudidas ou repuxos.",
        "Dificuldade pra parar": "Mesmo tentando, não consegue controlar o tremor.",
        "Tremores leves": "Pequenas vibrações no corpo, geralmente nas mãos ou queixo."
        }
    },

"Dificuldade pra engolir": {
    "definicao": "Sensação de que a comida ou líquido não desce corretamente pela garganta.",
    "popular": "Quando engolir água ou comida parece difícil ou incômodo, como se algo estivesse travando na garganta.",
    "clinico": "Disfagia",
    "termos": {
        "Engolir líquidos": "Tem dificuldade até com água, leite ou suco.",
        "Engolir sólidos": "Só sente problema com alimentos mais consistentes.",
        "Leve desconforto": "Sensação de 'arranhando' ou dificuldade pequena ao engolir."
        }
    },

"Icterícia": {
    "definicao": "Cor amarelada na pele e nos olhos, geralmente causada por problemas no fígado.",
    "popular": "Quando a pele ou os olhos da pessoa ficam amarelos, mesmo que levemente. É comum em recém-nascidos ou problemas no fígado.",
    "clinico": "Icterícia",
    "termos": {
        "Amarelado leve": "Tom amarelado visível de perto, mas não forte.",
        "Coloração discreta": "Amarelo quase imperceptível, mais visível na luz."
        }
    },

"Corpo estranho na garganta": {
    "definicao": "Sensação ou presença real de algo preso na garganta.",
    "popular": "Quando parece que tem algo entalado na garganta — um pedaço de comida, espinha de peixe ou qualquer coisa — e a pessoa sente incômodo ao engolir.",
    "clinico": "Obstrução faríngea leve",
    "termos": {
        "Corpo estranho preso": "Algo realmente ficou preso ou está incomodando na garganta.",
        "Dor ao engolir": "Ato de engolir dói mais que o normal.",
        "Sensação de algo preso": "Mesmo sem ter nada visível, parece que algo ficou ali."
        }
    },

"Sangramento gastrointestinal": {
    "definicao": "Presença de sangue na evacuação ou vômito, geralmente indicando sangramento interno.",
    "popular": "Quando sai sangue pelo vômito ou pelas fezes, o que pode assustar e indicar problema no estômago ou intestino.",
    "clinico": "Hemorragia digestiva",
    "termos": {
        "Sangue vivo": "Sangue vermelho claro, que não passou muito tempo no intestino ou estômago."
        }
    },

"Dor no ombro ou braço": {
    "definicao": "Dor localizada ou que se espalha entre o ombro e o braço, podendo indicar lesão ou outro problema.",
    "popular": "Quando o ombro ou o braço doem, formigam ou não se mexem direito, com dor que pode ir do pescoço até os dedos.",
    "clinico": "Dor irradiada ou lesão músculo-esquelética",
    "termos": {
        "Dor irradiando": "A dor começa em um ponto e se espalha.",
        "Formigamento": "Sensação de 'agulhadas' ou dormência.",
        "Limitação de movimento": "Não consegue levantar ou mexer o braço direito por causa da dor."
        }
    },

"Náusea ou enjoo": {
    "definicao": "Sensação de mal-estar no estômago, com ou sem vontade de vomitar.",
    "popular": "Quando bate aquele enjoo, como se fosse vomitar ou estivesse com o estômago revirado.",
    "clinico": "Náusea",
    "termos": {
        "Mal-estar": "Sensação geral ruim, sem motivo claro.",
        "Desconforto passageiro": "Enjoo leve que melhora com o tempo.",
        "Enjoo": "Sensação clara de que vai vomitar, mesmo que não vomite."
        }
    },

"Dor na perna e dificuldade pra caminhar": {
    "definicao": "Dor nas pernas associada à limitação nos movimentos ou dificuldade ao andar.",
    "popular": "Quando andar fica difícil por causa da dor ou fraqueza nas pernas, podendo até causar queda.",
    "clinico": "Claudicação ou limitação motora",
    "termos": {
        "Dificuldade de mover a perna": "A perna parece pesada, fraca ou trava.",
        "Queda": "A dor causou desequilíbrio ou a pessoa realmente caiu."
        }
    },

"Dores no pescoço ou rigidez da nuca": {
    "definicao": "Dor localizada na região cervical ou dificuldade de movimentar o pescoço normalmente.",
    "popular": "Quando o pescoço fica duro, dolorido e difícil de mexer, como se tivesse travado ou dormido de mau jeito.",
    "clinico": "Rigidez cervical ou torcicolo",
    "termos": {
        "Rigidez importante": "O pescoço mal se mexe de tanta dor.",
        "Posição ruim": "Ficou numa posição desconfortável por muito tempo.",
        "Dor localizada": "A dor é em um ponto específico do pescoço."
        }
    },

    "Comportamento estranho à normalidade": {
    "definicao": "Mudanças repentinas no modo como a pessoa age, pensa ou se comunica.",
    "popular": "Quando a pessoa começa a agir de forma esquisita do nada — vê coisas que não existem, parece confusa, fala coisas desconexas ou fica estranhamente calma ou agitada.",
    "clinico": "Alteração aguda de comportamento",
    "termos": {
        "Alteração súbita de consciência": "Quando a pessoa muda do normal para o confuso ou estranho rapidamente.",
        "Alucinação": "Ver, ouvir ou sentir coisas que não estão lá.",
        "Lucidez parcial": "Está consciente, mas confusa ou com falas sem sentido.",
        "Comportamento excêntrico": "Atitudes muito fora do padrão da pessoa, sem motivo aparente."
        }
    },

"Sangramento ativo": {
    "definicao": "Perda visível de sangue que ainda está acontecendo, por corte, lesão ou outra causa.",
    "popular": "Quando a pessoa está sangrando de verdade — seja pouco ou muito — e ainda não parou totalmente.",
    "clinico": "Hemorragia ativa",
    "termos": {
        "Palidez": "Pessoa muito branca, sinal de perda de sangue.",
        "Sangramento controlado": "Parou ou está quase parando, mas ainda tem um pouco.",
        "Volume considerável": "Sangue suficiente pra encharcar pano ou roupa, ou que não para com pressão leve."
        }
    },

"Alergia cutânea": {
    "definicao": "Reação alérgica que afeta a pele, causando coceira, vermelhidão ou descamação.",
    "popular": "Quando a pele fica irritada, coçando, com manchas vermelhas ou até sem sintomas, mas com aspecto diferente.",
    "clinico": "Dermatite alérgica",
    "termos": {
        "Coceira intensa": "Vontade forte de coçar, difícil de segurar.",
        "Descamação": "Quando a pele começa a soltar pequenas peles finas.",
        "Assintomática": "A pele muda, mas não dói nem coça."
        }
    },

"Reação alérgica": {
    "definicao": "Resposta do corpo a uma substância estranha, podendo causar sintomas leves ou graves.",
    "popular": "Quando o corpo reage mal a algo — como comida, remédio ou picada — e aparecem manchas vermelhas, coceira ou até sintomas no corpo todo.",
    "clinico": "Reação anafilática ou alérgica sistêmica",
    "termos": {
        "Erupções leves": "Manchinhas ou bolinhas que aparecem na pele e somem rápido.",
        "Placas vermelhas": "Manchas maiores, elevadas e vermelhas.",
        "Sintomas sistêmicos": "Reação que afeta além da pele — como falta de ar, inchaço ou tontura."
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
        "Pus": "Líquido amarelado ou esverdeado que sai da ferida.",
        "Secreção local": "Qualquer líquido saindo do machucado.",
        "Vermelhidão": "Área ao redor da ferida está bem vermelha."
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
        "Perda de consciência prolongada": "Desmaiou e demorou pra acordar.",
        "Palidez": "Ficou muito branca antes ou depois do desmaio.",
        "Tontura ao levantar": "Fica tonto quando se levanta rápido, como se fosse desmaiar."
        }
    },

"Dificuldade respiratória": {
    "definicao": "Problema mecânico para puxar ou soltar o ar, com esforço visível para respirar.",
    "popular": "É diferente de só sentir falta de ar. Aqui, a pessoa parece estar 'lutando' pra respirar, com o peito subindo muito, chiado forte ou até sensação de sufocamento.",
    "clinico": "Insuficiência respiratória ou esforço respiratório aumentado",
    "termos": {
        "Chiado grave": "Barulho alto no peito, como se estivesse assobiando ao respirar.",
        "Contínua": "Não melhora mesmo depois de descansar ou sentar.",
        "Desconforto extremo": "Sensação intensa de não conseguir respirar, causando pânico ou cansaço."
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
        "Púrpuras": "Manchas roxas que não desaparecem quando apertadas.",
        "Erupções": "Pequenas bolinhas ou manchas que surgem repentinamente.",
        "Irritações de contato": "Manchas vermelhas que coçam e aparecem após tocar algo, como produto ou tecido."
        }
    },

"Dor ou olho vermelho": {
    "definicao": "Desconforto ocular associado a vermelhidão, ardência ou sensibilidade à luz.",
    "popular": "Quando o olho está vermelho, dói, arde ou fica sensível à luz. Pode estar seco ou soltando secreção.",
    "clinico": "Conjuntivite ou inflamação ocular",
    "termos": {
        "Secreção": "Líquido que escorre do olho, podendo ser claro ou amarelado.",
        "Sensibilidade à luz": "Dificuldade de manter os olhos abertos em lugares claros.",
        "Ardência": "Sensação de queimação no olho.",
        "Olhos secos": "Falta de lágrima ou desconforto como se houvesse areia no olho."
        }
    },

"Sangramento vaginal": {
    "definicao": "Perda de sangue pela vagina fora do ciclo menstrual esperado ou em volume incomum.",
    "popular": "Quando desce sangue fora da menstruação normal ou vem em grande quantidade, podendo assustar.",
    "clinico": "Sangramento uterino anormal",
    "termos": {
        "Abundante": "Fluxo forte, que encharca o absorvente rapidamente.",
        "Fora do ciclo": "Sangramento inesperado, sem estar no período menstrual."
        }
    },

"Dor ou dificuldade ao urinar": {
    "definicao": "Sensação de dor, queimação ou esforço para urinar, geralmente por infecção.",
    "popular": "Quando arde ao fazer xixi, a urina sai fraca ou vem acompanhada de dor na barriga. Pode dar vontade toda hora e sair pouco.",
    "clinico": "Disúria ou infecção urinária",
    "termos": {
        "Ardência": "Queimação na hora de urinar.",
        "Desconforto abdominal": "Dor no pé da barriga que acompanha a vontade de urinar."
        }
    },

"Inchaço incomum": {
    "definicao": "Acúmulo de líquido em partes do corpo, especialmente mãos, pernas, rosto ou barriga.",
    "popular": "Quando alguma parte do corpo incha de repente, incha tudo ao mesmo tempo ou parece só um leve acúmulo de água. Pode ter várias causas.",
    "clinico": "Edema",
    "termos": {
        "Inchaço súbito": "Aparece de uma hora pra outra, geralmente em uma região.",
        "Inchaço generalizado": "Corpo inteiro parece mais 'cheio', inclusive rosto e barriga.",
        "Leve retenção": "A pele marca com o dedo ou a roupa aperta mais que o normal."
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
        "Sangue vermelho vivo em grande quantidade": "Saída de sangue vermelho brilhante em volume elevado pelo reto.",
        "Sangue moderado com dor abdominal": "Sangramento perceptível acompanhado de dor na região abdominal.",
        "Poucas gotas de sangue no papel higiênico": "Sangue em pequena quantidade visível apenas no papel após evacuar.",
        "Sangramento leve e isolado": "Pequeno sangramento que ocorre uma única vez."
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
        "Inflamação visível": "Quando a articulação está inchada, vermelha ou quente.",
        "Mobilidade limitada": "Dificuldade pra mexer o local normalmente.",
        "Edema": "É o nome técnico para inchaço.",
        "Trauma": "É um impacto no local que está doendo,como uma batida"
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
        "Instabilidade": "Sensação de desequilíbrio, como se o chão balançasse.",
        "Suor frio": "Suor que aparece com mal-estar, mesmo sem estar calor.",
        "Sensação de queda iminente": "É quando tem-se a sensação que no próximo momentovocê vai cair com certeza,mesmo que isso não aconteça",
        "Fraqueza súbita": "É a sensação de fraqueza que vem do nada"
        }
    },
"Formigamento ou perda de força": {
    "definicao": "Sensação de dormência, formigamento ou fraqueza em uma parte do corpo.",
    "popular": "Pode parecer que a mão ou perna está dormente ou sem força. Se for de repente, é mais preocupante.",
    "clinico": "Parestesia ou déficit motor",
    "termos": {
        "Fala arrastada": "Quando a pessoa fala devagar ou parece enrolada.",
        "Lado do corpo": "Refere-se a um dos lados, tipo só o braço e perna direitos ou esquerdos."
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
        "Irradiação": "É quando a dor nas costas vai para a perna ou outras partes.",
        "Urinar": "Fazer xixi.",
        "Repentina": "Começou a acontecer do nada",
        "Localizada": "Quando a dor está em um só ponto das costas"
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
        "Batimentos acelerados": "Quando o coração parece estar correndo.",
        "Falta de ar": "Dificuldade para respirar junto com os batimentos."
        }
    },
"Diarreia": {
    "definicao": "Evacuação líquida ou amolecida mais vezes que o normal.",
    "popular": "Quando vai ao banheiro várias vezes com fezes moles ou líquidas, podendo vir com dor de barriga.",
    "clinico": "Diarreia",
    "termos": {
        "Evacuações": "Fazer cocô.",
        "Sinais de desidratação": "Boca seca, pouca urina, olhos fundos, fraqueza."
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
        "Sopro Sustentado"
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
            st.markdown("🔎 Possíveis sintomas relacionados: **(Não temos sintomas para condições visuais progressivas,procure um médico oftalmologista para melhor orientação)**")
        else:
            st.error("🚨 Campo visual comprometido. Procure avaliação oftalmológica.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Não temos sintomas para condições visuais progressivas,procure um médico o quanto antes)**")
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
            st.markdown("🔎 Possíveis sintomas relacionados: **Não temos sintomas para condições visuais possivelmente daltônicas,procure um médico oftalmologista para melhor orientação)**")
        else:
            st.error("🚨 Dificuldade significativa em distinguir cores. Pode ser bom investigar daltonismo.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Não temos sintomas para condições visuais possivelmente daltônicas,procure um médico oftalmologista o quanto antes)**")
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
            st.markdown("🔎 Possíveis sintomas relacionados: **(Não possuímos sintomas específicos sobre circulação,é ideal procurar um médico)**")
        else:
            st.error("🚨 Circulação lenta. Pode indicar desidratação, vasoconstrição ou problema circulatório.")
            st.markdown("🔎 Possíveis sintomas relacionados: **(Não possuímos sintomas específicos sobre circulação,mas o seu caso pode ser grave,consulte um médico o quanto antes)**")

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
            st.markdown("🔎 Possíveis sintomas relacionados: **Manchas na pele, Infecção em ferida,lesões na pele, alergia cutânea**")
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
            st.warning("⚠️ Sinal de alteração auditiva.")
            st.markdown("🔎 Possíveis sintomas relacionados: **Alteração auditiva**")
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

def opcoes_sangramento_ativo():
    return [
        "Sangramento intenso que não para",
        "Sangramento moderado com tontura ou palidez",
        "Sangramento controlado, mas com volume considerável",
        "Sangramento pequeno e controlado"
    ]

def classificar_sangramento_ativo(resp):
    if resp == "Sangramento intenso que não para":
        return "vermelho", "Sangramento abundante e contínuo pode indicar risco grave de hemorragia. Procure socorro imediatamente."
    elif resp == "Sangramento moderado com tontura ou palidez":
        return "laranja", "Sinais de perda significativa de sangue. É necessário atendimento médico rápido."
    elif resp == "Sangramento controlado, mas com volume considerável":
        return "amarelo", "Requer atenção e possível avaliação, mesmo que controlado."
    else:
        return "verde", "Sangramento leve e controlado. Continue observando."

# Continuação: sintomas 11 a 21 no novo modelo (funções de opções e classificação)

def opcoes_desmaio_tontura():
    return [
        "Desmaio com perda de consciência prolongada",
        "Desmaio com recuperação, mas com confusão ou palidez",
        "Tontura ao levantar, sem outros sintomas",
        "Sensação leve de desequilíbrio"
    ]

def classificar_desmaio_tontura(resp):
    if resp == "Desmaio com perda de consciência prolongada":
        return "vermelho", "Pode indicar condição neurológica ou cardiovascular grave. Atendimento imediato é essencial."
    elif resp == "Desmaio com recuperação, mas com confusão ou palidez":
        return "laranja", "Sugere instabilidade circulatória. Avaliação médica é recomendada."
    elif resp == "Tontura ao levantar, sem outros sintomas":
        return "amarelo", "Pode ser hipotensão postural. Hidrate-se e evite movimentos bruscos."
    else:
        return "verde", "Tontura leve e isolada. Continue monitorando."

def opcoes_comportamento_estranho():
    return [
        "Alteração súbita de consciência, agressividade ou alucinação",
        "Confusão mental com febre ou sinais de infecção",
        "Desorientação leve, mas com lucidez parcial",
        "Comportamento excêntrico, mas sem risco"
    ]

def classificar_comportamento_estranho(resp):
    if resp == "Alteração súbita de consciência, agressividade ou alucinação":
        return "vermelho", "Mudanças comportamentais graves podem indicar distúrbio neurológico ou intoxicação. Procure ajuda urgente."
    elif resp == "Confusão mental com febre ou sinais de infecção":
        return "laranja", "Pode estar associado a infecção grave como meningite. Atenção médica necessária."
    elif resp == "Desorientação leve, mas com lucidez parcial":
        return "amarelo", "Alteração leve, porém merece observação."
    else:
        return "verde", "Comportamento sem risco evidente. Acompanhe a evolução."

def opcoes_dificuldade_respiratoria():
    return [
        "Falta de ar intensa com lábios roxos, confusão ou chiado grave",
        "Falta de ar moderada e contínua",
        "Respiração acelerada sem desconforto extremo",
        "Respiração leve com leve desconforto"
    ]

def classificar_dificuldade_respiratoria(resp):
    if resp == "Falta de ar intensa com lábios roxos, confusão ou chiado grave":
        return "vermelho", "Sinais de insuficiência respiratória grave. Procure atendimento imediato."
    elif resp == "Falta de ar moderada e contínua":
        return "laranja", "Desconforto respiratório relevante. Requer avaliação médica."
    elif resp == "Respiração acelerada sem desconforto extremo":
        return "amarelo", "Situação leve, mas que exige atenção se persistir."
    else:
        return "verde", "Sem alterações importantes na respiração."

def opcoes_dor_nas_costas():
    return [
        "Dor intensa e repentina com dificuldade para andar ou urinar",
        "Dor forte persistente que não melhora com repouso",
        "Dor moderada após esforço físico",
        "Dor leve, localizada e controlável"
    ]

def classificar_dor_nas_costas(resp):
    if resp == "Dor intensa e repentina com dificuldade para andar ou urinar":
        return "vermelho", "Pode indicar compressão neurológica ou problema renal. Procure socorro médico."
    elif resp == "Dor forte persistente que não melhora com repouso":
        return "laranja", "Dor de difícil controle. Avaliação ortopédica ou clínica pode ser necessária."
    elif resp == "Dor moderada após esforço físico":
        return "amarelo", "Causa mecânica provável. Repouso e analgesia podem ser suficientes."
    else:
        return "verde", "Dor leve e autolimitada. Monitoramento apenas."

def opcoes_reacao_alergica():
    return [
        "Inchaço de rosto, lábios ou dificuldade para respirar",
        "Coceira intensa com placas vermelhas pelo corpo",
        "Erupções leves e localizadas",
        "Alergia leve e sem sintomas sistêmicos"
    ]

def classificar_reacao_alergica(resp):
    if resp == "Inchaço de rosto, lábios ou dificuldade para respirar":
        return "vermelho", "Sinais de anafilaxia. Atendimento de emergência é fundamental."
    elif resp == "Coceira intensa com placas vermelhas pelo corpo":
        return "laranja", "Reação alérgica significativa. Requer tratamento e monitoramento."
    elif resp == "Erupções leves e localizadas":
        return "amarelo", "Pode ser controlada com cuidados simples. Observe evolução."
    else:
        return "verde", "Sem sinais de gravidade. Cuidados básicos são suficientes."

def opcoes_alteracoes_urinarias():
    return [
        "Urina com sangue ou incapacidade de urinar",
        "Dor intensa ao urinar com febre",
        "Ardência leve ou aumento de frequência",
        "Urina normal com pequeno desconforto"
    ]

def classificar_alteracoes_urinarias(resp):
    if resp == "Urina com sangue ou incapacidade de urinar":
        return "vermelho", "Alterações graves no trato urinário. Procure atendimento imediatamente."
    elif resp == "Dor intensa ao urinar com febre":
        return "laranja", "Sugere infecção urinária avançada. Avaliação médica necessária."
    elif resp == "Ardência leve ou aumento de frequência":
        return "amarelo", "Sintomas leves, mas que podem evoluir. Hidratação e atenção são importantes."
    else:
        return "verde", "Sem sinais de alerta. Situação tranquila."

def opcoes_formigamento_perda_forca():
    return [
        "Perda súbita de força ou fala arrastada",
        "Formigamento em um lado do corpo",
        "Leve dormência nas mãos ou pés",
        "Sensação leve e passageira"
    ]

def classificar_formigamento_perda_forca(resp):
    if resp == "Perda súbita de força ou fala arrastada":
        return "vermelho", "Sinais clássicos de AVC. Atendimento imediato é essencial."
    elif resp == "Formigamento em um lado do corpo":
        return "laranja", "Pode indicar início de comprometimento neurológico. Necessita avaliação."
    elif resp == "Leve dormência nas mãos ou pés":
        return "amarelo", "Alteração sensitiva leve. Observe evolução."
    else:
        return "verde", "Sensação transitória e sem risco."

def opcoes_inchaco():
    return [
        "Inchaço súbito em uma perna com dor intensa",
        "Inchaço generalizado com falta de ar",
        "Inchaço leve no final do dia",
        "Leve retenção sem desconforto"
    ]

def classificar_inchaco(resp):
    if resp == "Inchaço súbito em uma perna com dor intensa":
        return "vermelho", "Risco de trombose venosa profunda. Procure emergência."
    elif resp == "Inchaço generalizado com falta de ar":
        return "laranja", "Pode estar associado a insuficiência cardíaca ou renal. Avaliação médica é necessária."
    elif resp == "Inchaço leve no final do dia":
        return "amarelo", "Retenção de líquidos leve. Elevação das pernas e hidratação ajudam."
    else:
        return "verde", "Sem alterações relevantes. Situação sob controle."

def opcoes_sangramento_vaginal():
    return [
        "Durante gravidez, com dor ou sangramento intenso",
        "Abundante fora do ciclo com dor abdominal",
        "Moderado e inesperado",
        "Leve e esperado"
    ]

def classificar_sangramento_vaginal(resp):
    if resp == "Durante gravidez, com dor ou sangramento intenso":
        return "vermelho", "Pode indicar risco à gestação. Procure ajuda médica imediatamente."
    elif resp == "Abundante fora do ciclo com dor abdominal":
        return "laranja", "Pode ser distúrbio hormonal ou patológico. Avaliação necessária."
    elif resp == "Moderado e inesperado":
        return "amarelo", "Merece atenção, mesmo sem outros sintomas."
    else:
        return "verde", "Dentro do esperado. Acompanhe evolução."

def opcoes_lesoes_na_pele():
    return [
        "Púrpuras, vermelhas escuras ou com febre alta",
        "Erupções espalhadas com coceira intensa",
        "Manchas leves e pequenas",
        "Pequenas irritações de contato"
    ]

def classificar_lesoes_na_pele(resp):
    if resp == "Púrpuras, vermelhas escuras ou com febre alta":
        return "vermelho", "Podem indicar infecção grave ou reação sistêmica. Procure emergência."
    elif resp == "Erupções espalhadas com coceira intensa":
        return "laranja", "Alergia importante ou virose. Requer observação."
    elif resp == "Manchas leves e pequenas":
        return "amarelo", "Alteração cutânea leve. Cuidados simples são suficientes."
    else:
        return "verde", "Irritação leve e sem risco."

def opcoes_dor_ou_olho_vermelho():
    return [
        "Dor ocular intensa ou perda súbita da visão",
        "Olhos vermelhos com secreção e sensibilidade à luz",
        "Irritação leve com ardência",
        "Olhos secos ou cansados"
    ]

def classificar_dor_ou_olho_vermelho(resp):
    if resp == "Dor ocular intensa ou perda súbita da visão":
        return "vermelho", "Possível emergência oftalmológica. Atendimento urgente necessário."
    elif resp == "Olhos vermelhos com secreção e sensibilidade à luz":
        return "laranja", "Pode ser conjuntivite ou inflamação ocular. Requer atenção."
    elif resp == "Irritação leve com ardência":
        return "amarelo", "Situação leve. Observe e higienize a área."
    else:
        return "verde", "Sem sinais de gravidade ocular."

def opcoes_dor_perna_caminhar():
    return[
        "Dor súbita com inchaço, vermelhidão ou dificuldade de mover a perna",
        "Dor intensa após queda ou lesão recente",
        "Dor moderada, persistente, mas ainda consegue caminhar",
        "Dor leve e passageira, sem sinais visíveis"
    ]

def classificar_dor_perna_caminhar(resp):
    if resp == "Dor súbita com inchaço, vermelhidão ou dificuldade de mover a perna":
        return "vermelho", "Sinais de trombose ou lesão grave. Atendimento imediato."
    elif resp == "Dor intensa após queda ou lesão recente":
        return "laranja", "Pode haver fratura ou entorse. Avaliação ortopédica recomendada."
    elif resp == "Dor moderada, persistente, mas ainda consegue caminhar":
        return "amarelo", "Quadro leve a moderado. Requer repouso e analgesia."
    else:
        return "verde", "Dor leve e passageira. Observe evolução."
            
def opcoes_intoxicacao():
    return [
        "Ingestão de substância tóxica com confusão, vômito ou inconsciência",
        "Ingestão suspeita com sintomas moderados (náusea, tontura)",
        "Ingestão leve com sintomas leves (enjoo leve, dor de barriga)",
        "Ingestão pequena com sintomas ausentes ou mínimos"
    ]

def classificar_intoxicacao(resposta):
    if resposta == "Ingestão de substância tóxica com confusão, vômito ou inconsciência":
        return "vermelho", "Sinais graves de intoxicação. Procure atendimento médico imediatamente."
    elif resposta == "Ingestão suspeita com sintomas moderados (náusea, tontura)":
        return "laranja", "Pode ser um quadro moderado de intoxicação. Monitorar e buscar orientação médica."
    elif resposta == "Ingestão leve com sintomas leves (enjoo leve, dor de barriga)":
        return "amarelo", "Sintomas leves e transitórios. Mantenha hidratação e observação."
    else:
        return "verde", "Sem sinais de intoxicação relevante. Continue monitorando."

def opcoes_dor_pescoco():
    return [
        "Dor intensa com febre, vômito ou confusão",
        "Rigidez importante com dor de cabeça forte",
        "Dor moderada após esforço físico ou posição ruim",
        "Dor leve e localizada, sem outros sintomas"
    ]

def classificar_dor_pescoco(resposta):
    if resposta == "Dor intensa com febre, vômito ou confusão":
        return "vermelho", "Pode ser meningite ou outra condição grave. Procure ajuda médica imediatamente."
    elif resposta == "Rigidez importante com dor de cabeça forte":
        return "laranja", "Sinais que merecem avaliação médica. Pode haver comprometimento neurológico."
    elif resposta == "Dor moderada após esforço físico ou posição ruim":
        return "amarelo", "Geralmente de origem muscular. Repouso e analgésico podem ser suficientes."
    else:
        return "verde", "Dor leve e localizada. Monitorar apenas."

def opcoes_alteracao_visao():
    return [
        "Perda súbita da visão ou visão muito turva de um lado",
        "Visão dupla ou embaçada com dor de cabeça ou náusea",
        "Leve embaçamento ou dificuldade temporária pra focar",
        "Cansaço visual leve, sem perda ou dor"
    ]

def classificar_alteracao_visao(resposta):
    if resposta == "Perda súbita da visão ou visão muito turva de um lado":
        return "vermelho", "Emergência oftalmológica. Atendimento imediato é necessário."
    elif resposta == "Visão dupla ou embaçada com dor de cabeça ou náusea":
        return "laranja", "Pode indicar pressão elevada ou problema neurológico. Avaliação médica recomendada."
    elif resposta == "Leve embaçamento ou dificuldade temporária pra focar":
        return "amarelo", "Pode ser fadiga ocular ou alteração passageira. Observe evolução."
    else:
        return "verde", "Sem alterações visuais relevantes."

def opcoes_engasgo():
    return [
        "Engasgo com tosse ineficaz, lábios roxos ou dificuldade extrema",
        "Tosse persistente com respiração ofegante",
        "Tossiu, mas respira normalmente agora",
        "Episódio leve e isolado, sem sinais atuais"
    ]

def classificar_engasgo(resposta):
    if resposta == "Engasgo com tosse ineficaz, lábios roxos ou dificuldade extrema":
        return "vermelho", "Sinais de obstrução grave das vias aéreas. Proceda com manobra de desengasgo e procure socorro imediato."
    elif resposta == "Tosse persistente com respiração ofegante":
        return "laranja", "Desconforto respiratório significativo. Requer observação e possível avaliação médica."
    elif resposta == "Tossiu, mas respira normalmente agora":
        return "amarelo", "Situação controlada, mas continue observando o padrão respiratório."
    else:
        return "verde", "Episódio leve e isolado. Sem sinais de risco."

def opcoes_ferimentos_cortes():
    return [
        "Corte profundo com sangramento intenso e exposição de tecidos",
        "Ferida moderada com sangramento que demora a parar",
        "Ferida pequena, mas com sinais de infecção (pus, vermelhidão)",
        "Corte leve, limpo e controlado"
    ]

def classificar_ferimentos_cortes(opcao):
    if opcao == "Corte profundo com sangramento intenso e exposição de tecidos":
        return "vermelho", "Ferimento grave com risco de hemorragia ou infecção. Procure socorro imediato."
    elif opcao == "Ferida moderada com sangramento que demora a parar":
        return "laranja", "Requer cuidados para evitar infecção e estancar sangramento."
    elif opcao == "Ferida pequena, mas com sinais de infecção (pus, vermelhidão)":
        return "amarelo", "Monitorar e higienizar. Pode necessitar de pomada ou consulta médica."
    else:
        return "verde", "Ferimento leve e bem controlado. Higienize e proteja."

def opcoes_corpo_estranho_sentidos():
    return [
        "Dor intensa ou secreção com febre",
        "Desconforto moderado e persistente",
        "Leve irritação, sem dor ou sinais de infecção",
        "Presença confirmada, mas sem sintomas"
    ]

def classificar_corpo_estranho_sentidos(opcao):
    if opcao == "Dor intensa ou secreção com febre":
        return "vermelho", "Pode haver infecção ou lesão interna. Requer atendimento médico."
    elif opcao == "Desconforto moderado e persistente":
        return "laranja", "Situação incômoda. Pode precisar de remoção médica do corpo estranho."
    elif opcao == "Leve irritação, sem dor ou sinais de infecção":
        return "amarelo", "Quadro leve, mas continue observando se evolui."
    else:
        return "verde", "Sem sintomas preocupantes."

def opcoes_dor_ao_urinar():
    return [
        "Dor intensa com sangue na urina ou febre",
        "Ardência moderada com urgência e desconforto abdominal",
        "Ardência leve ou aumento de frequência urinária",
        "Leve desconforto, sem outros sintomas"
    ]

def classificar_dor_ao_urinar(opcao):
    if opcao == "Dor intensa com sangue na urina ou febre":
        return "vermelho", "Indício de infecção urinária grave ou cálculo renal. Atendimento médico necessário."
    elif opcao == "Ardência moderada com urgência e desconforto abdominal":
        return "laranja", "Sinais de infecção em estágio inicial. Procure avaliação médica."
    elif opcao == "Ardência leve ou aumento de frequência urinária":
        return "amarelo", "Provável infecção leve. Monitorar e aumentar hidratação."
    else:
        return "verde", "Sem sinais relevantes no momento."

def opcoes_ansiedade_agitacao():
    return [
        "Agitação extrema com risco de autoagressão ou agressividade",
        "Crise intensa com falta de ar, tremores ou choro incontrolável",
        "Ansiedade moderada com pensamentos acelerados",
        "Sensação leve de nervosismo ou tensão"
    ]

def classificar_ansiedade_agitacao(opcao):
    if opcao == "Agitação extrema com risco de autoagressão ou agressividade":
        return "vermelho", "Crise severa. É necessário socorro imediato ou suporte especializado."
    elif opcao == "Crise intensa com falta de ar, tremores ou choro incontrolável":
        return "laranja", "Crise significativa de ansiedade. Requer acolhimento e possível intervenção profissional."
    elif opcao == "Ansiedade moderada com pensamentos acelerados":
        return "amarelo", "Quadro leve a moderado. Técnicas de respiração e apoio emocional podem ajudar."
    else:
        return "verde", "Estado emocional estável. Sem sinais de alerta."

def opcoes_diarreia():
    return [
        "Diarreia intensa com sangue ou sinais de desidratação",
        "Várias evacuações líquidas com febre ou dor abdominal",
        "Episódio isolado de diarreia sem outros sintomas",
        "Fezes amolecidas por curto período"
    ]

def classificar_diarreia(opcao):
    if opcao == "Diarreia intensa com sangue ou sinais de desidratação":
        return "vermelho", "Quadro grave de diarreia com risco de desidratação severa. Procure atendimento."
    elif opcao == "Várias evacuações líquidas com febre ou dor abdominal":
        return "laranja", "Pode indicar infecção intestinal. Requer hidratação e avaliação médica."
    elif opcao == "Episódio isolado de diarreia sem outros sintomas":
        return "amarelo", "Monitorar evolução. Mantenha dieta leve e hidratação."
    else:
        return "verde", "Alteração leve e autolimitada."

def opcoes_sensacao_desmaio():
    return [
        "Fraqueza súbita com visão turva e suor frio",
        "Tontura persistente com sensação de queda iminente",
        "Sensação leve de cabeça vazia ou instabilidade",
        "Episódio pontual que já passou"
    ]

def classificar_sensacao_desmaio(opcao):
    if opcao == "Fraqueza súbita com visão turva e suor frio":
        return "vermelho", "Pode indicar queda de pressão ou outra emergência clínica. Requer avaliação imediata."
    elif opcao == "Tontura persistente com sensação de queda iminente":
        return "laranja", "Situação moderada. Atenção à hidratação e possíveis gatilhos."
    elif opcao == "Sensação leve de cabeça vazia ou instabilidade":
        return "amarelo", "Leve desconforto. Observe se há repetição dos sintomas."
    else:
        return "verde", "Sintomas resolvidos. Situação estável."

def opcoes_palpitacoes():
    return [
        "Batimentos acelerados com dor no peito ou falta de ar",
        "Palpitações intensas e persistentes, sem outros sintomas",
        "Batimentos rápidos ocasionais, mas sem desconforto",
        "Sensação leve que passa rapidamente"
    ]

def classificar_palpitacoes(opcao):
    if opcao == "Batimentos acelerados com dor no peito ou falta de ar":
        return "vermelho", "Pode ser arritmia cardíaca ou emergência cardiovascular. Procure atendimento imediato."
    elif opcao == "Palpitações intensas e persistentes, sem outros sintomas":
        return "laranja", "Requer avaliação para descartar causas cardíacas."
    elif opcao == "Batimentos rápidos ocasionais, mas sem desconforto":
        return "amarelo", "Normalmente benigno. Reduza cafeína e estresse."
    else:
        return "verde", "Sem sinais relevantes."

def opcoes_inchaco_olhos_face():
    return [
        "Inchaço com dor intensa, febre ou fechamento dos olhos",
        "Inchaço moderado com vermelhidão e coceira",
        "Inchaço leve sem dor, após alergia ou trauma",
        "Inchaço pequeno e passageiro"
    ]


def classificar_inchaco_olhos_face(opcao):
    if opcao == "Inchaço com dor intensa, febre ou fechamento dos olhos":
        return "vermelho", "Risco de infecção ou reação alérgica grave. Atendimento imediato recomendado."
    elif opcao == "Inchaço moderado com vermelhidão e coceira":
        return "laranja", "Pode ser conjuntivite ou alergia. Requer observação e cuidados básicos."
    elif opcao == "Inchaço leve sem dor, após alergia ou trauma":
        return "amarelo", "Situação leve e autolimitada. Mantenha compressas frias e observação."
    else:
        return "verde", "Sem alterações relevantes."

def opcoes_sangramento_nasal():
    return [
        "Sangramento intenso que não para com pressão direta",
        "Sangramento moderado que reaparece durante o dia",
        "Sangramento leve após esforço ou espirro",
        "Sangramento isolado e já controlado"
    ]

def classificar_sangramento_nasal(opcao):
    if opcao == "Sangramento intenso que não para com pressão direta":
        return "vermelho", "Necessita avaliação médica para controle do sangramento."
    elif opcao == "Sangramento moderado que reaparece durante o dia":
        return "laranja", "Pode indicar fragilidade capilar ou irritação nasal. Requer acompanhamento."
    elif opcao == "Sangramento leve após esforço ou espirro":
        return "amarelo", "Geralmente benigno. Use soro fisiológico e evite coçar o nariz."
    else:
        return "verde", "Episódio resolvido sem necessidade de intervenção."

def opcoes_dor_articulacoes():
    return [
        "Dor súbita com inchaço e dificuldade de movimentar",
        "Dor intensa após trauma ou inflamação visível",
        "Dor moderada que piora com o uso",
        "Dor leve que melhora com repouso"
    ]

def classificar_dor_articulacoes(opcao):
    if opcao == "Dor súbita com inchaço e dificuldade de movimentar":
        return "vermelho", "Suspeita de lesão articular grave. Avaliação ortopédica urgente."
    elif opcao == "Dor intensa após trauma ou inflamação visível":
        return "laranja", "Inflamação ou lesão moderada. Pode necessitar de cuidados médicos."
    elif opcao == "Dor moderada que piora com o uso":
        return "amarelo", "Provavelmente sobrecarga. Repouso e gelo podem aliviar."
    else:
        return "verde", "Dor leve e tolerável. Sem sinais de risco."

def opcoes_tosse():
    return [
        "Tosse com sangue ou falta de ar severa",
        "Tosse persistente com febre alta",
        "Tosse seca ou com catarro moderado",
        "Tosse ocasional sem outros sintomas"
    ]

def classificar_tosse(resp):
    if resp == "Tosse com sangue ou falta de ar severa":
        return "vermelho", "Tosse com sinais de gravidade respiratória. Procure pronto atendimento."
    elif resp == "Tosse persistente com febre alta":
        return "laranja", "Pode indicar infecção como pneumonia. Requer avaliação médica."
    elif resp == "Tosse seca ou com catarro moderado":
        return "amarelo", "Quadro viral ou alérgico leve. Monitorar e hidratar."
    else:
        return "verde", "Sem sinais de alarme. Tosse ocasional e leve."

def opcoes_coceira():
    return [
        "Coceira intensa com placas vermelhas e inchaço",
        "Coceira forte que não alivia, atrapalha o sono",
        "Coceira moderada e localizada",
        "Coceira leve, passageira"
    ]

def classificar_coceira(opcao):
    if opcao == "Coceira intensa com placas vermelhas e inchaço":
        return "vermelho", "Reação alérgica intensa ou dermatite grave. Procure atendimento médico urgente."
    elif opcao == "Coceira forte que não alivia, atrapalha o sono":
        return "laranja", "Quadro incômodo e persistente. Avaliação médica é recomendada."
    elif opcao == "Coceira moderada e localizada":
        return "amarelo", "Situação leve a moderada. Hidratantes ou antialérgicos podem ajudar."
    else:
        return "verde", "Coceira leve e passageira. Sem sinais de alerta."

def opcoes_queimacao_peito():
    return [
        "Queimação forte com náusea ou suor frio",
        "Desconforto moderado que piora ao deitar",
        "Ardência leve após comer alimentos pesados",
        "Sensação leve, ocasional, sem outros sintomas"
    ]

def classificar_queimacao_peito(opcao):
    if opcao == "Queimação forte com náusea ou suor frio":
        return "vermelho", "Pode indicar problema cardíaco. Atendimento médico imediato necessário."
    elif opcao == "Desconforto moderado que piora ao deitar":
        return "laranja", "Possível refluxo gástrico. Requer atenção e mudança de hábitos."
    elif opcao == "Ardência leve após comer alimentos pesados":
        return "amarelo", "Refluxo leve. Evite alimentos gordurosos e observe evolução."
    else:
        return "verde", "Sintoma leve e esporádico. Sem risco aparente."

def opcoes_alteracao_fala():
    return [
        "Perda súbita da fala ou fala arrastada",
        "Dificuldade de encontrar palavras ou formar frases",
        "Fala lenta ou confusa, mas consegue se expressar",
        "Leve hesitação, mas sem prejuízo da comunicação"
    ]

def classificar_alteracao_fala(opcao):
    if opcao == "Perda súbita da fala ou fala arrastada":
        return "vermelho", "Sinal de possível AVC. Procure socorro imediato."
    elif opcao == "Dificuldade de encontrar palavras ou formar frases":
        return "laranja", "Alterações neurológicas devem ser investigadas."
    elif opcao == "Fala lenta ou confusa, mas consegue se expressar":
        return "amarelo", "Quadro leve. Monitorar e evitar esforço mental excessivo."
    else:
        return "verde", "Sem alterações importantes da fala."

def opcoes_dor_ouvido():
    return [
        "Dor intensa com febre ou secreção purulenta",
        "Dor forte e contínua, sem melhora com analgésico",
        "Dor leve com coceira ou zumbido",
        "Desconforto discreto que vai e volta"
    ]

def classificar_dor_ouvido(opcao):
    if opcao == "Dor intensa com febre ou secreção purulenta":
        return "vermelho", "Indício de infecção grave. Atendimento médico necessário."
    elif opcao == "Dor forte e contínua, sem melhora com analgésico":
        return "laranja", "Dor persistente pode evoluir. Consulte um profissional."
    elif opcao == "Dor leve com coceira ou zumbido":
        return "amarelo", "Quadro leve, possivelmente alérgico ou infeccioso inicial."
    else:
        return "verde", "Desconforto leve e transitório. Observe evolução."

def opcoes_sensibilidade_luz_som():
    return [
        "Sensibilidade intensa com dor de cabeça e náusea",
        "Incômodo moderado que piora em ambientes claros ou barulhentos",
        "Leve desconforto ao sair no sol ou ouvir sons agudos",
        "Sensação leve e eventual"
    ]

def classificar_sensibilidade_luz_som(resp):
    if resp == "Sensibilidade intensa com dor de cabeça e náusea":
        return "vermelho", "Pode indicar enxaqueca grave ou condição neurológica. Procure avaliação."
    elif resp == "Incômodo moderado que piora em ambientes claros ou barulhentos":
        return "laranja", "Sintomas moderados podem interferir na rotina. Requer observação."
    elif resp == "Leve desconforto ao sair no sol ou ouvir sons agudos":
        return "amarelo", "Reação leve. Use óculos escuros ou evite ambientes ruidosos."
    else:
        return "verde", "Sensibilidade leve. Sem sinais preocupantes."

def opcoes_nausea():
    return [
        "Náusea constante com vômito e mal-estar",
        "Enjoo forte que impede alimentação",
        "Enjoo leve e intermitente",
        "Desconforto passageiro após alimentação"
    ]

def classificar_nausea(resp):
    if resp == "Náusea constante com vômito e mal-estar":
        return "vermelho", "Possível infecção gastrointestinal ou intoxicação. Procure atendimento."
    elif resp == "Enjoo forte que impede alimentação":
        return "laranja", "Pode levar à desidratação. Avaliação médica pode ser necessária."
    elif resp == "Enjoo leve e intermitente":
        return "amarelo", "Sintomas leves. Mantenha hidratação e dieta leve."
    else:
        return "verde", "Sintoma leve e esporádico. Sem risco."

def opcoes_dor_ombro_braco():
    return [
        "Dor irradiando do peito ou com formigamento",
        "Dor intensa com limitação de movimento",
        "Dor moderada após esforço",
        "Dor leve que melhora com repouso"
    ]

def classificar_dor_ombro_braco(resp):
    if resp == "Dor irradiando do peito ou com formigamento":
        return "vermelho", "Possível infarto. Atendimento médico imediato recomendado."
    elif resp == "Dor intensa com limitação de movimento":
        return "laranja", "Pode ser tendinite ou lesão. Requer avaliação ortopédica."
    elif resp == "Dor moderada após esforço":
        return "amarelo", "Situação comum. Repouso e gelo ajudam na recuperação."
    else:
        return "verde", "Dor leve e transitória. Sem preocupação."

def opcoes_alergia_cutanea():
    return [
        "Lesão com inchaço e coceira intensa",
        "Mancha vermelha espalhada com descamação",
        "Irritação leve e localizada",
        "Lesão pequena e assintomática"
    ]

def classificar_alergia_cutanea(resp):
    if resp == "Lesão com inchaço e coceira intensa":
        return "vermelho", "Reação alérgica intensa. Pode evoluir para quadro sistêmico. Procure ajuda médica."
    elif resp == "Mancha vermelha espalhada com descamação":
        return "laranja", "Possível dermatite. Requer hidratação e avaliação médica."
    elif resp == "Irritação leve e localizada":
        return "amarelo", "Sintoma leve. Utilize hidratantes e observe evolução."
    else:
        return "verde", "Lesão assintomática. Sem necessidade de intervenção."

def opcoes_sangramento_gi():
    return [
        "Fezes com sangue vivo ou pretas com mal-estar",
        "Sangue moderado sem dor intensa",
        "Pequena presença de sangue isolada",
        "Observação leve e sem sintomas associados"
    ]

def classificar_sangramento_gi(resp):
    if resp == "Fezes com sangue vivo ou pretas com mal-estar":
        return "vermelho", "Pode indicar hemorragia digestiva. Atendimento imediato é essencial."
    elif resp == "Sangue moderado sem dor intensa":
        return "laranja", "Quadro preocupante. Procure avaliação médica."
    elif resp == "Pequena presença de sangue isolada":
        return "amarelo", "Pode ser fissura anal ou irritação leve. Observe."
    else:
        return "verde", "Sem sinais de alarme. Acompanhe se houver repetição."

def opcoes_corpo_estranho_garganta():
    return [
        "Corpo estranho preso com dificuldade para respirar ou engolir",
        "Desconforto com dor ao engolir",
        "Sensação de algo preso, mas respira normalmente",
        "Episódio leve e já resolvido"
    ]

def classificar_corpo_estranho_garganta(resp):
    if resp == "Corpo estranho preso com dificuldade para respirar ou engolir":
        return "vermelho", "Emergência. Risco de obstrução das vias aéreas. Procure socorro imediatamente."
    elif resp == "Desconforto com dor ao engolir":
        return "laranja", "Pode ser inflamação ou objeto pequeno. Avaliação médica necessária."
    elif resp == "Sensação de algo preso, mas respira normalmente":
        return "amarelo", "Observe. Pode desaparecer sozinho ou exigir remoção simples."
    else:
        return "verde", "Situação resolvida. Sem riscos atuais."

def opcoes_ictericia():
    return [
        "Icterícia intensa com dor abdominal ou vômito",
        "Pele amarelada com febre ou cansaço",
        "Amarelado leve, sem sintomas associados",
        "Coloração discreta e passageira"
    ]

def classificar_ictericia(resp):
    if resp == "Icterícia intensa com dor abdominal ou vômito":
        return "vermelho", "Possível comprometimento hepático grave. Procure atendimento médico."
    elif resp == "Pele amarelada com febre ou cansaço":
        return "laranja", "Icterícia associada a infecção ou disfunção hepática. Necessita avaliação."
    elif resp == "Amarelado leve, sem sintomas associados":
        return "amarelo", "Icterícia leve. Monitorar coloração da pele e olhos."
    else:
        return "verde", "Sem sinais relevantes. Observe se houver evolução."

def opcoes_dificuldade_engolir():
    return [
        "Não consegue engolir líquidos ou saliva",
        "Dor e dificuldade ao engolir sólidos",
        "Leve desconforto para engolir",
        "Sensação passageira ao engolir"
    ]

def classificar_dificuldade_engolir(resp):
    if resp == "Não consegue engolir líquidos ou saliva":
        return "vermelho", "Obstrução ou inflamação grave. Atendimento médico urgente."
    elif resp == "Dor e dificuldade ao engolir sólidos":
        return "laranja", "Pode indicar infecção ou irritação. Requer avaliação médica."
    elif resp == "Leve desconforto para engolir":
        return "amarelo", "Geralmente leve e transitório. Observe evolução."
    else:
        return "verde", "Sem sintomas preocupantes."

def opcoes_tremores():
    return [
        "Tremores com perda de consciência ou força",
        "Movimentos anormais contínuos com dificuldade para parar",
        "Tremores leves em repouso",
        "Episódio isolado e breve"
    ]

def classificar_tremores(resp):
    if resp == "Tremores com perda de consciência ou força":
        return "vermelho", "Sinais neurológicos graves. Procure socorro imediatamente."
    elif resp == "Movimentos anormais contínuos com dificuldade para parar":
        return "laranja", "Pode indicar crise neurológica ou ansiedade severa. Requer avaliação."
    elif resp == "Tremores leves em repouso":
        return "amarelo", "Quadro leve. Monitorar frequência e intensidade."
    else:
        return "verde", "Tremores leves e isolados. Sem sinais de risco."

def opcoes_retencao_urinaria():
    return [
        "Não urina há muitas horas com dor e distensão abdominal",
        "Jato fraco com sensação de bexiga cheia",
        "Urina com dificuldade, mas consegue aliviar",
        "Pequena alteração, mas sem desconforto"
    ]

def classificar_retencao_urinaria(resp):
    if resp == "Não urina há muitas horas com dor e distensão abdominal":
        return "vermelho", "Retenção urinária grave. Risco de complicações renais. Atendimento imediato necessário."
    elif resp == "Jato fraco com sensação de bexiga cheia":
        return "laranja", "Pode ser obstrução parcial. Avaliação urológica recomendada."
    elif resp == "Urina com dificuldade, mas consegue aliviar":
        return "amarelo", "Situação leve. Acompanhar se houver piora."
    else:
        return "verde", "Sem alterações relevantes."
            
def opcoes_infeccao_ferida():
    return [
        "Ferida com pus, inchaço, dor e febre",
        "Vermelhidão intensa e secreção local",
        "Leve vermelhidão sem dor",
        "Cicatrização normal com alteração mínima"
    ]

def classificar_infeccao_ferida(resp):
    if resp == "Ferida com pus, inchaço, dor e febre":
        return "vermelho", "Infecção ativa e sistêmica. Atendimento médico urgente."
    elif resp == "Vermelhidão intensa e secreção local":
        return "laranja", "Infecção localizada. Necessita cuidados e possível antibiótico."
    elif resp == "Leve vermelhidão sem dor":
        return "amarelo", "Irritação leve. Higienização adequada pode resolver."
    else:
        return "verde", "Ferida em boa evolução. Sem sinais de infecção."

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

# Mapa atualizado de sintomas
mapa_sintomas = {
    "Dor na perna e dificuladade para caminhar": (opcoes_dor_perna_caminhar, classificar_dor_perna_caminhar),
    "Sinais de intoxicação ou envenenamento": (opcoes_intoxicacao, classificar_intoxicacao),
    "Dores no pescoço ou rigidez na nuca": (opcoes_dor_pescoco, classificar_dor_pescoco),
    "Alterações visuais súbitas": (opcoes_alteracao_visao, classificar_alteracao_visao),
    "Engasgo ou obstrução das vias aéreas": (opcoes_engasgo, classificar_engasgo),
    "Ferimentos ou cortes com objetos": (opcoes_ferimentos_cortes, classificar_ferimentos_cortes),
    "Corpo estranho nos olhos, ouvidos ou nariz": (opcoes_corpo_estranho_sentidos, classificar_corpo_estranho_sentidos),
    "Alterações urinárias": (opcoes_alteracoes_urinarias, classificar_alteracoes_urinarias),
    "Ansiedade ou agitação intensa": (opcoes_ansiedade_agitacao, classificar_ansiedade_agitacao),
    "Diarreia": (opcoes_diarreia, classificar_diarreia),
    "Sensação de desmaio": (opcoes_sensacao_desmaio, classificar_sensacao_desmaio),
    "Palpitações ou batimentos cardíacos acelerados": (opcoes_palpitacoes, classificar_palpitacoes),
    "Inchaço nos olhos ou face": (opcoes_inchaco_olhos_face, classificar_inchaco_olhos_face),
    "Sangramento nasal": (opcoes_sangramento_nasal, classificar_sangramento_nasal),
    "Dor nas articulações": (opcoes_dor_articulacoes, classificar_dor_articulacoes),
    "Coceira na pele": (opcoes_coceira, classificar_coceira),
    "Queimação no peito": (opcoes_queimacao_peito, classificar_queimacao_peito),
    "Alterações na fala": (opcoes_alteracao_fala, classificar_alteracao_fala),
    "Dor no ouvido": (opcoes_dor_ouvido, classificar_dor_ouvido),
    "Sensibilidade à luz ou som": (opcoes_sensibilidade_luz_som, classificar_sensibilidade_luz_som),
    "Náusea ou enjoo": (opcoes_nausea, classificar_nausea),
    "Dor no ombro ou braço": (opcoes_dor_ombro_braco, classificar_dor_ombro_braco),
    "Reação alérgica": (opcoes_reacao_alergica, classificar_reacao_alergica),
    "Sangramento gastrointestinal": (opcoes_sangramento_gi, classificar_sangramento_gi),
    "Corpo estranho na garganta": (opcoes_corpo_estranho_garganta, classificar_corpo_estranho_garganta),
    "Icterícia (pele ou olhos amarelados)": (opcoes_ictericia, classificar_ictericia),
    "Dificuldade para engolir": (opcoes_dificuldade_engolir, classificar_dificuldade_engolir),
    "Tremores ou movimentos involuntários": (opcoes_tremores, classificar_tremores),
    "Retenção urinária": (opcoes_retencao_urinaria, classificar_retencao_urinaria),
    "Infecção em ferida": (opcoes_infeccao_ferida, classificar_infeccao_ferida),
    "Desmaio ou tontura": (opcoes_desmaio_tontura, classificar_desmaio_tontura),
    "Dor nas costas": (opcoes_dor_nas_costas, classificar_dor_nas_costas),
    "Dificuldade respiratória": (opcoes_dificuldade_respiratoria, classificar_dificuldade_respiratoria),
    "Lesões na pele": (opcoes_lesoes_na_pele, classificar_lesoes_na_pele),
    "Dor ou olho vermelho": (opcoes_dor_ou_olho_vermelho, classificar_dor_ou_olho_vermelho),
    "Formigamento ou perda de força": (opcoes_formigamento_perda_forca, classificar_formigamento_perda_forca),
    "Sangramento vaginal": (opcoes_sangramento_vaginal, classificar_sangramento_vaginal),
    "Dor ou dificulade ao urinar": (opcoes_dor_ao_urinar, classificar_dor_ao_urinar),
    "Inchaço incomum": (opcoes_inchaco, classificar_inchaco),
    "Comportamento estranho à normalidade": (opcoes_comportamento_estranho, classificar_comportamento_estranho),
    "Sangramento ativo": (opcoes_sangramento_ativo, classificar_sangramento_ativo),
    "Alergia cutânea": (opcoes_alergia_cutanea, classificar_alergia_cutanea),
    }
mapa_sintomas = dict(sorted(mapa_sintomas.items()))

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
# Fluxograma: Dor testicular (conservador)
FLUXOS[normalizar("Dor testicular")] = {
    "label": "Dor testicular",
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
# Fluxograma: Dor testicular (conservador)
FLUXOS[normalizar("Dor testicular")] = {
    "label": "Dor testicular",
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
                "Dor ao urinar (ardor)": 0.7,
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
FLUXOS[normalizar("Trauma craniano")] = {
    "label": "Trauma craniano",
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

# Fluxograma: Manchas na pele
FLUXOS[normalizar("Manchas na pele")] = {
    "label": "Manchas na pele",
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
# Fluxograma: Dor odontológica
FLUXOS[normalizar("Dor odontológica")] = {
    "label": "Dor odontológica",
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
# Fluxograma: Alteração auditiva
FLUXOS[normalizar("Alteração auditiva")] = {
    "label": "Alteração auditiva",
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
                "Dor de ouvido importante": 0.8
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
FLUXOS[normalizar("Movimentos fetais")] = {
    "label": "Movimentos fetais",
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
                "Manchas na pele": 1.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Febre alta persistente com prostração ou recusa alimentar"}, "min_cor": "vermelho"},
        {"se": {"sinais_associados": ["Respiração acelerada/dificuldade para respirar", "Manchas na pele"]}, "min_cor": "vermelho"},
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
# CONVULSÕES
# ===============================
FLUXOS[normalizar("Convulsões")] = {
    "label": "Convulsões",
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
    sintomas_disponiveis = sorted(set(list(mapa_sintomas.keys()) + labels_fluxos()))

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

    # Usamos um FORM: nada calcula/mostra até clicar "Ver resultado"
    with st.form("form_detalhamento"):
        # Renderização de perguntas por sintoma
        for sintoma in st.session_state.sintomas_escolhidos:
            st.markdown(f"### {sintoma}")
            if eh_fluxo(sintoma):
                # Garante estrutura para este fluxo
                chave = normalizar(sintoma)
                if chave not in st.session_state["fluxo_respostas"]:
                    st.session_state["fluxo_respostas"][chave] = {}
                # Renderiza perguntas do fluxo
                coletar_respostas_fluxo(sintoma)
            else:
                # Fallback antigo (mapa_sintomas)
                func_opcoes, _ = mapa_sintomas[sintoma]
                opcoes = func_opcoes()
                escolha = st.radio(f"{sintoma}:", opcoes, key=f"opcao_{sintoma}")
                st.session_state["respostas_usuario"][sintoma] = escolha

        enviado = st.form_submit_button("Ver resultado")

    # Só processa e exibe resultados SE o botão foi clicado
    if enviado:
        st.markdown("---")
        cores_geradas = []

        for sintoma in st.session_state.sintomas_escolhidos:
            if eh_fluxo(sintoma):
                chave = normalizar(sintoma)
                cor, score = pontuar_fluxo(sintoma, st.session_state["fluxo_respostas"][chave])
                motivo = f"Pontuação composta: {score:.1f} (fluxograma multi-perguntas)."
            else:
                _, func_classificacao = mapa_sintomas[sintoma]
                escolha = st.session_state["respostas_usuario"][sintoma]
                cor, motivo = func_classificacao(escolha)

            cores_geradas.append(cor)
            st.markdown(f"### {sintoma}")
            st.markdown(f"Motivo: {motivo}")
            st.markdown("---")

        # Combinação de cores (tua lógica)
        cor_final = classificar_combinacao(
            sintomas=[s.lower() for s in st.session_state.sintomas_escolhidos],
            cores=cores_geradas
        )

        # --- AJUSTE CONSERVADOR POR FATORES (idade/gravidez e duplicidade de sistema) ---
        gravidez = str(st.session_state.get("gravida", "")).strip().lower() in ["sim", "true", "1"]
        idade_paciente = st.session_state.get("idade")

        ajuste_niveis = calcular_ajuste_por_fatores_conservador(
            sintomas_escolhidos=st.session_state.sintomas_escolhidos,
            cores_individuais=cores_geradas,
            sintoma_para_sistema=sintoma_para_sistema,
            idade=idade_paciente,
            gravida=gravidez
        )

        # Aplica, no máximo, +1 nível
        if ajuste_niveis >= 1:
            cor_final = aumentar_cor_em_1_nivel(cor_final)

        st.success(f"Gravidade estimada: {cor_final.upper()}")

        st.markdown("---")
        st.subheader("📘 Legenda de Gravidade")
        st.markdown("""
- 🔴 **VERMELHO:** Situação crítica. Procure atendimento médico imediatamente.
- 🟠 **LARANJA:** Caso urgente. Necessita avaliação rápida em unidade de saúde.
- 🟡 **AMARELO:** Gravidade moderada. Requer atenção, mas pode aguardar avaliação.
- 🟢 **VERDE:** Baixa gravidade. Pode observar os sintomas ou procurar atendimento não urgente.
""")

