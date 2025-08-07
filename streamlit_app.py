import streamlit as st
from datetime import datetime
import pandas as pd
import unicodedata
import time

def normalizar(texto):
    """Remove acentos e coloca em minúsculas para facilitar comparações."""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

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
        "desmaio ou tontura", "alterações na fala", "alterações visuais súbitas", "tremores ou movimentos involuntários"
    ],
    "gastrointestinal": [
        "náusea ou enjoo", "diarreia em criança", "sangramento gastrointestinal",
        "vômito em criança", "dor abdominal", "gases", "diarreia"
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
        "alergia cutânea", "reação alérgica", "lesões na pele", "manchas na pele", "coceira na pele"
    ],
    "oftalmologico": [
        "alterações visuais súbitas", "dor ou olho vermelho", "inchaço nos olhos ou face", "corpo estranho nos olhos, ouvidos ou nariz"
    ],
    "otorrino": [
        "dor no ouvido", "coriza e espirros", "sangramento nasal", "alteração auditiva", "dificuldade pra engolir"
    ],
    "obstetrico": [
        "dor durante a gravidez", "trabalho de parto", "redução dos movimentos fetais"
    ],
    "pediatrico": [
        "febre lactente", "icterícia neonatal", "queda em criança", "choro persistente"
    ],
    "hematologico": [
        "sangramento ativo", "sangramento gastrointestinal", "sangramento nasal", "sangramento retal"
    ],
    "psiquiatrico": [
        "ansiedade ou agitação intensas", "comportamento estranho à normalidade"
    ],
    "endocrino": [
        "hipoglicemia", "hiperglicemia", "hipotensão", "temperatura baixa"
    ],
    "hepatico": [
        "icterícia", "icterícia neonatal"
    ],
    "infeccioso": [
        "febre", "infecção em ferida", "sinais de intoxicação ou envenenamento", "inchaço dos linfonodos"
    ],
    "reprodutor masculino": [
        "nódulo testicular", "dor nos testículos", "sangue no sêmen"
    ],
    "mamario": [
        "nódulo mamário", "secreção mamilar (fora da amamentação)"
    ],
    "ginecologico": [
        "sangramento vaginal"
    ]
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
    refinados = set(condicoes_brutas)

    if idade is not None:
        if idade < 5:
            refinados.update(["Infeccioso", "Respiratório", "Neurológico", "Musculoesquelético", "Otorrino", "Gastrointestinal"])
        elif idade > 60:
            refinados.update(["Cardíaco", "Neurológico", "Musculoesquelético", "Endócrino", "Infeccioso", "Hepático", "Oftalmológico", "Cutâneo", "Urinário"])
        elif idade < 14 and imc_class == "Desnutrido":
            refinados.add("Neurológico")

    if imc_class == "Obeso":
        refinados.update(["Cardíaco", "Respiratório", "Hematológico", "Psiquiátrico", "Endócrino", "Musculoesquelético"])
    elif imc_class == "Desnutrido":
        refinados.update(["Infeccioso", "Hematológico", "Gastrointestinal", "Musculoesquelético", "Neurológico", "Psiquiátrico"])

    if gravida == "Sim":
        refinados.update(["Hematológico", "Endócrino", "Mamário", "Infeccioso", "Otorrino", "Musculoesquelético, Ginecológico"])

        if idade is not None and idade < 16:
            refinados.update(["Cardíaco", "Neurológico", "Endócrino", "Obstétrico", "Psiquiátrico", "Mamário", "Musculoesquelético, Ginecológico"])


    return list(refinados)

def sistemas_afetados_secundariamente(grupo_primario):
    tabela = {
        "Cardíaco": ["Respiratório", "Hematológico", "Urinário", "Neurológico"],
        "Respiratório": ["Cardíaco", "Otorrino", "Neurológico"],
        "Neurológico": ["Psiquiátrico", "Musculoesquelético", "Urinário", "Gastrointestinal", "Respiratório", "Cardíaco"],
        "Gastrointestinal": ["Hepático", "Hematológico", "Urinário"],
        "Urinário": ["Cardíaco", "Endócrino"],
        "Otorrino": ["Respiratório"],
        "Hematológico": ["Cardíaco", "Endócrino", "Hepático", "Urinário"],
        "Psiquiátrico": ["Neurológico"],
        "Endócrino": ["Cardíaco", "Hepático", "Hematológico"],
        "Hepático": ["Gastrointestinal", "Hematológico"],
        "Autoimune": ["Cutâneo", "Hematológico", "Urinário", "Neurológico", "Musculoesquelético", "Hepático", "Psiquiátrico"],
        "Diabetes": ["Neurológico", "Oftalmológico", "Urinário", "Cardíaco", "Cutâneo", "Hematológico"],
        "Reprodutor masculino": ["Reprodutor masculino"],
        "Mamário": ["Mamário"],
        "Pediátrico": ["Pediátrico"],
        "Obstétrico": ["Obstétrico"],
        "Cutâneo": ["Cutâneo"],
        "Oftalmológico": ["Oftalmológico"],
        "Ginecológico": ["Ginecológico"]
    }
    return tabela.get(grupo_primario, [])

def verificar_se_deve_subir_cor(sintomas_escolhidos, sistemas_afetados, sintoma_para_sistema):
    sintomas_norm = [normalizar(s) for s in sintomas_escolhidos]
    sistemas_norm = [normalizar(s) for s in sistemas_afetados]

    for sintoma in sintomas_norm:
        sistema = sintoma_para_sistema.get(sintoma)
        if sistema and normalizar(sistema) in sistemas_norm:
            return True
    return False

def classificar_combinacao(sintomas, cores):
    pesos = {"verde": 0.5, "amarelo": 1.75, "laranja": 5.5, "vermelho": 8}
    total = sum(pesos.get(cor, 0) for cor in cores)

    if any(cor == "vermelho" for cor in cores):
        return "vermelho"
    # Regra especial: único sintoma e ele é laranja
    if len(cores) == 1 and cores[0] == "laranja":
        return "laranja"
    elif total >= 8:
        return "vermelho"
    elif total >= 5.5:
        return "laranja"
    elif total >= 1.75:
        return "amarelo"
    else:
        return "verde"

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
            "Inchaço acompanhado de febre ou perda de peso": "Os gânglios estão grandes e a pessoa tem febre ou emagrece sem explicação.",
            "Inchaço doloroso ou inflamado": "Dói ao tocar e pode estar vermelho ou quente.",
            "Inchaço perceptível, mas sem outros sintomas": "Dá pra sentir os caroços, mas a pessoa está bem.",
            "Inchaço pequeno e isolado, sem dor": "Só um gânglio inchado, sem dor ou outros sintomas."
        }
    },

"Nódulo na mama": {
    "definicao": "Presença de massa ou caroço na mama, que pode ser benigno ou sinal de câncer.",
    "popular": "Caroço no seio que pode doer ou crescer, às vezes sai líquido.",
    "clinico": "Nódulo mamário",
    "termos": {
        "Nódulo crescente ou com secreção": "O caroço está aumentando ou sai líquido do seio.",
        "Nódulo duro, fixo ou irregular": "O caroço não se move e tem formato estranho.",
        "Nódulo doloroso, mas recente": "O caroço dói, mas apareceu há pouco tempo.",
        "Pequeno nódulo móvel, sem dor": "Tem um caroço pequeno que se move ao tocar e não dói."
        }
    },

"Nódulo testicular": {
    "definicao": "Presença de caroço ou massa em um dos testículos, podendo ser indolor e progressivo.",
    "popular": "Caroço no saco, geralmente sem dor, que pode crescer com o tempo.",
    "clinico": "Massa testicular",
    "termos": {
        "Nódulo firme e indolor, perceptível há dias": "Caroço que não dói e está lá há alguns dias.",
        "Nódulo doloroso ou com inchaço": "O testículo dói ou está inchado onde apareceu o caroço.",
        "Mudança recente no tamanho do testículo": "Um dos testículos aumentou de tamanho de repente.",
        "Sensação de caroço pequeno e móvel": "Caroço que se move ao tocar e é pequeno."
        }
    },

"Dor nos testículos": {
    "definicao": "Dor localizada em um ou ambos os testículos, podendo ser sinal de urgência médica.",
    "popular": "Dor nas bolas, que pode ser leve ou muito forte, às vezes de repente.",
    "clinico": "Orquialgia",
    "termos": {
        "Dor intensa e súbita em um dos testículos": "A dor começou de repente e é muito forte em um lado.",
        "Dor moderada com inchaço": "Está doendo e o testículo ficou inchado.",
        "Desconforto leve ao tocar": "Sente dorzinha leve só quando encosta.",
        "Dor leve que desapareceu": "Já teve dor, mas ela passou sozinha."
        }
    },

"Secreção mamilar (fora da amamentação)": {
    "definicao": "Saída de líquido pelo mamilo quando a pessoa não está amamentando.",
    "popular": "Sai leite ou outro líquido do peito mesmo sem estar grávida ou amamentando.",
    "clinico": "Galactorreia / secreção mamilar anormal",
    "termos": {
        "Secreção com sangue ou espontânea": "Sai sangue ou sai sozinho, sem apertar.",
        "Secreção unilateral e persistente": "Só sai de um lado e continua saindo com o tempo.",
        "Saída de secreção ao apertar o mamilo": "Sai líquido só quando aperta o bico do peito.",
        "Secreção ocasional, sem outros sintomas": "Saiu líquido uma vez, mas sem dor ou outro sinal."
        }
    },

"Sangue no sêmen": {
    "definicao": "Presença de sangue visível no esperma, podendo ter várias causas.",
    "popular": "Esperma sai com sangue, cor rosa ou marrom.",
    "clinico": "Hemospermia",
    "termos": {
        "Presença frequente de sangue no sêmen": "Aparece sangue quase sempre na hora de ejacular.",
        "Sangue apareceu após dor ou trauma": "Teve pancada ou dor e depois saiu sangue no sêmen.",
        "Pequena quantidade única, sem dor": "Saiu um pouco de sangue uma vez, sem sentir dor.",
        "Aparência alterada, mas sem sangue visível": "O esperma parece estranho, mas não tem sangue aparente."
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
        "Alteração de comportamento": "A criança ficou quieta demais ou agitada demais depois da queda.",
        "Hematoma leve": "Roxinho ou galo pequeno, que aparece depois da batida."
    }
},

"Vômito em criança": {
    "definicao": "Expulsão do conteúdo do estômago pela boca, podendo ocorrer em jato e várias vezes.",
    "popular": "Quando a criança vomita com força, várias vezes, e parece estar desidratando.",
    "clinico": "Vômitos persistentes em pediatria",
    "termos": {
        "Vômito em jato frequente com sinais de desidratação": "Vômito forte que sai com pressão, junto com boca seca, moleza ou choro sem lágrima."
    }
},

"Diarreia em criança": {
    "definicao": "Evacuações frequentes e líquidas, que podem causar desidratação.",
    "popular": "Quando a criança faz cocô mole várias vezes ao dia e começa a mostrar sinais de que está desidratada.",
    "clinico": "Diarreia aguda pediátrica",
    "termos": {
        "Sinais de desidratação": "Choro sem lágrima, boca seca, moleza, fralda seca por muito tempo."
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
        "Trauma grave": "Batida forte, com risco de lesão interna ou fratura.",
        "Inconsciência": "A pessoa desmaiou ou não responde.",
        "Dor local": "Dor só no lugar onde bateu, mas sem outros sintomas."
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
        "Convulsão ativa": "A crise está acontecendo naquele momento.",
        "Tremores leves": "Movimentos involuntários menores, sem queda ou rigidez.",
        "Epilepsia": "Doença que causa convulsões repetidas com histórico médico."
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
        "Grave": "A sensação é tão forte que a pessoa mal consegue falar ou se mover.",
        "Lábios roxos": "Sinal de pouco oxigênio, mostrando que o problema é sério."
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
        "Palidez extrema": "Pele muito branca, parecendo sem sangue.",
        "Pressão baixa": "Medição da pressão abaixo de 90/60 mmHg."
    }
},

"Hipoglicemia": {
    "definicao": "Queda dos níveis de açúcar no sangue, podendo causar sintomas neurológicos e físicos.",
    "popular": "Quando a glicose baixa demais, causando tremedeira, fome de repente, suor e até desmaio.",
    "clinico": "Hipoglicemia",
    "termos": {
        "Sudorese intensa": "Suor exagerado, mesmo sem calor ou esforço.",
        "Fome súbita": "Sensação repentina de precisar comer urgente.",
        "Tremores": "Mãos ou corpo tremendo involuntariamente."
    }
},

"Hiperglicemia": {
    "definicao": "Excesso de glicose no sangue, comum em pessoas com diabetes descompensado.",
    "popular": "Quando o açúcar do sangue está alto e a pessoa sente muita sede, enjoo e mal-estar.",
    "clinico": "Hiperglicemia",
    "termos": {
        "Sede intensa": "Necessidade de beber muita água o tempo todo.",
        "Mal-estar com enjoo": "Sensação ruim geral acompanhada de vontade de vomitar."
    }
},

"Temperatura baixa": {
    "definicao": "Redução anormal da temperatura corporal, conhecida como hipotermia.",
    "popular": "Quando o corpo esfria demais e a pessoa fica com frio, tremendo e com mãos e pés gelados.",
    "clinico": "Hipotermia",
    "termos": {
        "Extremidades frias": "Mãos e pés muito gelados ao toque.",
        "Calafrios": "Tremores causados pelo frio intenso.",
        "Pele fria": "Pele gelada, mesmo em ambiente normal."
    }
},

"Dor durante a gravidez": {
    "definicao": "Desconforto abdominal ou pélvico em gestantes, que pode ou não indicar complicações.",
    "popular": "Quando a grávida sente dor no pé da barriga, com ou sem contrações, podendo indicar algo grave.",
    "clinico": "Dor gestacional",
    "termos": {
        "Perda de líquido": "Quando escorre água pela vagina, como se estivesse vazando urina ou rompendo a bolsa."
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
        "Mordida profunda": "Ferida que atravessa todas as camadas da pele.",
        "Suspeita de raiva": "Quando a mordida é de animal desconhecido ou não vacinado.",
        "Mordida superficial": "Arranhão ou machucado leve, só na parte de cima da pele."
    }
},

"Queimadura": {
    "definicao": "Lesão na pele ou tecidos por calor, produtos químicos, eletricidade ou radiação.",
    "popular": "Quando encosta em algo quente ou químico e a pele queima. Pode ficar vermelha, fazer bolhas ou queimar profundamente.",
    "clinico": "Queimadura térmica ou química",
    "termos": {
        "Queimadura extensa": "Quando pega uma área grande do corpo.",
        "Bolhas": "Quando a pele levanta com líquido dentro, sinal de queimadura mais profunda."
    }
},

"Ferida não-traumática": {
    "definicao": "Ferida que surge sem pancada ou corte, geralmente por infecção, circulação ruim ou doenças de pele.",
    "popular": "Machucado que aparece sozinho, sem cair ou se bater. Pode ter pus, doer, cheirar mal ou piorar com o tempo.",
    "clinico": "Úlcera cutânea ou lesão espontânea",
    "termos": {
        "Secreção": "Líquido ou pus que sai da ferida.",
        "Mal cheiro": "Cheiro forte vindo da ferida, sinal de infecção."
    }
},

"Gases": {
    "definicao": "Acúmulo de ar no intestino, provocando distensão e desconforto.",
    "popular": "Barriga estufada, soltando pum o tempo todo ou barulho alto no intestino. Às vezes não melhora nem depois de soltar.",
    "clinico": "Flatulência ou distensão abdominal",
    "termos": {
        "Flatulência": "Pum em excesso.",
        "Barulho intestinal alto": "Ruídos fortes na barriga.",
        "Sem alívio": "Mesmo soltando gases, a dor ou desconforto continua."
    }
},

"Sangramento retal": {
    "definicao": "Presença de sangue saindo pelo ânus, geralmente visível nas fezes ou no papel higiênico.",
    "popular": "Quando sai sangue pelo ânus ao evacuar. Pode ser pouco ou muito, e o sangue geralmente é vermelho vivo.",
    "clinico": "Rectorragia",
    "termos": {
        "Vermelho vivo": "Cor do sangue quando o sangramento vem do final do intestino ou do ânus."
    }
},

"Confusão mental": {
    "definicao": "Alteração da clareza de pensamento, com dificuldade para entender, lembrar ou se orientar.",
    "popular": "Quando a pessoa começa a falar coisas sem sentido, não reconhece as pessoas, esquece onde está ou age de forma estranha.",
    "clinico": "Alteração do estado mental ou delirium",
    "termos": {
        "Desorientação": "Quando não sabe onde está, que dia é ou quem é quem.",
        "Lapsos de memória": "Esquecimentos rápidos, confunde fatos recentes ou nomes."
    }
},

"Perda de consciência": {
    "definicao": "Quando a pessoa deixa de responder, desmaia ou apaga, mesmo que por pouco tempo.",
    "popular": "Quando a pessoa cai ou apaga e não responde. Pode voltar sozinha depois ou precisar de ajuda.",
    "clinico": "Perda de consciência",
    "termos": {}
},

"Trauma na cabeça": {
    "definicao": "Lesão na cabeça provocada por batida, queda ou impacto direto.",
    "popular": "Quando a pessoa bate a cabeça com força, em queda ou pancada. Pode ficar tonta, vomitar, esquecer o que aconteceu ou até desmaiar.",
    "clinico": "Traumatismo cranioencefálico (TCE)",
    "termos": {
        "Perda de consciência": "Quando a pessoa desmaia ou apaga depois da pancada.",
        "Amnésia": "Quando não lembra do que aconteceu antes ou depois da batida.",
        "Vômito em jato": "Quando vomita com força, sem esforço, após o trauma."
    }
},

"Manchas anormais na pele": {
    "definicao": "Alterações na coloração da pele, como manchas vermelhas, roxas, escuras ou esbranquiçadas.",
    "popular": "Manchas que surgem na pele do nada ou após remédio, febre ou pancada. Pode coçar, doer, espalhar ou mudar de cor com o tempo.",
    "clinico": "Exantema, petéquias ou equimoses (dependendo do tipo)",
    "termos": {
        "Petéquias": "Manchinhas vermelhas pequenas que não somem quando aperta.",
        "Equimose": "Mancha roxa, tipo hematoma.",
        "Lesão disseminada": "Quando as manchas se espalham pelo corpo todo.",
        "Bordas elevadas": "É quando a parte de divisão entre mancha e pele está mais pra cima que a mancha em si",
        "Descamação": "É quando parece que a pele está se soltando do corpo,em forma mais fina"
    }
},

"Incontinência urinária": {
    "definicao": "Incapacidade de segurar a urina, com perdas involuntárias.",
    "popular": "Quando a pessoa faz xixi sem querer, seja aos poucos ou tudo de uma vez, mesmo tentando segurar.",
    "clinico": "Incontinência urinária",
    "termos": {
        "Urgência urinária": "Quando dá vontade súbita e forte de urinar.",
        "Perda involuntária": "Quando escapa xixi sem conseguir controlar.",
        "Pequenos escapes": "Quando uma pequena quantidade de urina escapa involuntariamente "
    }
},

"Coriza e espirros": {
    "definicao": "Coriza é o nariz escorrendo, e espirros são expulsões rápidas de ar pelo nariz e boca, geralmente por irritação.",
    "popular": "Nariz escorrendo sem parar, espirrando o tempo todo, com ou sem febre. Pode ser gripe, resfriado ou alergia.",
    "clinico": "Rinorreia e espirros",
    "termos": {
        "Secreção clara": "Catarro transparente, típico de alergia ou vírus.",
        "Secreção purulenta": "Catarro amarelo ou verde, indicando infecção.",
        "Crise alérgica": "Quando os espirros e o nariz escorrendo não param.",
        "Irritação nasal":"É quando o nariz arde,dando uma sensação de queimação"
    }
},

"Incontinência urinária em idosos": {
    "definicao": "Perda involuntária de urina, comum na população idosa por fatores musculares, neurológicos ou medicamentos.",
    "popular": "O idoso começa a fazer xixi sem perceber ou não consegue chegar ao banheiro a tempo. Pode acontecer à noite ou durante o dia, com ou sem aviso.",
    "clinico": "Incontinência urinária senil",
    "termos": {
        "Incontinência de urgência": "Quando escapa porque não dá tempo de chegar.",
        "Incontinência por transbordamento": "A bexiga enche tanto que começa a vazar.",
        "Noctúria": "Acordar à noite para urinar com muita frequência.",
        "Perda total do controle urinário": "Quando se perde completamente a capacidade de decidir a hora em que se faz xixi",
        "Incontinência frequente": "Quando se tem a capacidade de segurar o xixi às vezes,mas na maioria das vezes não",
        "Gotejamente": "Quando somente algumas gotas escapam de vez em quando",
        "Leves escapes ocasionais": "Quando uma pequena quantidade de urina escapa involuntariamente,mas somente em poucas situações"
    }
},

"Queda em idosos": {
    "definicao": "Perda de equilíbrio ou escorregão que leva ao chão, com ou sem lesão.",
    "popular": "Quando o idoso cai sozinho, tropeça, escorrega ou perde a força. Pode bater a cabeça, quebrar ossos ou ficar muito assustado.",
    "clinico": "Queda de altura do próprio corpo",
    "termos": {
        "Perda de estabilidade": "Quando o idoso se desequilibra com facilidade.",
        "Fratura": "Quebra de osso após a queda.",
        "Síncope": "Desmaio que leva à queda.",
        "Perda de consciência": "Quando a pessoa desmaia ou apaga depois da pancada.",
        "Tombos esporádicos": "Quando o idoso cai levemente em raras ocasiões,mas sem consequências graves"
    }
},

"Delírio em idosos": {
    "definicao": "Confusão mental repentina, com alteração na atenção, memória e comportamento.",
    "popular": "Quando o idoso começa a falar coisa sem sentido, se perde no tempo e espaço ou vê coisas que não existem. Pode surgir de repente e piorar à noite.",
    "clinico": "Delirium",
    "termos": {
        "Desorientação": "Quando não sabe onde está, que dia é ou quem são as pessoas.",
        "Alucinação": "Ver ou ouvir coisas que não existem.",
        "Flutuação de consciência": "Às vezes tá bem, outras vezes não entende nada.",
        "Confusão mental": "Dificuldade de pensar normalmente",
        "Alteração de comportamento": "É quando o idoso passa a tomar decisões  que não são coerente com o que ele pensava antes"
    }
},

"Politrauma": {
    "definicao": "Lesão corporal severa que coloca a vida em risco, como batidas fortes, atropelamentos ou quedas de altura.",
    "popular": "Quando a pessoa se machuca seriamente, com muito sangue, fratura exposta, dificuldade pra respirar ou inconsciência.",
    "clinico": "Trauma de alta energia",
    "termos": {
        "Fratura exposta": "Osso quebrado que aparece pra fora da pele.",
        "Hemorragia": "Perda grande de sangue.",
        "Comprometimento neurológico": "Perda de movimento, fala ou consciência.",
        "Dor localizada": "É quando a dor fica em um lugar só",
        "Fratura": "É quando um osso quebra"
    }
},
    
"Dor de dente": {
    "definicao": "Dor localizada nos dentes, podendo ser constante ou pulsante.",
    "popular": "Quando o dente começa a doer forte, latejar ou doer ao morder. Pode vir com inchaço, febre ou dor irradiada pra cabeça.",
    "clinico": "Odontalgia",
    "termos": {
        "Abcesso dentário": "Inchaço com pus perto do dente.",
        "Irradiação": "Quando a dor vai pra orelha, pescoço ou cabeça.",
        "Sensibilidade": "Dor ao comer doce, gelado ou quente."
    }
},

"Alteração na audição": {
    "definicao": "Redução da audição ou percepção de sons anormais.",
    "popular": "Quando a pessoa começa a escutar menos, sentir o ouvido tapado, ouvir zumbido ou ter dor no ouvido.",
    "clinico": "Hipoacusia ou zumbido",
    "termos": {
        "Zumbido": "Som no ouvido como chiado, apito ou buzina.",
        "Perda súbita ": "Quando para de ouvir de repente.",
        "Otite": "Inflamação do ouvido que causa dor e secreção.",
        "Zumbido": "Comoo um chiado que fica toda hor presente"
    }
},

"Dor de garganta": {
    "definicao": "Dor ou irritação na garganta, que pode dificultar engolir ou falar.",
    "popular": "Aquela dor pra engolir, que às vezes vem com pus, placas brancas ou febre. Pode arder, queimar ou deixar a voz rouca.",
    "clinico": "Faringite ou amigdalite",
    "termos": {
        "Placas": "Manchas esbranquiçadas ou amareladas nas amígdalas, indicando infecção.",
        "Pus visível": "Material branco que sai da garganta ou fica grudado.",
        "Irritação": "Sensação de garganta arranhando ou pegando fogo."
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
        "Palidez": "É quando a pessoa tá mais branca que o normal.",
        "Irradiar": "É quando a dor do peito se espalha pelo braço ou mandíbula.",
              "Mandíbula": "É o osso da parte de baixo da cabeça; o queixo e os dentes de baixo estão inclusos nela."
        }
    },
"Dor de cabeça": {
    "definicao": "Dor na região da cabeça, que pode ter várias causas como tensão, problemas neurológicos ou infecções.",
    "popular": "É quando a cabeça começa a doer forte, média ou fraca, podendo vir com enjoo, luz incomodando ou vista embaçada.",
    "clinico": "Cefaleia",
    "termos": {
        "Visão turva": "Quando a vista fica embaçada ou difícil de enxergar.",
        "Sensibilidade à luz": "Quando a claridade incomoda muito os olhos.",
        "Náusea": "Aquela sensação de enjoo ou vontade de vomitar.",
        "Intermitente": "É qunado ocorre de vez em quando,passa,mas depos volta,de novo",
        "Rotineira": "É algo constante,ou seja,já se tornou parte da sua vida,de tanto que ocorre"
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
        "Desidratação": "Quando o corpo perde muito líquido, a pessoa fica fraca e com boca seca.",
        "Vômito em jato": "Vômito que sai com muita força, como uma mangueira."
        }
    },
"Dor abdominal": {
    "definicao": "Dor na barriga, que pode ter várias causas como gases, inflamações ou infecções.",
    "popular": "É dor na barriga, que pode ser leve ou forte, de repente ou aos poucos, e pode vir com febre ou vômito.",
    "clinico": "Dor abdominal",
    "termos": {
        "Rigidez abdominal": "Barriga dura e dolorida ao apertar.",
        "Localizada": "Quando a dor está só em um ponto da barriga."
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
        "Calafrios": "Tremores de frio mesmo com febre.",
        "Persistente": "Febre que não melhora mesmo com remédio."
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
        st.session_state.clique_reflexo = {
            "numeros": [random.randint(0, 9) for _ in range(10)],
            "respostas": [],
            "indice": 0,
            "inicio_tempo": time.time()
        }

    dados = st.session_state.clique_reflexo
    total = len(dados["numeros"])

    if dados["indice"] < total:
        atual = dados["numeros"][dados["indice"]]
        st.markdown(f"### Número mostrado: **{atual}**")
        st.markdown(f"Rodada {dados['indice'] + 1} de {total}")

        # Guarda o tempo de exibição do número se ainda não estiver registrado
        if "tempo_inicio_atual" not in st.session_state or st.session_state.get("ultima_rodada", -1) != dados["indice"]:
            st.session_state.tempo_inicio_atual = time.time()
            st.session_state.ultima_rodada = dados["indice"]

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Clique se for 7", key=f"clicar_{dados['indice']}"):
                tempo_reacao = time.time() - st.session_state.tempo_inicio_atual
                dados["respostas"].append(("clicou", atual, tempo_reacao))
                dados["indice"] += 1
                st.rerun()
        with col2:
            if st.button("Ignorar", key=f"ignorar_{dados['indice']}"):
                tempo_reacao = time.time() - st.session_state.tempo_inicio_atual
                dados["respostas"].append(("ignorou", atual, tempo_reacao))
                dados["indice"] += 1
                st.rerun()
    else:
        st.subheader("📊 Resultado do Teste")

        # Filtra apenas as respostas válidas com 3 elementos (ação, número, tempo)
respostas_filtradas = [r for r in dados["respostas"] if len(r) == 3]

# Agora processa só o que tem formato correto
cliques_certos = sum(1 for acao, n, t in respostas_filtradas if acao == "clicou" and n == 7)
cliques_errados = sum(1 for acao, n, t in respostas_filtradas if acao == "clicou" and n != 7)
deixou_passar = sum(1 for acao, n, t in respostas_filtradas if acao == "ignorou" and n == 7)
total_7 = sum(1 for _, n, _ in respostas_filtradas if n == 7)

tempos_reacao_corretos = [t for acao, n, t in respostas_filtradas if acao == "clicou" and n == 7]
media_tempo = sum(tempos_reacao_corretos) / len(tempos_reacao_corretos) if tempos_reacao_corretos else None

        # Exibição
    st.write(f"Números 7 apresentados: {total_7}")
    st.write(f"Cliques corretos: {cliques_certos}")
    st.write(f"Cliques errados (falsos positivos): {cliques_errados}")
    st.write(f"Números 7 ignorados (erros por omissão): {deixou_passar}")

    if media_tempo is not None:
        st.write(f"⏱️ Tempo médio de reação nos acertos: **{media_tempo:.2f} segundos**")
        if media_tempo <= 0.8:
            st.success("🧠 Tempo de reação excelente!")
        elif media_tempo <= 1.5:
            st.info("⚠️ Tempo de reação dentro do esperado.")
        else:
            st.warning("🐢 Tempo de reação um pouco lento. Pode ser cansaço, distração ou atenção baixa.")
    else:
        st.write("⚠️ Nenhum clique correto registrado, tempo de reação não avaliado.")

        # ESTE BOTÃO FICA FORA DO BLOCO 'if' e 'else'
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
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Variação de peso (últimos 30 dias)":
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
elif opcao == "Autotestes para apuração de sintoma" and subteste == "Audição (Detecção de som)":
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

elif opcao == "Autotestes para apuração de sintoma" and subteste == "Audição (Frequências altas e baixas)":
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

def opcoes_inchaco_linfonodos():
    return [
        "Inchaço acompanhado de febre ou perda de peso",
        "Inchaço doloroso ou inflamado",
        "Inchaço perceptível, mas sem outros sintomas",
        "Inchaço pequeno e isolado, sem dor"
    ]

def classificar_inchaco_linfonodos(resp):
    if "febre" in resp or "perda de peso" in resp:
        return "laranja", "Pode indicar infecção sistêmica ou condição mais grave."
    elif "doloroso" in resp or "inflamado" in resp:
        return "amarelo", "Dor ou inflamação sugere infecção localizada nos linfonodos."
    elif "sem outros sintomas" in resp:
        return "amarelo", "Mesmo sem outros sintomas, o inchaço pode indicar inflamação."
    else:
        return "verde", "Pequeno inchaço isolado geralmente não é preocupante."

def opcoes_nodulo_mama():
    return [
        "Nódulo crescente ou com secreção",
        "Nódulo duro, fixo ou irregular",
        "Nódulo doloroso, mas recente",
        "Pequeno nódulo móvel, sem dor"
    ]

def classificar_nodulo_mama(resp):
    if "secreção" in resp or "crescente" in resp:
        return "laranja", "Nódulo com secreção ou crescimento rápido deve ser avaliado com urgência."
    elif "duro" in resp or "fixo" in resp or "irregular" in resp:
        return "laranja", "Nódulos fixos e irregulares podem sugerir lesões suspeitas."
    elif "doloroso" in resp:
        return "amarelo", "Nódulo doloroso recente costuma ser benigno, mas merece atenção."
    else:
        return "amarelo", "Nódulo móvel e sem dor é geralmente benigno, mas deve ser acompanhado."

def opcoes_nodulo_testicular():
    return [
        "Nódulo firme e indolor, perceptível há dias",
        "Nódulo doloroso ou com inchaço",
        "Mudança recente no tamanho do testículo",
        "Sensação de caroço pequeno e móvel"
    ]

def classificar_nodulo_testicular(resp):
    if "firme" in resp and "indolor" in resp:
        return "laranja", "Nódulos firmes e indolores podem ser sinais de alterações mais sérias."
    elif "doloroso" in resp or "inchaço" in resp:
        return "amarelo", "Dor e inchaço podem indicar inflamação ou infecção local."
    elif "tamanho do testículo" in resp:
        return "amarelo", "Mudanças recentes no tamanho merecem investigação."
    else:
        return "amarelo", "Caroços pequenos e móveis costumam ser benignos, mas devem ser avaliados."

def opcoes_dor_testiculos():
    return [
        "Dor intensa e súbita em um dos testículos",
        "Dor moderada com inchaço",
        "Desconforto leve ao tocar",
        "Dor leve que desapareceu"
    ]

def classificar_dor_testiculos(resp):
    if "intensa" in resp and "súbita" in resp:
        return "vermelho", "Dor súbita e intensa pode indicar torção testicular, uma emergência médica."
    elif "moderada" in resp or "inchaço" in resp:
        return "laranja", "Dor com inchaço pode estar relacionada a infecção ou inflamação."
    elif "leve ao tocar" in resp:
        return "amarelo", "Desconforto leve pode ser transitório, mas deve ser observado."
    else:
        return "verde", "Dor leve que já desapareceu geralmente não é preocupante."

def opcoes_secrecao_mamilar():
    return [
        "Secreção com sangue ou espontânea",
        "Secreção unilateral e persistente",
        "Saída de secreção ao apertar o mamilo",
        "Secreção ocasional, sem outros sintomas"
    ]

def classificar_secrecao_mamilar(resp):
    if "sangue" in resp or "espontânea" in resp:
        return "laranja", "Secreção com sangue ou espontânea pode estar relacionada a alterações mamárias significativas."
    elif "unilateral" in resp or "persistente" in resp:
        return "amarelo", "Secreções persistentes ou de um lado só merecem investigação médica."
    elif "ao apertar" in resp:
        return "amarelo", "Pode ser fisiológica, mas deve ser observada."
    else:
        return "verde", "Secreção leve e ocasional normalmente não representa risco."

def opcoes_sangue_semen():
    return [
        "Presença frequente de sangue no sêmen",
        "Sangue apareceu após dor ou trauma",
        "Pequena quantidade única, sem dor",
        "Aparência alterada, mas sem sangue visível"
    ]

def classificar_sangue_semen(resp):
    if "frequente" in resp:
        return "laranja", "Sangue frequente no sêmen pode ter causas graves e deve ser investigado."
    elif "dor" in resp or "trauma" in resp:
        return "laranja", "Presença de sangue após dor ou trauma pode indicar lesão local."
    elif "única" in resp and "sem dor" in resp:
        return "amarelo", "Um episódio isolado pode não ser grave, mas merece atenção se repetir."
    else:
        return "verde", "Aparência alterada sem sangue não indica risco imediato."

def opcoes_trauma_craniano():
    return [
        "Batida forte com perda de consciência, vômito ou amnésia",
        "Batida com dor de cabeça intensa e tontura",
        "Batida leve com dor local",
        "Topada leve, sem sintomas associados"
    ]

def classificar_trauma_craniano(resp):
    if resp == "Batida forte com perda de consciência, vômito ou amnésia":
        return "vermelho", "Sinais neurológicos após trauma indicam risco elevado."
    elif resp == "Batida com dor de cabeça intensa e tontura":
        return "laranja", "Dor intensa e tontura após pancada pode indicar concussão."
    elif resp == "Batida leve com dor local":
        return "amarelo", "Dor local leve é comum, mas deve ser monitorada."
    else:
        return "verde", "Topadas leves sem sintomas geralmente não causam preocupação."

def opcoes_manchas_pele():
    return [
        "Mancha escura irregular com crescimento rápido",
        "Ferida que não cicatriza com bordas elevadas",
        "Mancha vermelha com descamação e coceira",
        "Mancha clara e estável, sem outros sintomas"
    ]

def classificar_manchas_pele(resp):
    if resp == "Mancha escura irregular com crescimento rápido":
        return "vermelho", "Pode ser sinal de melanoma, um tipo grave de câncer de pele."
    elif resp == "Ferida que não cicatriza com bordas elevadas":
        return "laranja", "Feridas persistentes podem indicar lesão maligna."
    elif resp == "Mancha vermelha com descamação e coceira":
        return "amarelo", "Pode indicar condição dermatológica inflamatória."
    else:
        return "verde", "Manchas estáveis e sem sintomas são geralmente benignas."


def opcoes_incontinencia_urinaria():
    return [
        "Perda total de controle com dor ou febre",
        "Urina escapando frequentemente sem aviso",
        "Perda leve ao tossir ou se mexer",
        "Pequenos escapes ocasionais sem desconforto"
    ]

def classificar_incontinencia_urinaria(resp):
    if resp == "Perda total de controle com dor ou febre":
        return "vermelho", "Incontinência com dor ou febre pode indicar infecção urinária grave."
    elif resp == "Urina escapando frequentemente sem aviso":
        return "laranja", "Pode indicar alteração neurológica ou do trato urinário."
    elif resp == "Perda leve ao tossir ou se mexer":
        return "amarelo", "Incontinência leve pode ser comum, mas merece atenção."
    else:
        return "verde", "Escapes leves e raros são comuns e geralmente não preocupam."

def opcoes_coriza_espirros():
    return [
        "Coriza intensa com dificuldade para respirar e febre alta",
        "Espirros constantes e nariz muito entupido",
        "Coriza leve com espirros ocasionais",
        "Leve irritação nasal sem outros sintomas"
    ]

def classificar_coriza_espirros(resp):
    if resp == "Coriza intensa com dificuldade para respirar e febre alta":
        return "vermelho", "Procure atendimento médico imediato. Pode indicar uma infecção respiratória grave."
    elif resp == "Espirros constantes e nariz muito entupido":
        return "laranja", "É aconselhável procurar atendimento. Pode ser sinal de infecção ou crise alérgica importante."
    elif resp == "Coriza leve com espirros ocasionais":
        return "amarelo", "Observe a evolução dos sintomas. Pode ser apenas um resfriado leve."
    else:
        return "verde", "Sem sinais de alerta. Mantenha repouso e hidratação."

def opcoes_incontinencia_idoso():
    return [
        "Perda total do controle urinário com febre ou confusão",
        "Incontinência frequente e súbita, com ardência",
        "Gotejamento ou perda leve ao se movimentar",
        "Leves escapes ocasionais sem outros sintomas"
    ]

def classificar_incontinencia_idoso(resp):
    if resp == "Perda total do controle urinário com febre ou confusão":
        return "vermelho", "Procure atendimento imediato. Pode indicar infecção grave ou distúrbio neurológico."
    elif resp == "Incontinência frequente e súbita, com ardência":
        return "laranja", "Procure orientação médica. Pode ser infecção urinária ou inflamação."
    elif resp == "Gotejamento ou perda leve ao se movimentar":
        return "amarelo", "Acompanhe os sintomas. É importante discutir com um médico em breve."
    else:
        return "verde", "Sem sinais de urgência. Pode ser manejado com orientação médica regular."

def opcoes_queda_idoso():
    return [
        "Queda com perda de consciência ou fratura",
        "Queda com dor intensa ou dificuldade para se levantar",
        "Queda leve com dor local e hematoma",
        "Tombos esporádicos sem dor ou lesão"
    ]

def classificar_queda_idoso(resp):
    if resp == "Queda com perda de consciência ou fratura":
        return "vermelho", "Emergência! Vá ao pronto-socorro imediatamente."
    elif resp == "Queda com dor intensa ou dificuldade para se levantar":
        return "laranja", "Recomenda-se avaliação médica urgente para descartar lesões."
    elif resp == "Queda leve com dor local e hematoma":
        return "amarelo", "Observe a evolução. Pode ser necessário exame se piorar."
    else:
        return "verde", "Sem sinais de alarme imediato, mas fique atento a alterações."

def opcoes_delirio_idoso():
    return [
        "Desorientação súbita com agitação ou alucinações",
        "Confusão mental com alteração de comportamento e/ou flutuação de consciência ",
        "Esquecimento leve e dificuldade para responder",
        "Ligeira confusão passageira, mas estável"
    ]

def classificar_delirio_idoso(resp):
    if "Desorientação súbita" in resp:
        return "vermelho", "Procure ajuda médica imediatamente. Pode ser uma emergência neurológica ou infecciosa."
    elif "alteração de comportamento" in resp:
        return "laranja", "Sinais de alerta. Agende uma consulta médica o quanto antes."
    elif "dificuldade para responder" in resp:
        return "amarelo", "É importante acompanhar e relatar esses sintomas ao médico."
    else:
        return "verde", "Sem sinais urgentes, mas siga observando o comportamento."

def opcoes_trauma_grave():
    return [
        "Acidente com perda de consciência, fratura exposta ou sangramento grave",
        "Queda ou impacto com dor intensa e possível fratura",
        "Batida com dor localizada e hematoma",
        "Pequeno impacto sem dor ou limitação"
    ]

def classificar_trauma_grave(resp):
    if resp == "Acidente com perda de consciência, fratura exposta ou sangramento grave":
        return "vermelho", "Emergência grave. Procure o pronto-socorro imediatamente."
    elif resp == "Queda ou impacto com dor intensa e possível fratura":
        return "laranja", "Alerta de possível fratura. Vá à emergência ou pronto atendimento."
    elif resp == "Batida com dor localizada e hematoma":
        return "amarelo", "Lesão leve. Acompanhe os sintomas e procure atendimento se piorar."
    else:
        return "verde", "Sem sinais de urgência, apenas observe."

def opcoes_dor_odontologica():
    return [
        "Dor forte com inchaço no rosto ou febre",
        "Dor intensa ao mastigar ou à noite",
        "Dor leve com sensibilidade ao frio/quente",
        "Leve incômodo eventual"
    ]

def classificar_dor_odontologica(resp):
    if "inchaço no rosto" in resp or "febre" in resp:
        return "vermelho", "Emergência odontológica. Pode indicar infecção grave."
    elif "mastigar" in resp or "à noite" in resp:
        return "laranja", "Dor moderada. Agende atendimento com dentista rapidamente."
    elif "sensibilidade" in resp:
        return "amarelo", "Acompanhe os sintomas. Pode indicar problema dentário inicial."
    else:
        return "verde", "Sintoma leve. Siga com higiene bucal e monitoramento."

def opcoes_alteracao_auditiva():
    return [
        "Perda súbita da audição com zumbido ou dor",
        "Diminuição importante da audição com secreção",
        "Sensação de ouvido tampado leve",
        "Alteração momentânea após barulho ou pressão"
    ]

def classificar_alteracao_auditiva(resp):
    if "Perda súbita" in resp:
        return "vermelho", "Procure atendimento médico urgente. Pode indicar problema auditivo grave."
    elif "secreção" in resp:
        return "laranja", "Alerta para infecção. Busque avaliação médica."
    elif "ouvido tampado" in resp:
        return "amarelo", "Sintoma leve. Se persistir, procure um otorrino."
    else:
        return "verde", "Sem sinais de gravidade. Observe os sintomas."
            
def opcoes_dor_garganta():
    return [
        "Dor forte com dificuldade de engolir e febre alta",
        "Dor moderada com placas ou pus visível",
        "Irritação leve e dificuldade discreta",
        "Leve desconforto ao falar ou engolir"
    ]

def classificar_dor_garganta(resp):
    if "febre alta" in resp:
        return "vermelho", "Procure pronto atendimento. Pode ser infecção grave."
    elif "placas" in resp or "pus" in resp:
        return "laranja", "Atenção! Pode ser amigdalite ou infecção. Busque orientação médica."
    elif "Irritação leve" in resp:
        return "amarelo", "Monitorar evolução dos sintomas."
    else:
        return "verde", "Sem sinais de urgência. Mantenha hidratação."

def opcoes_mordedura():
    return [
        "Mordida profunda com sangramento e suspeita de raiva",
        "Mordida com dor e sinais de infecção",
        "Mordida superficial com inchaço",
        "Pequeno arranhão sem dor"
    ]

def classificar_mordedura(resp):
    if "raiva" in resp:
        return "vermelho", "Emergência! Vá ao hospital imediatamente. Risco de raiva."
    elif "infecção" in resp:
        return "laranja", "Atenção! Pode ser necessário antibiótico. Busque atendimento."
    elif "inchaço" in resp:
        return "amarelo", "Monitorar. Se aumentar, vá ao médico."
    else:
        return "verde", "Sem risco aparente. Mantenha o local limpo e observe."
            
def opcoes_queimaduras():
    return [
        "Queimadura extensa, com bolhas e pele escura",
        "Queimadura moderada com bolhas e dor intensa",
        "Queimadura pequena com vermelhidão e dor leve",
        "Apenas vermelhidão passageira sem dor"
    ]

def classificar_queimaduras(resp):
    if "extensa" in resp:
        return "vermelho", "Queimadura grave. Vá ao pronto-socorro imediatamente."
    elif "moderada" in resp:
        return "laranja", "Pode necessitar de avaliação médica e curativo especializado."
    elif "vermelhidão e dor leve" in resp:
        return "amarelo", "Trate com pomada e observe."
    else:
        return "verde", "Sem gravidade. Mantenha a hidratação da pele."
            
def opcoes_ferida_nao_traumatica():
    return [
        "Ferida grande com secreção e mal cheiro",
        "Ferida dolorosa com sinais de infecção",
        "Ferida pequena com vermelhidão",
        "Apenas uma mancha sem dor ou secreção"
    ]

def classificar_ferida_nao_traumatica(resp):
    if "mal cheiro" in resp:
        return "vermelho", "Infecção grave. Vá ao médico imediatamente."
    elif "sinais de infecção" in resp:
        return "laranja", "Necessário tratamento. Consulte um médico."
    elif "vermelhidão" in resp:
        return "amarelo", "Pode evoluir. Fique atento a pioras."
    else:
        return "verde", "Sem risco aparente. Mantenha limpo e seco."

def opcoes_gases():
    return [
        "Dor abdominal intensa com inchaço e sem alívio",
        "Desconforto forte e barulhos intestinais altos",
        "Flatulência frequente com leve dor",
        "Gases leves, sem incômodo relevante"
    ]

def classificar_gases(resp):
    if "sem alívio" in resp:
        return "laranja", "Sinais de distensão intestinal. Avaliação médica pode ser necessária."
    elif "Desconforto forte" in resp:
        return "amarelo", "Acompanhe os sintomas e procure ajuda se persistirem."
    elif "leve dor" in resp:
        return "amarelo", "Sintoma comum, observe a evolução."
    else:
        return "verde", "Sem sinais de alerta."

def opcoes_sangramento_retal():
    return [
        "Sangue vermelho vivo em grande quantidade",
        "Sangue moderado com dor abdominal",
        "Poucas gotas de sangue no papel higiênico",
        "Sangramento leve e isolado"
    ]

def classificar_sangramento_retal(resp):
    if "grande quantidade" in resp:
        return "vermelho", "Procure atendimento médico imediatamente."
    elif "dor abdominal" in resp:
        return "laranja", "Alerta para hemorroidas ou outras causas. Consulte o médico."
    elif "poucas gotas" in resp:
        return "amarelo", "Fique atento. Se recorrente, busque um especialista."
    else:
        return "verde", "Isolado e leve. Continue observando."

def opcoes_confusao_mental():
    return [
        "Desorientação completa e fala incoerente",
        "Confusão mental com dificuldade de reconhecer pessoas ou lugares",
        "Leve desatenção ou lapsos de memória",
        "Ligeira distração sem prejuízo das atividades"
    ]

def classificar_confusao_mental(resp):
    if resp == "Desorientação completa e fala incoerente":
        return "vermelho", "A desorientação completa e a fala incoerente indicam um quadro grave, que pode estar relacionado a alterações neurológicas ou metabólicas. Procure atendimento médico urgente."
    elif resp == "Confusão mental com dificuldade de reconhecer pessoas ou lugares":
        return "laranja", "Esse grau de confusão pode indicar um problema em evolução, como infecção, efeito colateral de medicamentos ou distúrbios cognitivos. Avaliação médica é recomendada."
    elif resp == "Leve desatenção ou lapsos de memória":
        return "amarelo", "Pode ser um sinal inicial de cansaço, estresse ou alteração cognitiva leve. Acompanhe com atenção."
    else:
        return "verde", "Aparentemente estável, sem sinais de alarme. Continue observando."

def opcoes_perda_consciencia():
    return [
        "Perda total de consciência recente sem recuperação",
        "Desmaio com recuperação, mas com tontura persistente",
        "Sensação de quase desmaio, mas sem queda",
        "Nenhum episódio de perda de consciência"
    ]

def classificar_perda_consciencia(resp):
    if resp == "Perda total de consciência recente sem recuperação":
        return "vermelho", "A perda total de consciência sem recuperação imediata é um sinal de gravidade e pode indicar condições neurológicas, cardíacas ou metabólicas sérias. Procure atendimento médico urgente."
    elif resp == "Desmaio com recuperação, mas com tontura persistente":
        return "laranja", "Apesar da recuperação, a tontura persistente pode indicar um problema subjacente que merece investigação médica em breve."
    elif resp == "Sensação de quase desmaio, mas sem queda":
        return "amarelo", "É importante observar se há outros sintomas associados. Pode ser causado por desidratação, ansiedade ou queda de pressão."
    else:
        return "verde", "Sem sinais de alerta importantes no momento. Continue acompanhando e procure ajuda se o quadro piorar."

def opcoes_hipotensao():
    return [
        "Pressão muito baixa com tontura e palidez extrema",
        "Tontura ao levantar e fraqueza acentuada",
        "Sensação de pressão baixa leve",
        "Sem sintomas de pressão baixa"
    ]

def classificar_hipotensao(resp):
    if resp == "Pressão muito baixa com tontura e palidez extrema":
        return "vermelho", "Queda acentuada da pressão arterial com sintomas intensos pode indicar um quadro de emergência, como choque circulatório. Procure atendimento médico imediatamente."
    elif resp == "Tontura ao levantar e fraqueza acentuada":
        return "laranja", "Esses sinais sugerem hipotensão ortostática ou desidratação. É necessário monitorar e, se persistirem, buscar avaliação médica."
    elif resp == "Sensação de pressão baixa leve":
        return "amarelo", "Pode ser transitório, especialmente em dias quentes ou com jejum prolongado. Mantenha hidratação e observe evolução."
    else:
        return "verde", "Sem sintomas relevantes no momento. Mantenha hábitos saudáveis e continue observando possíveis alterações."

def opcoes_hipoglicemia():
    return [
        "Desmaio ou confusão com sudorese intensa",
        "Tontura, tremores e fome súbita",
        "Leve fraqueza ou irritação",
        "Sem sintomas associados"
    ]

def classificar_hipoglicemia(resp):
    if resp == "Desmaio ou confusão com sudorese intensa":
        return "vermelho", "Quadro grave de hipoglicemia que pode levar à perda de consciência ou convulsões. Procure socorro médico imediato."
    elif resp == "Tontura, tremores e fome súbita":
        return "laranja", "Esses sintomas indicam uma queda importante de glicose no sangue. É necessário agir rápido com ingestão de açúcar e monitoramento."
    elif resp == "Leve fraqueza ou irritação":
        return "amarelo", "Podem ser sinais iniciais de hipoglicemia. Faça uma pausa, alimente-se e observe a evolução."
    else:
        return "verde", "Sem indícios de hipoglicemia no momento. Mantenha alimentação equilibrada e rotina de cuidados, se for diabético."

def opcoes_hiperglicemia():
    return [
        "Sede intensa, urina excessiva e cansaço extremo",
        "Mal-estar com enjoo e dor abdominal",
        "Leve fraqueza e sede acima do normal",
        "Sem sintomas associados"
    ]

def classificar_hiperglicemia(resp):
    if resp == "Sede intensa, urina excessiva e cansaço extremo":
        return "vermelho", "Sintomas graves que podem indicar cetoacidose diabética. Procure atendimento médico com urgência."
    elif resp == "Mal-estar com enjoo e dor abdominal":
        return "laranja", "Alterações associadas à hiperglicemia moderada. Requer controle e possível avaliação médica."
    elif resp == "Leve fraqueza e sede acima do normal":
        return "amarelo", "Pode ser um sinal de glicemia elevada. Reforce a hidratação e monitore os níveis de glicose."
    else:
        return "verde", "Sem sintomas evidentes de glicose elevada. Continue com os cuidados habituais."

def opcoes_temperatura_baixa():
    return [
        "Extremidades frias com sonolência ou confusão",
        "Calafrios e pele fria persistente",
        "Sensação de frio sem outros sintomas",
        "Temperatura normal para o ambiente"
    ]

def classificar_temperatura_baixa(resp):
    if resp == "Extremidades frias com sonolência ou confusão":
        return "vermelho", "Risco de hipotermia grave. É necessário buscar aquecimento e atendimento médico imediatamente."
    elif resp == "Calafrios e pele fria persistente":
        return "laranja", "Sinais de hipotermia leve a moderada. Mantenha-se aquecido e monitorado."
    elif resp == "Sensação de frio sem outros sintomas":
        return "amarelo", "Situação leve, geralmente transitória. Observe se os sintomas evoluem."
    else:
        return "verde", "Temperatura adequada ao ambiente. Sem sinais de risco."

def opcoes_dor_durante_gravidez():
    return [
        "Dor intensa com sangramento ou perda de líquido",
        "Dor abdominal moderada e persistente",
        "Desconforto leve e intermitente",
        "Dor ocasional esperada para a gestação"
    ]

def classificar_dor_durante_gravidez(resp):
    if resp == "Dor intensa com sangramento ou perda de líquido":
        return "vermelho", "Pode indicar trabalho de parto prematuro ou complicações graves. Procure atendimento médico imediato."
    elif resp == "Dor abdominal moderada e persistente":
        return "laranja", "Dor constante pode indicar alguma alteração gestacional. Requer avaliação médica."
    elif resp == "Desconforto leve e intermitente":
        return "amarelo", "Sintomas comuns na gestação. Mantenha repouso e acompanhamento."
    else:
        return "verde", "Sem sinais preocupantes. Continue o pré-natal normalmente."

def opcoes_movimentos_fetais():
    return [
        "Nenhum movimento fetal percebido nas últimas horas",
        "Redução clara nos movimentos habituais",
        "Movimentos presentes, mas menos ativos que o normal",
        "Movimentos normais para o estágio gestacional"
    ]

def classificar_movimentos_fetais(resp):
    if resp == "Nenhum movimento fetal percebido nas últimas horas":
        return "vermelho", "Ausência de movimentos pode indicar sofrimento fetal. Busque avaliação médica urgente."
    elif resp == "Redução clara nos movimentos habituais":
        return "laranja", "Alteração na atividade fetal. Deve ser investigado pelo obstetra."
    elif resp == "Movimentos presentes, mas menos ativos que o normal":
        return "amarelo", "Pode ser normal em fases específicas da gestação. Observe e comunique qualquer mudança significativa."
    else:
        return "verde", "Movimentos fetais dentro do esperado. Continue acompanhando normalmente."

def opcoes_trabalho_parto():
    return [
        "Contrações intensas com sangramento ou bolsa rota",
        "Contrações regulares e dolorosas há mais de 1 hora",
        "Contrações leves e irregulares",
        "Apenas sensação de pressão pélvica sem dor"
    ]

def classificar_trabalho_parto(resp):
    if resp == "Contrações intensas com sangramento ou bolsa rota":
        return "vermelho", "Sinais de início do trabalho de parto com possíveis complicações. Dirija-se ao hospital imediatamente."
    elif resp == "Contrações regulares e dolorosas há mais de 1 hora":
        return "laranja", "Indica que o trabalho de parto pode estar começando. Procure orientação médica."
    elif resp == "Contrações leves e irregulares":
        return "amarelo", "Pode ser o início do trabalho de parto ou apenas contrações de treinamento. Observe a evolução."
    else:
        return "verde", "Sem indícios claros de início do trabalho de parto. Mantenha acompanhamento pré-natal."

def opcoes_febre_lactente():
    return [
        "Febre alta persistente com prostração ou recusa alimentar",
        "Febre alta mas bebê responde a estímulos",
        "Febre leve com comportamento preservado",
        "Febre passageira e sem outros sintomas"
    ]

def classificar_febre_lactente(resp):
    if "prostração" in resp or "recusa alimentar" in resp:
        return "vermelho", "Bebê com febre e sinais de gravidade como prostração ou recusa alimentar exige atendimento médico imediato."
    elif "responde a estímulos" in resp:
        return "laranja", "Febre alta, mas com boa resposta, ainda exige cuidado e monitoramento de evolução."
    elif "comportamento preservado" in resp:
        return "amarelo", "Febre leve, sem alteração no comportamento. Observe e mantenha hidratação."
    else:
        return "verde", "Febre passageira, sem sintomas de alerta. Continue observando e evite agasalhar em excesso."

def opcoes_choro_persistente():
    return [
        "Choro inconsolável há mais de 2 horas com sinais de dor",
        "Choro frequente e difícil de acalmar",
        "Choro leve mas diferente do habitual",
        "Choro normal para a idade"
    ]


def classificar_choro_persistente(resp):
    if "inconsolável" in resp:
        return "vermelho", "Choro inconsolável e prolongado pode indicar dor intensa, desconforto ou condição grave. Procure avaliação médica urgente."
    elif "difícil de acalmar" in resp:
        return "laranja", "Pode sugerir desconforto ou início de quadro infeccioso. Requer observação e possível consulta."
    elif "diferente do habitual" in resp:
        return "amarelo", "Mudanças sutis no padrão de choro podem indicar incômodo leve. Observe e anote se houver piora."
    else:
        return "verde", "Choro esperado para a idade. Mantenha a rotina e observação."

def opcoes_ictericia_neonatal():
    return [
        "Icterícia intensa em face e corpo com sonolência excessiva",
        "Amarelado moderado até o abdome",
        "Amarelado leve no rosto e olhos",
        "Discreto e com melhora espontânea"
    ]

def classificar_ictericia_neonatal(resp):
    if "sonolência" in resp:
        return "vermelho", "Icterícia intensa com sonolência pode indicar complicação neurológica. Procure atendimento imediatamente."
    elif "abdome" in resp:
        return "laranja", "A icterícia moderada requer avaliação para prevenir agravamento."
    elif "leve no rosto" in resp:
        return "amarelo", "Comum em recém-nascidos, mas precisa ser monitorado para evitar evolução."
    else:
        return "verde", "Sem sinais preocupantes. Mantenha acompanhamento neonatal."

def opcoes_queda_crianca():
    return [
        "Queda com perda de consciência ou vômito",
        "Batida na cabeça com alteração de comportamento",
        "Hematoma leve e sem sintomas",
        "Queda leve e criança está bem"
    ]

def classificar_queda_crianca(resp):
    if "perda de consciência" in resp:
        return "vermelho", "Sinais neurológicos após queda são graves. Leve a criança para avaliação médica imediatamente."
    elif "alteração de comportamento" in resp:
        return "laranja", "Mudança no comportamento pode indicar concussão leve. Observe com atenção e consulte o pediatra."
    elif "Hematoma leve" in resp:
        return "amarelo", "Provavelmente sem gravidade, mas continue observando evolução e sintomas."
    else:
        return "verde", "Sem sinais de alarme. A criança está bem após a queda."

def opcoes_vomito_crianca():
    return [
        "Vômito em jato frequente com sinais de desidratação",
        "Vômito constante após refeições",
        "Vômito isolado sem outros sintomas",
        "Vômito leve e passageiro"
    ]

def classificar_vomito_crianca(resp):
    if "jato" in resp or "desidratação" in resp:
        return "vermelho", "Vômito em jato ou sinais de desidratação exigem atendimento médico imediato."
    elif "constante após refeições" in resp:
        return "laranja", "Pode indicar intolerância alimentar ou infecção. Avaliação médica recomendada."
    elif "isolado" in resp:
        return "amarelo", "Quadro leve e isolado. Continue observando hidratação e evolução."
    else:
        return "verde", "Sem sinais de alarme. Situação tranquila."
            
def opcoes_diarreia_crianca():
    return [
        "Diarreia com sangue ou sinais de desidratação",
        "Diarreia frequente com febre",
        "Diarreia moderada e sem sinais de alerta",
        "Evacuações levemente amolecidas"
    ]

def classificar_diarreia_crianca(resp):
    if "sangue" in resp or "desidratação" in resp:
        return "vermelho", "Diarreia com sinais graves pode indicar infecção intestinal séria. Procure atendimento urgente."
    elif "febre" in resp:
        return "laranja", "Quadro possivelmente infeccioso. Requer atenção e hidratação adequada."
    elif "moderada" in resp:
        return "amarelo", "Sem sinais graves. Mantenha hidratação e alimentação leve."
    else:
        return "verde", "Evacuação levemente alterada, mas sem riscos aparentes."

def opcoes_dor_no_peito():
    return [
        "Dor com desmaio, palidez ou confusão",
        "Dor muito forte e piorando",
        "Dor que irradia pro braço ou mandíbula",
        "Dor moderada com suor ou enjoo",
        "Dor leve, estável e sem outros sintomas"
    ]

def classificar_dor_no_peito(resp):
    if resp == "Dor com desmaio, palidez ou confusão":
        return "vermelho", "Sinais sugestivos de infarto ou grave alteração circulatória. Procure emergência imediatamente."
    elif resp == "Dor muito forte e piorando":
        return "laranja", "Dor torácica progressiva exige avaliação médica o quanto antes."
    elif resp in ["Dor que irradia pro braço ou mandíbula", "Dor moderada com suor ou enjoo"]:
        return "amarelo", "Possível origem cardíaca. Fique atento a evolução e procure um pronto atendimento se piorar."
    else:
        return "verde", "Dor leve e estável. Continue monitorando."

def opcoes_febre():
    return [
        "Acima de 39°C com calafrios e mal-estar intenso",
        "Persistente entre 38°C e 39°C",
        "Leve, com sintomas gripais",
        "Febre isolada sem outros sintomas"
    ]

def classificar_febre(resp):
    if resp == "Acima de 39°C com calafrios e mal-estar intenso":
        return "vermelho", "Febre alta com sinais sistêmicos pode indicar infecção grave. Procure ajuda médica."
    elif resp == "Persistente entre 38°C e 39°C":
        return "laranja", "Febre persistente requer atenção, principalmente se durar mais de 48 horas."
    elif resp == "Leve, com sintomas gripais":
        return "amarelo", "Geralmente infecciosa e autolimitada. Repouso e hidratação ajudam na recuperação."
    else:
        return "verde", "Febre isolada, sem sinais de alarme. Continue monitorando."

def opcoes_falta_de_ar():
    return [
        "Grave, com lábios roxos ou confusão",
        "Moderada e constante",
        "Leve, apenas aos esforços",
        "Sem desconforto relevante"
    ]

def classificar_falta_de_ar(resp):
    if resp == "Grave, com lábios roxos ou confusão":
        return "vermelho", "Insuficiência respiratória grave. Procure socorro imediatamente."
    elif resp == "Moderada e constante":
        return "laranja", "Pode indicar infecção ou crise respiratória. Requer avaliação."
    elif resp == "Leve, apenas aos esforços":
        return "amarelo", "Fique atento à progressão. Situação controlada no momento."
    else:
        return "verde", "Respiração normal, sem desconfortos importantes."

def opcoes_vomito():
    return [
        "Vômitos com sangue ou sinais de desidratação",
        "Vômitos persistentes sem melhora",
        "Ocasional, com outros sintomas leves",
        "Vômito único e controlado"
    ]

def classificar_vomito(resp):
    if resp == "Vômitos com sangue ou sinais de desidratação":
        return "vermelho", "Urgência médica por risco de hemorragia ou desidratação grave."
    elif resp == "Vômitos persistentes sem melhora":
        return "laranja", "Situação preocupante. Pode indicar gastroenterite ou intolerância alimentar."
    elif resp == "Ocasional, com outros sintomas leves":
        return "amarelo", "Quadro leve. Mantenha hidratação e dieta leve."
    else:
        return "verde", "Vômito isolado sem sinais de risco. Sem necessidade de ação imediata."

def opcoes_trauma_ou_queda():
    return [
        "Trauma grave com sangramento ou inconsciência",
        "Trauma moderado com dor intensa",
        "Queda leve com dor local",
        "Sem dor ou lesão aparente"
    ]

def classificar_trauma_ou_queda(resp):
    if resp == "Trauma grave com sangramento ou inconsciência":
        return "vermelho", "Trauma com sinais neurológicos ou hemorragia requer atendimento urgente."
    elif resp == "Trauma moderado com dor intensa":
        return "laranja", "Lesão pode envolver fratura ou contusão importante. Avaliação médica recomendada."
    elif resp == "Queda leve com dor local":
        return "amarelo", "Possivelmente leve, mas merece observação contínua."
    else:
        return "verde", "Sem indícios de lesão relevante. Mantenha observação."

def opcoes_dor_de_cabeca():
    return [
        "Muito forte, súbita ou com visão turva",
        "Moderada com náusea ou sensibilidade à luz",
        "Leve e intermitente",
        "Rotineira, sem sintomas associados"
    ]

def classificar_dor_de_cabeca(resp):
    if resp == "Muito forte, súbita ou com visão turva":
        return "vermelho", "Pode indicar hemorragia, enxaqueca grave ou crise hipertensiva. Procure atendimento imediato."
    elif resp == "Moderada com náusea ou sensibilidade à luz":
        return "laranja", "Dor pode ser de origem tensional ou migranosa. Consulte um médico se persistir."
    elif resp == "Leve e intermitente":
        return "amarelo", "Dor leve e sem progressão. Observe e evite gatilhos como estresse e sono irregular."
    else:
        return "verde", "Cefaleia rotineira sem sintomas adicionais. Situação tranquila."

def opcoes_dor_abdominal():
    return [
        "Dor intensa e súbita com rigidez na barriga ou vômitos",
        "Dor moderada com febre ou vômito persistente",
        "Dor intermitente ou localizada, sem sinais associados",
        "Dor leve que melhora com repouso"
    ]

def classificar_dor_abdominal(resp):
    if resp == "Dor intensa e súbita com rigidez na barriga ou vômitos":
        return "vermelho", "Pode indicar apendicite, obstrução intestinal ou outra emergência abdominal. Procure hospital."
    elif resp == "Dor moderada com febre ou vômito persistente":
        return "laranja", "Quadro infeccioso ou inflamatório. Precisa de avaliação médica."
    elif resp == "Dor intermitente ou localizada, sem sinais associados":
        return "amarelo", "Provavelmente leve ou funcional. Acompanhe evolução dos sintomas."
    else:
        return "verde", "Dor leve e autolimitada. Sem sinais de preocupação."

def opcoes_convulsoes():
    return [
        "Convulsão ativa ou recente sem recuperação da consciência",
        "Convulsão recente com recuperação parcial, mas com confusão",
        "Histórico de epilepsia com crise controlada",
        "Tremores leves e conscientes, sem perda de consciência"
    ]

def classificar_convulsoes(resp):
    if resp == "Convulsão ativa ou recente sem recuperação da consciência":
        return "vermelho", "Emergência neurológica. Chame socorro imediatamente."
    elif resp == "Convulsão recente com recuperação parcial, mas com confusão":
        return "laranja", "Situação ainda instável. Procure pronto atendimento."
    elif resp == "Histórico de epilepsia com crise controlada":
        return "amarelo", "Situação conhecida. Mantenha rotina de cuidados e medicação."
    else:
        return "verde", "Sem sinais preocupantes. Monitoramento normal."

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
    "Nódulo testicular": (opcoes_nodulo_testicular, classificar_nodulo_testicular),
    "Nódulo mamário": (opcoes_nodulo_mama, classificar_nodulo_mama),
    "Inchaço dos linfonodos": (opcoes_inchaco_linfonodos, classificar_inchaco_linfonodos),
    "Dor nos testículos": (opcoes_dor_testiculos, classificar_dor_testiculos),
    "Sangue no sêmen": (opcoes_sangue_semen, classificar_sangue_semen),
    "Secreção mamilar(fora da amamentação)": (opcoes_secrecao_mamilar, classificar_secrecao_mamilar),
    "Dor na perna e dificuladade para caminhar": (opcoes_dor_perna_caminhar, classificar_dor_perna_caminhar),
    "Dor no peito": (opcoes_dor_no_peito, classificar_dor_no_peito),
    "Trauma na cabeça": (opcoes_trauma_craniano, classificar_trauma_craniano),
    "Manchas anormais na pele": (opcoes_manchas_pele, classificar_manchas_pele),
    "Incontinência urinária": (opcoes_incontinencia_urinaria, classificar_incontinencia_urinaria),
    "Coriza e espirros": (opcoes_coriza_espirros, classificar_coriza_espirros),
    "Incontinência urinária em idosos": (opcoes_incontinencia_idoso,classificar_incontinencia_idoso),
    "Queda em idosos": (opcoes_queda_idoso, classificar_queda_idoso),
    "Delírio em idosos": (opcoes_delirio_idoso, classificar_delirio_idoso),
    "Politrauma": (opcoes_trauma_grave, classificar_trauma_grave),
    "Dor de dente": (opcoes_dor_odontologica, classificar_dor_odontologica),
    "Alteração na audição": (opcoes_alteracao_auditiva, classificar_alteracao_auditiva),
    "Dor de garganta": (opcoes_dor_garganta, classificar_dor_garganta),
    "Mordedura": (opcoes_mordedura, classificar_mordedura),
    "Queimadura": (opcoes_queimaduras, classificar_queimaduras),
    "Ferida não-traumática": (opcoes_ferida_nao_traumatica, classificar_ferida_nao_traumatica),
    "Gases": (opcoes_gases, classificar_gases),
    "Sangramento retal": (opcoes_sangramento_retal, classificar_sangramento_retal),
    "Confusão mental": (opcoes_confusao_mental, classificar_confusao_mental),
    "Perda de consciência": (opcoes_perda_consciencia, classificar_perda_consciencia),
    "Hipotensão ou colapso": (opcoes_hipotensao, classificar_hipotensao),
    "Hipoglicemia": (opcoes_hipoglicemia, classificar_hipoglicemia),
    "Hiperglicemia": (opcoes_hiperglicemia, classificar_hiperglicemia),
    "Temperatura muito baixa": (opcoes_temperatura_baixa, classificar_temperatura_baixa),
    "Dor durante a gravidez": (opcoes_dor_durante_gravidez, classificar_dor_durante_gravidez),
    "Redução dos movimentos fetais": (opcoes_movimentos_fetais, classificar_movimentos_fetais),
    "Trabalho de parto": (opcoes_trabalho_parto, classificar_trabalho_parto),
    "Febre em lactente": (opcoes_febre_lactente, classificar_febre_lactente),
    "Choro persistente em bebê": (opcoes_choro_persistente, classificar_choro_persistente),
    "Icterícia neonatal": (opcoes_ictericia_neonatal, classificar_ictericia_neonatal),
    "Queda em criança": (opcoes_queda_crianca, classificar_queda_crianca),
    "Vômito em criança": (opcoes_vomito_crianca, classificar_vomito_crianca),
    "Diarreia em criança": (opcoes_diarreia_crianca, classificar_diarreia_crianca),
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
    "Convulsão": (opcoes_convulsoes, classificar_convulsoes),
    "Trauma ou queda": (opcoes_trauma_ou_queda, classificar_trauma_ou_queda),
    "Dor nas costas": (opcoes_dor_nas_costas, classificar_dor_nas_costas),
    "Dor abdominal": (opcoes_dor_abdominal, classificar_dor_abdominal),
    "Febre": (opcoes_febre, classificar_febre),
    "Vômito": (opcoes_vomito, classificar_vomito),
    "Dificuldade respiratória": (opcoes_dificuldade_respiratoria, classificar_dificuldade_respiratoria),
    "Dor de cabeça": (opcoes_dor_de_cabeca, classificar_dor_de_cabeca),
    "Lesões na pele": (opcoes_lesoes_na_pele, classificar_lesoes_na_pele),
    "Dor ou olho vermelho": (opcoes_dor_ou_olho_vermelho, classificar_dor_ou_olho_vermelho),
    "Formigamento ou perda de força": (opcoes_formigamento_perda_forca, classificar_formigamento_perda_forca),
    "Sangramento vaginal": (opcoes_sangramento_vaginal, classificar_sangramento_vaginal),
    "Dor ou dificulade ao urinar": (opcoes_dor_ao_urinar, classificar_dor_ao_urinar),
    "Inchaço incomum": (opcoes_inchaco, classificar_inchaco),
    "Comportamento estranho à normalidade": (opcoes_comportamento_estranho, classificar_comportamento_estranho),
    "Sangramento ativo": (opcoes_sangramento_ativo, classificar_sangramento_ativo),
    "Alergia cutânea": (opcoes_alergia_cutanea, classificar_alergia_cutanea),
    "Falta de ar": (opcoes_falta_de_ar, classificar_falta_de_ar)
    }
mapa_sintomas = dict(sorted(mapa_sintomas.items()))


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
    sintomas_disponiveis = list(mapa_sintomas.keys())

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

    # Inicializa variáveis
    if "cores_sintomas" not in st.session_state:
        st.session_state["cores_sintomas"] = []
    if "respostas_usuario" not in st.session_state:
        st.session_state["respostas_usuario"] = {}

    for sintoma in st.session_state.sintomas_escolhidos:
        func_opcoes, func_classificacao = mapa_sintomas[sintoma]
        opcoes = func_opcoes()
        escolha = st.radio(f"{sintoma}:", opcoes, key=f"opcao_{sintoma}")
        st.session_state["respostas_usuario"][sintoma] = escolha

    # AQUI COMEÇA O BLOCO DO BOTÃO
    if st.button("Ver resultado", key="ver_resultado"):

        st.session_state["cores_sintomas"] = []
        st.markdown("---")

        for sintoma in st.session_state.sintomas_escolhidos:
            func_opcoes, func_classificacao = mapa_sintomas[sintoma]
            escolha = st.session_state["respostas_usuario"][sintoma]
            cor, motivo = func_classificacao(escolha)
            st.session_state["cores_sintomas"].append(cor)

            st.markdown(f"### {sintoma}")
            st.markdown(f"**🔍 Motivo:** {motivo}")
            st.markdown("---")

        cor_final = classificar_combinacao(
            sintomas=[s.lower() for s in st.session_state.sintomas_escolhidos],
            cores=st.session_state["cores_sintomas"]
        )

        grupos_paciente = st.session_state.get("grupos_risco_refinados", [])
        gravidez = str(st.session_state.get("gravida", "")).strip().lower() in ["sim", "true", "1"]

        sistemas_por_fatores = gerar_sistemas_afetados_por_fatores(
            idade=st.session_state.get("idade"),
            imc_class=st.session_state.get("classificacao_imc"),
            gravida=gravidez,
            condicoes_brutas=grupos_paciente
        )

        sistemas_secundarios = []
        for grupo in grupos_paciente:
            sistemas_secundarios += sistemas_afetados_secundariamente(grupo)

        sistemas_afetados = set(sistemas_por_fatores + sistemas_secundarios)

        sintoma_para_sistema = {
            normalizar(sintoma): sistema
            for sistema, lista in sistemas_sintomas.items()
            for sintoma in lista
        }

        ajuste = verificar_se_deve_subir_cor(
            sintomas_escolhidos=st.session_state.sintomas_escolhidos,
            sistemas_afetados=sistemas_afetados,
            sintoma_para_sistema=sintoma_para_sistema
        )


        if ajuste == True:
            cor_final = aumentar_cor_em_1_nivel(cor_final)

        emoji_cor = {
            "verde": "🟢",
            "amarelo": "🟡",
            "laranja": "🟠",
            "vermelho": "🔴"
        }

        st.success(f"🩺 Gravidade estimada: **{cor_final.upper()}**")

        st.markdown("---")
        st.subheader("📘 Legenda de Gravidade")
        st.markdown("""
- 🔴 **VERMELHO:** Situação crítica. Procure atendimento médico imediatamente.
- 🟠 **LARANJA:** Caso urgente. Necessita avaliação rápida em unidade de saúde.
- 🟡 **AMARELO:** Gravidade moderada. Requer atenção, mas pode aguardar avaliação.
- 🟢 **VERDE:** Baixa gravidade. Pode observar os sintomas ou procurar atendimento não urgente.
""")
