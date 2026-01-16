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


# 1) TONTURA / SENSAÇÃO DE DESMAIO
FLUXOS[normalizar("Tontura")] = {
    "label": "Tontura",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Tontura com desmaio recente ou queda": 4.0,
                "Tontura intensa, não consegue ficar em pé": 3.0,
                "Tontura moderada principalmente ao levantar": 1.5,
                "Tontura leve, episódica": 0.5
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito, em minutos": 1.2,
                "Em algumas horas": 0.6,
                "Dias ou semanas": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados / fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Dor no peito ou falta de ar": 2.0,
                "Palpitações ou batimento irregular": 1.5,
                "Déficit neurológico (fraqueza, fala embolada, visão dupla)": 2.5,
                "Rigidez de nuca ou febre alta": 1.5,
                "Trauma recente na cabeça": 2.0,
                "Queda de pressão conhecida (hipotensão)": 1.0,
                "Suspeita de hipoglicemia (diabetes, tremor/sudorese)": 1.0,
                "Desidratação (vômitos/diarreia, pouca urina)": 0.8,
                "Uso de álcool, sedativos ou drogas": 0.7,
                "Gravidez": 0.6,
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Tontura com desmaio recente ou queda"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Dor no peito ou falta de ar"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Déficit neurológico (fraqueza, fala embolada, visão dupla)"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Trauma recente na cabeça"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 1) CHIADO NO PEITO (SIBILOS)
FLUXOS[normalizar("Chiado no peito")] = {
    "label": "Chiado no peito",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Chiado intenso, dificuldade para falar": 4.0,
                "Chiado moderado, falta de ar em repouso": 2.5,
                "Chiado leve apenas ao esforço": 1.0,
                "Chiado ocasional, sem falta de ar": 0.4
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito, em minutos": 1.5,
                "Horas": 0.8,
                "Dias": 0.3
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de asma/bronquite": 0.6,
                "Uso de inalador sem melhora": 0.6,
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Chiado intenso, dificuldade para falar"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}
# 4) INTOLERÂNCIA TÉRMICA
FLUXOS[normalizar("Intolerância térmica")] = {
    "label": "Intolerância térmica",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade/impacto:",
            "tipo": "radio",
            "opcoes": {
                "Desconforto intenso que impede atividades": 2.5,
                "Desconforto moderado": 1.2,
                "Leve/ambiental (tolerável)": 0.3
            }
        },
        {
            "id": "predominio",
            "label": "Predomínio:",
            "tipo": "radio",
            "opcoes": {
                "Ao calor": 0.4,
                "Ao frio": 0.4
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (horas/dias)": 0.6,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Temperatura ≥ 40 °C ou confusão": 3.0,
                "Pele muito quente e seca": 1.5,
                "Suor excessivo/palpitações/perda de peso": 0.8,
                "Pele seca/constipação/ganho de peso": 0.8,
                "Desidratação (pouca urina, vômitos/diarreia)": 1.0,
                "Uso de medicamentos (betabloqueadores/anticolinérgicos/hormônios)": 0.4,
                "Menopausa/ondas de calor": 0.3
            }
        }
    ],
    "regras_excecao": [
        {"se": {"riscos": "Temperatura ≥ 40 °C ou confusão"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Desidratação (pouca urina, vômitos/diarreia)"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}
# 5) MOVIMENTOS INVOLUNTÁRIOS
FLUXOS[normalizar("Movimentos involuntários")] = {
    "label": "Movimentos involuntários",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade/impacto:",
            "tipo": "radio",
            "opcoes": {
                "Movimentos generalizados com queda ou confusão": 4.0,
                "Movimentos intensos que impedem tarefas": 2.5,
                "Movimentos leves/intermitentes": 0.5
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (segundos/minutos)": 1.0,
                "Dias": 0.4,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "tipo",
            "label": "Tipo principal:",
            "tipo": "radio",
            "opcoes": {
                "Tremor (repouso/ação)": 0.4,
                "Soluços musculares breves (mioclonia)": 0.6,
                "Tiques (piscar/gestos repetitivos)": 0.3
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Alteração de consciência/mordedura de língua/urina": 3.0,
                "Febre e rigidez": 2.0,
                "Trauma craniano recente": 2.0,
                "Uso de neurolépticos/metoclopramida/lítio": 1.2,
                "Álcool/drogas": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Movimentos generalizados com queda ou confusão"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Alteração de consciência/mordedura de língua/urina"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Febre e rigidez"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Trauma craniano recente"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Uso de neurolépticos/metoclopramida/lítio"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 2) TOSSE COM SANGUE (HEMOPTISE)
FLUXOS[normalizar("Tosse com sangue")] = {
    "label": "Tosse com sangue ",
    "perguntas": [
        {
            "id": "volume",
            "label": "Quantidade de sangue:",
            "tipo": "radio",
            "opcoes": {
                "Grande volume (≥ 200 ml)": 4.0,
                "Moderado (até 200 ml)": 2.5,
                "Pequeno volume (estrias de sangue)": 1.0
            }
        },
        {
            "id": "duracao",
            "label": "Duração/recorrência:",
            "tipo": "radio",
            "opcoes": {
                "Persistente há dias": 1.0,
                "Episódico, apenas uma vez": 0.4
            }
        },
        {
            "id": "riscos",
            "label": "Fatores associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Histórico de tuberculose/câncer pulmonar": 1.0,
                "Febre e perda de peso": 0.8,
                "Tabagismo intenso": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"volume": "Grande volume (≥ 200 ml)"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 3) ROUQUIDÃO SÚBITA OU PERSISTENTE
FLUXOS[normalizar("Rouquidão súbita ou persistente")] = {
    "label": "Rouquidão súbita ou persistente",
    "perguntas": [
        {
            "id": "duracao",
            "label": "Duração da rouquidão:",
            "tipo": "radio",
            "opcoes": {
                "Mais de 3 semanas": 2.5,
                "Entre 1–3 semanas": 1.0,
                "Menos de 1 semana": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Dificuldade para respirar": 2.0,
                "Dor ou dificuldade para engolir": 1.5,
                "Sangue na saliva": 1.5,
                "Tabagismo/álcool em excesso": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": "Dificuldade para respirar"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 4) EXPECTORAÇÃO COM ODOR FÉTIDO
FLUXOS[normalizar("Expectoração com odor fétido")] = {
    "label": "Expectoração com odor fétido",
    "perguntas": [
        {
            "id": "quantidade",
            "label": "Quantidade de secreção:",
            "tipo": "radio",
            "opcoes": {
                "Grande volume purulento": 2.5,
                "Moderado": 1.0,
                "Pequeno volume": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Febre alta": 1.5,
                "Dor torácica": 1.2,
                "Perda de peso": 0.8,
                "Halitose": 0.4
            }
        }
    ],
    "mapeamento_cor": [
        (4.0, "vermelho"),
        (2.0, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 5) DORMÊNCIA EM PARTE DO CORPO
FLUXOS[normalizar("Dormência em parte do corpo")] = {
    "label": "Dormência em parte do corpo",
    "perguntas": [
        {
            "id": "local",
            "label": "Local da dormência:",
            "tipo": "radio",
            "opcoes": {
                "Um lado inteiro do corpo (hemicorpo)": 3.0,
                "Braço ou perna isolados": 2.0,
                "Dedos ou extremidades apenas": 0.6
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (em segundos/minutos)": 2.0,
                "Progressivo (horas/dias)": 1.0,
                "Intermitente": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Dificuldade para falar": 2.0,
                "Alteração de visão": 1.5,
                "Fraqueza em membro": 1.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"local": "Um lado inteiro do corpo (hemicorpo)"}, "min_cor": "vermelho"},
        {"se": {"inicio": "Súbito (em segundos/minutos)"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}


# 8) VISÃO DUPLA (DIPLOPIA)
FLUXOS[normalizar("Visão dupla ")] = {
    "label": "Visão dupla ",
    "perguntas": [
        {
            "id": "inicio",
            "label": "Início da diplopia:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 2.5,
                "Progressivo (dias+)": 1.0,
                "Intermitente": 0.6
            }
        },
        {
            "id": "associados",
            "label": "Sinais/sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Pálpebra caída (ptose) ou desvio ocular": 1.5,
                "Dor de cabeça intensa": 1.0,
                "Fraqueza/fala alterada": 2.0
            }
        },
        {
            "id": "trauma",
            "label": "História de trauma ocular/craniano recente:",
            "tipo": "radio",
            "opcoes": {
                "Sim": 1.5,
                "Não": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"inicio": "Súbito (minutos/horas)"}, "min_cor": "laranja"},
        {"se": {"associados": "Fraqueza/fala alterada"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 9) PELE FRIA E ÚMIDA ASSOCIADA A MAL-ESTAR
FLUXOS[normalizar("Pele fria e úmida associada a mal-estar")] = {
    "label": "Pele fria e úmida associada a mal-estar",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Quadro atual:",
            "tipo": "radio",
            "opcoes": {
                "Mal-estar intenso com tontura/pré-síncope": 2.5,
                "Náusea, sudorese e fraqueza": 1.5,
                "Leve indisposição": 0.4
            }
        },
        {
            "id": "dorpeito",
            "label": "Dor/pressão no peito associada:",
            "tipo": "radio",
            "opcoes": {
                "Sim": 2.0,
                "Não": 0.0
            }
        },
        {
            "id": "pressao",
            "label": "Pressão arterial medida (se souber):",
            "tipo": "radio",
            "opcoes": {
                "Muito baixa (hipotensão)": 2.0,
                "Desconhecida/normal": 0.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"dorpeito": "Sim"}, "min_cor": "vermelho"},
        {"se": {"pressao": "Muito baixa (hipotensão)"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 10) VÔMITO COM SANGUE (HEMATÊMESE)
FLUXOS[normalizar("Vômito com sangue ")] = {
    "label": "Vômito com sangue",
    "perguntas": [
        {
            "id": "volume",
            "label": "Volume de sangue no vômito:",
            "tipo": "radio",
            "opcoes": {
                "Grande volume/“em jato”": 4.0,
                "Moderado": 2.5,
                "Traços/estrias de sangue": 1.0
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Fezes pretas (melena) ou sangue nas fezes": 1.5,
                "Tontura ou desmaio": 1.5,
                "Dor abdominal intensa": 1.0,
                "Uso de AAS/AINEs/álcool": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"volume": "Grande volume/“em jato”"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 11) AUMENTO DO VOLUME ABDOMINAL (DISTENSÃO)
FLUXOS[normalizar("Aumento do volume abdominal ")] = {
    "label": "Aumento do volume abdominal",
    "perguntas": [
        {
            "id": "instalacao",
            "label": "Instalação da distensão:",
            "tipo": "radio",
            "opcoes": {
                "Súbita (horas)": 2.0,
                "Dias": 1.0,
                "Semanas+": 0.6
            }
        },
        {
            "id": "sintomas",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Vômitos biliosos/fecaloides": 2.0,
                "Ausência de evacuação/eliminações": 1.5,
                "Febre": 1.0,
                "Dor abdominal intensa": 1.5
            }
        },
        {
            "id": "riscos",
            "label": "Condições de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Cirurgia abdominal recente": 1.0,
                "Hérnia conhecida": 0.8,
                "Doença hepática conhecida": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"sintomas": "Vômitos biliosos/fecaloides"}, "min_cor": "vermelho"},
        {"se": {"sintomas": "Ausência de evacuação/eliminações"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 12) SANGUE NA URINA (HEMATÚRIA)
FLUXOS[normalizar("Sangue na urina ")] = {
    "label": "Sangue na urina",
    "perguntas": [
        {
            "id": "intensidade",
            "label": "Intensidade da hematúria:",
            "tipo": "radio",
            "opcoes": {
                "Urina vermelha/“colorida” a olho nu": 2.5,
                "Apenas traços (suspeita microscópica)": 0.8
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Dor lombar/cólica": 1.5,
                "Febre/calafrios": 1.5,
                "Coágulos ao urinar": 1.5,
                "Dor/ardor para urinar": 1.0
            }
        },
        {
            "id": "fatores",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Uso de anticoagulantes": 1.0,
                "Histórico de cálculos": 0.8,
                "Trauma abdominal/perineal": 1.0
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": "Coágulos ao urinar"}, "min_cor": "laranja"},
        {"se": {"associados": "Febre/calafrios"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}
# 2) DOR E RIGIDEZ ARTICULAR
FLUXOS[normalizar("Dor e rigidez articular")] = {
    "label": "Dor e rigidez articular",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade e impacto:",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa, não consegue mover a articulação": 3.5,
                "Dor moderada com limitação": 2.0,
                "Dor leve, melhora com repouso": 0.6
            }
        },
        {
            "id": "duracao",
            "label": "Duração/início:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 0.8,
                "Dias": 0.4,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "padrao",
            "label": "Padrão de acometimento:",
            "tipo": "radio",
            "opcoes": {
                "Uma articulação (monoarticular)": 0.8,
                "Várias articulações": 0.4
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Rigidez matinal ≥ 60 min": 0.8,
                "Inchaço evidente": 0.8,
                "Febre": 1.2,
                "Articulação muito quente/vermelha": 2.5,
                "Trauma recente": 1.0,
                "Ferida/punção recente na articulação": 1.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"riscos": "Articulação muito quente/vermelha"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Ferida/punção recente na articulação"}, "min_cor": "vermelho"},
        {"se": {"padrao": "Uma articulação (monoarticular)", "riscos": "Febre"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Trauma recente"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}
# 3) EDEMA / INCHAÇO
FLUXOS[normalizar("Edema/Inchaço")] = {
    "label": "Edema/Inchaço",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade/impacto:",
            "tipo": "radio",
            "opcoes": {
                "Inchaço súbito e doloroso": 3.0,
                "Inchaço moderado que piora ao longo do dia": 1.5,
                "Inchaço leve/ocasional": 0.4
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (horas)": 1.0,
                "Dias": 0.5,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "local",
            "label": "Localização do inchaço:",
            "tipo": "radio",
            "opcoes": {
                "Uma perna/braço (unilateral)": 1.2,
                "Ambas as pernas (bilateral)": 0.6,
                "Face/lábios": 2.0
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Dor em panturrilha": 2.5,
                "Falta de ar súbita ou dor no peito": 2.5,
                "Vermelhidão e calor local": 1.5,
                "Febre": 1.0,
                "Piora ao deitar/ortopneia": 1.0,
                "Uso recente de medicamentos (hormônios, AINEs, bloqueadores de cálcio)": 0.4,
                "Picada/contato alérgico": 0.6,
                "Gravidez": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"local": "Face/lábios"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Dor em panturrilha"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Falta de ar súbita ou dor no peito"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Vermelhidão e calor local", "quadro": "Inchaço súbito e doloroso"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 13) CORRIMENTO URETRAL ANORMAL
FLUXOS[normalizar("Corrimento uretral anormal")] = {
    "label": "Corrimento uretral anormal",
    "perguntas": [
        {
            "id": "aspecto",
            "label": "Aspecto do corrimento:",
            "tipo": "radio",
            "opcoes": {
                "Purulento (espesso, amarelado/esverdeado)": 2.5,
                "Clareado/transparente": 1.0,
                "Pequena secreção esporádica": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Ardência ao urinar": 1.5,
                "Febre": 1.5,
                "Dor testicular": 1.5,
                "Úlcera/lesão genital": 1.0
            }
        },
        {
            "id": "riscos",
            "label": "Histórico:",
            "tipo": "multiselect",
            "opcoes": {
                "Relação sexual desprotegida recente": 1.5,
                "Parceiros múltiplos": 1.0,
                "IST prévia": 0.8
            }
        }
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 14) CORRIMENTO VAGINAL FÉTIDO
FLUXOS[normalizar("Corrimento vaginal fétido")] = {
    "label": "Corrimento vaginal fétido",
    "perguntas": [
        {
            "id": "odor",
            "label": "Intensidade do odor:",
            "tipo": "radio",
            "opcoes": {
                "Odor muito forte/fétido": 2.5,
                "Odor perceptível, mas não intenso": 1.0,
                "Sem odor significativo": 0.2
            }
        },
        {
            "id": "aspecto",
            "label": "Aspecto do corrimento:",
            "tipo": "radio",
            "opcoes": {
                "Espesso e purulento": 1.5,
                "Acre/branco esfarelado": 1.0,
                "Aquoso": 0.4
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Febre/dor abdominal": 2.0,
                "Prurido vaginal": 1.0,
                "Dor pélvica": 1.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"associados": "Febre/dor abdominal"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (4.5, "vermelho"),
        (2.5, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 15) DOR PÉLVICA CÍCLICA
FLUXOS[normalizar("Dor pélvica cíclica")] = {
    "label": "Dor pélvica cíclica",
    "perguntas": [
        {
            "id": "intensidade",
            "label": "Intensidade da dor:",
            "tipo": "radio",
            "opcoes": {
                "Dor incapacitante (não realiza atividades)": 2.5,
                "Dor moderada (atrapalha atividades)": 1.5,
                "Dor leve suportável": 0.6
            }
        },
        {
            "id": "ciclo",
            "label": "Relação com ciclo menstrual:",
            "tipo": "radio",
            "opcoes": {
                "Sempre presente em menstruação": 1.5,
                "Ocasional, variável": 0.6,
                "Sem relação clara": 0.2
            }
        },
        {
            "id": "associados",
            "label": "Sintomas associados:",
            "tipo": "multiselect",
            "opcoes": {
                "Sangramento intenso": 1.5,
                "Febre": 1.0,
                "Infertilidade/diagnóstico de endometriose": 0.8
            }
        }
    ],
    "mapeamento_cor": [
        (3.5, "vermelho"),
        (2.0, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 1) DOR MUSCULAR
FLUXOS[normalizar("Dor muscular")] = {
    "label": "Dor muscular",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade e impacto:",
            "tipo": "radio",
            "opcoes": {
                "Dor intensa, desproporcional, pior à palpação ou movimento": 3.5,
                "Dor moderada que limita atividades": 2.0,
                "Dor leve após esforço": 0.8,
                "Desconforto muscular ocasional": 0.3
            }
        },
        {
            "id": "inicio",
            "label": "Início dos sintomas:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (minutos/horas)": 1.0,
                "Dias": 0.4,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "local",
            "label": "Distribuição da dor:",
            "tipo": "radio",
            "opcoes": {
                "Difusa (vários grupos musculares)": 0.8,
                "Localizada (um ponto/segmento)": 0.4
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados / fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Trauma importante recente": 2.0,
                "Esforço extenuante/treino intenso": 0.8,
                "Edema rígido/progressivo na região (empastamento)": 2.0,
                "Fraqueza progressiva do membro": 1.8,
                "Urina escura (cor de coca-cola)": 2.5,
                "Febre ou mal-estar geral": 1.2,
                "Dor com vermelhidão e calor local": 1.5,
                "Uso de estatinas/antivirais/antipsicóticos": 0.8,
                "Picada animal/inseto recente": 0.6,
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Dor intensa, desproporcional, pior à palpação ou movimento"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Urina escura (cor de coca-cola)"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Edema rígido/progressivo na região (empastamento)"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Fraqueza progressiva do membro"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Trauma importante recente"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}







# 20) ATAQUES DE PÂNICO
FLUXOS[normalizar("Ataques de pânico")] = {
    "label": "Ataques de pânico",
    "perguntas": [
        {
            "id": "frequencia",
            "label": "Frequência das crises:",
            "tipo": "radio",
            "opcoes": {
                "Múltiplas vezes na semana": 2.0,
                "Uma vez por semana": 1.0,
                "Episódico raro": 0.4
            }
        },
        {
            "id": "sintomas",
            "label": "Sintomas presentes durante crise:",
            "tipo": "multiselect",
            "opcoes": {
                "Sensação de morte iminente": 1.5,
                "Palpitações/tremores": 1.0,
                "Falta de ar": 1.0,
                "Tontura/desmaio": 1.0
            }
        }
    ],
    "mapeamento_cor": [
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# 21) IDEAÇÃO SUICIDA
FLUXOS[normalizar("Ideação suicida")] = {
    "label": "Ideação suicida",

{
    "id": "mensagem_apoio",
    "label": "Mensagem de apoio",
    "tipo": "texto",
    "valor": (
        "Você não está sozinho. O que você está sentindo é importante e merece atenção.\n\n"
        "Se estiver em risco ou se sentindo sobrecarregado, procure ajuda agora:\n"
        "• CVV – Centro de Valorização da Vida: 188 (24h, gratuito)\n"
        "• Emergência: 190 ou 192\n\n"
        "Se puder, converse com alguém de confiança ou busque apoio profissional."
    )
}

    "perguntas": [
        {
            "id": "ideacao",
            "label": "Pensamentos suicidas:",
            "tipo": "radio",
            "opcoes": {
                "Plano ativo de se machucar": 4.0,
                "Pensamentos frequentes sem plano": 3.0,
                "Pensamentos ocasionais": 1.5
            }
        },
        {
            "id": "historico",
            "label": "Histórico:",
            "tipo": "multiselect",
            "opcoes": {
                "Tentativa prévia": 2.0,
                "Transtorno psiquiátrico diagnosticado": 1.5,
                "Abuso de álcool/drogas": 1.0
            }
        },
        {
            "id": "rede",
            "label": "Rede de apoio:",
            "tipo": "radio",
            "opcoes": {
                "Isolamento social": 1.5,
                "Apoio familiar/pessoal presente": 0.0
            }
        }
    ],

    "regras_excecao": [
        {"se": {"ideacao": "Plano ativo de se machucar"}, "min_cor": "vermelho"}
    ],

    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# =========================
# PACOTE DE FLUXOS CRÍTICOS
# =========================

# 1) ACIDENTE ELÉTRICO
FLUXOS[normalizar("Acidente elétrico")] = {
    "label": "Acidente elétrico",
    "perguntas": [
        {
            "id": "mecanismo",
            "label": "Qual foi a situação principal?",
            "tipo": "radio",
            "opcoes": {
                "Choque de alta tensão (>1000V) ou raio": 4.0,
                "Choque de média tensão (110–380V) com tempo de contato prolongado": 2.5,
                "Choque breve de baixa/média tensão sem queda": 1.0,
                "Formigamento leve sem lesão aparente": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados (selecione os que tiver):",
            "tipo": "checkbox",
            "opcoes": {
                "Perda de consciência, confusão ou desmaio": 2.0,
                "Dor no peito, palpitação ou falta de ar": 1.8,
                "Queimaduras de entrada/saída": 1.5,
                "Quedas ou trauma associado": 1.2,
                "Espasmos musculares persistentes": 0.8
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu o evento?",
            "tipo": "radio",
            "opcoes": {
                "Agora ou < 1 hora": 1.0,
                "1 a 24 horas": 0.6,
                "Há > 24 horas": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Algum fator de risco se aplica?",
            "tipo": "multiselect",
            "opcoes": {
                "Áreas molhadas (banho/piscina/chuva)": 0.7,
                "Gravidez": 0.6,
                "Idade ≤ 4 anos": 0.8,
                "Idade ≥ 67 anos": 0.6,
                "Cardiopatia conhecida ou marca-passo": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"mecanismo": "Choque de alta tensão (>1000V) ou raio"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Perda de consciência, confusão ou desmaio", "Dor no peito, palpitação ou falta de ar"]}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Queimaduras de entrada/saída"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 2) AFOGAMENTO
FLUXOS[normalizar("Afogamento")] = {
    "label": "Afogamento",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a pessoa agora?",
            "tipo": "radio",
            "opcoes": {
                "Inconsciente ou com respiração anormal": 5.0,
                "Tosse intensa, falta de ar ou cianose": 3.0,
                "Tosse leve e náusea, respiração normal": 1.2,
                "Assustada, sem sintomas respiratórios": 0.3
            }
        },
        {
            "id": "tempo",
            "label": "Tempo submerso aproximado:",
            "tipo": "radio",
            "opcoes": {
                "≥ 1 minuto": 2.0,
                "< 1 minuto": 0.8,
                "Não sabe": 0.8
            }
        },
        {
            "id": "meio",
            "label": "Meio onde ocorreu:",
            "tipo": "radio",
            "opcoes": {
                "Mar/rio/represa": 0.6,
                "Piscina": 0.4,
                "Banheira/caixa d’água": 0.3
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≤ 4 anos": 0.8,
                "Idade ≥ 67 anos": 0.6,
                "Trauma de cabeça ou coluna na água": 1.5,
                "Ingestão de álcool/drogas": 0.5
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Inconsciente ou com respiração anormal"}, "min_cor": "vermelho"},
        {"se": {"riscos": ["Trauma de cabeça ou coluna na água"]}, "min_cor": "vermelho"},
        {"se": {"quadro": "Tosse intensa, falta de ar ou cianose"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.5, "amarelo"),
        (0.0, "verde")
    ]
}

# 4) FRATURA OU LUXAÇÃO
FLUXOS[normalizar("Fratura ou luxação")] = {
    "label": "Fratura ou luxação",
    "perguntas": [
        {
            "id": "gravidade",
            "label": "Situação principal:",
            "tipo": "radio",
            "opcoes": {
                "Deformidade evidente/encurtamento ou fratura exposta": 3.5,
                "Dor intensa com incapacidade de apoio/uso": 2.2,
                "Dor moderada com inchaço localizado": 1.0,
                "Dor leve sem limitação": 0.2
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Formigamento/fraqueza distal": 1.2,
                "Estalo ou crepitação": 0.8,
                "Hematoma extenso": 0.6
            }
        },
        {
            "id": "tempo",
            "label": "Quando ocorreu?",
            "tipo": "radio",
            "opcoes": {
                "Agora ou < 24h": 0.8,
                "1–7 dias": 0.4,
                "> 7 dias": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≥ 67 anos": 0.6,
                "Osteoporose/uso crônico de corticoide": 0.6,
                "Uso de anticoagulante": 0.8
            }
        }
    ],
    "regras_excecao": [
        {"se": {"gravidade": "Deformidade evidente/encurtamento ou fratura exposta"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Formigamento/fraqueza distal"]}, "min_cor": "laranja"},
        {"se": {"gravidade": "Dor intensa com incapacidade de apoio/uso"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (2.8, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 5) INSOLAÇÃO
FLUXOS[normalizar("Insolação")] = {
    "label": "Insolação",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Quadro principal:",
            "tipo": "radio",
            "opcoes": {
                "Alteração de consciência ou convulsão": 4.0,
                "Temperatura corporal muito alta (pele quente e seca)": 3.0,
                "Dor de cabeça intensa, tontura, náusea": 1.5,
                "Mal-estar leve após sol": 0.4
            }
        },
        {
            "id": "exposicao",
            "label": "Exposição ao calor:",
            "tipo": "radio",
            "opcoes": {
                "Prolongada/atividade intensa sob sol": 1.2,
                "Moderada": 0.6,
                "Breve": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≤ 4 anos": 0.8,
                "Idade ≥ 67 anos": 0.8,
                "Doenças cardíacas/renais": 0.6,
                "Diuréticos/anticolinérgicos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Alteração de consciência ou convulsão"}, "min_cor": "vermelho"},
        {"se": {"quadro": "Temperatura corporal muito alta (pele quente e seca)"}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (5.5, "vermelho"),
        (3.0, "laranja"),
        (1.4, "amarelo"),
        (0.0, "verde")
    ]
}

# 6) EXAUSTÃO POR CALOR
FLUXOS[normalizar("Exaustão por calor")] = {
    "label": "Exaustão por calor",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Sintomas principais:",
            "tipo": "radio",
            "opcoes": {
                "Fraqueza intensa, tontura com pré-síncope": 2.2,
                "Cãibras, náusea/vômito, cefaleia": 1.5,
                "Cansaço e suor excessivo": 0.8,
                "Desconforto leve": 0.2
            }
        },
        {
            "id": "duracao",
            "label": "Duração da exposição ao calor:",
            "tipo": "radio",
            "opcoes": {
                "≥ 2 horas de atividade no calor": 1.0,
                "30–120 min": 0.6,
                "< 30 min": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Desidratação provável": 0.8,
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6,
                "Doença cardíaca/renal": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Fraqueza intensa, tontura com pré-síncope"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (3.8, "vermelho"),
        (2.2, "laranja"),
        (1.0, "amarelo"),
        (0.0, "verde")
    ]
}

# 7) EXPOSIÇÃO A FUMAÇA OU INCÊNDIO
FLUXOS[normalizar("Exposição a fumaça ou incêndio")] = {
    "label": "Exposição a fumaça ou incêndio",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Como está a respiração?",
            "tipo": "radio",
            "opcoes": {
                "Falta de ar importante, rouquidão ou confusão": 3.5,
                "Tosse persistente e dor no peito": 2.0,
                "Irritação leve de olhos/garganta": 0.8,
                "Sem sintomas respiratórios": 0.2
            }
        },
        {
            "id": "exposicao",
            "label": "Exposição:",
            "tipo": "radio",
            "opcoes": {
                "Ambiente fechado/inalação intensa": 2.0,
                "Ambiente aberto": 0.6
            }
        },
        {
            "id": "sinais",
            "label": "Sinais associados:",
            "tipo": "checkbox",
            "opcoes": {
                "Fuligem no nariz/boca": 1.5,
                "Queimadura facial/pelos nasais chamuscados": 1.5,
                "Náusea, dor de cabeça (suspeita de CO)": 1.2
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6,
                "Asma/Doença pulmonar": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Falta de ar importante, rouquidão ou confusão"}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Fuligem no nariz/boca", "Queimadura facial/pelos nasais chamuscados"]}, "min_cor": "vermelho"},
        {"se": {"sinais": ["Náusea, dor de cabeça (suspeita de CO)"]}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.4, "amarelo"),
        (0.0, "verde")
    ]
}

# 8) EXPOSIÇÃO A PRODUTOS QUÍMICOS
FLUXOS[normalizar("Exposição a produtos químicos")] = {
    "label": "Exposição a produtos químicos",
    "perguntas": [
        {
            "id": "via",
            "label": "Via de exposição:",
            "tipo": "radio",
            "opcoes": {
                "Inalação ou ingestão": 3.0,
                "Contato ocular": 2.0,
                "Contato cutâneo": 1.0
            }
        },
        {
            "id": "sintomas",
            "label": "Sintomas atuais:",
            "tipo": "checkbox",
            "opcoes": {
                "Falta de ar, chiado ou dor no peito": 2.0,
                "Vômitos persistentes ou sonolência": 1.8,
                "Dor intensa/queimação em olhos/pele": 1.5,
                "Irritação leve em pele/olhos": 0.6
            }
        },
        {
            "id": "agente",
            "label": "Tipo de agente (se souber):",
            "tipo": "radio",
            "opcoes": {
                "Corrosivo/ácido/base forte/organofosforado": 2.5,
                "Solvente/álcool/limpeza comum": 0.8,
                "Desconhecido": 1.0
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Exposição prolongada/ambiente fechado": 0.8,
                "Idade ≤ 4 anos": 0.6,
                "Idade ≥ 67 anos": 0.6,
                "Asma/Doença pulmonar": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"via": "Inalação ou ingestão"}, "min_cor": "laranja"},
        {"se": {"agente": "Corrosivo/ácido/base forte/organofosforado"}, "min_cor": "vermelho"},
        {"se": {"sintomas": ["Falta de ar, chiado ou dor no peito", "Vômitos persistentes ou sonolência"]}, "min_cor": "vermelho"}
    ],
    "mapeamento_cor": [
        (6.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}

# 9) DESIDRATAÇÃO
FLUXOS[normalizar("Desidratação")] = {
    "label": "Desidratação",
    "perguntas": [
        {
            "id": "quadro",
            "label": "Gravidade aparente:",
            "tipo": "radio",
            "opcoes": {
                "Letargia, confusão ou olhos muito fundos": 3.0,
                "Tontura ao levantar, boca muito seca, diurese reduzida": 1.8,
                "Sede aumentada e urina amarela escura": 1.0,
                "Sede leve": 0.3
            }
        },
        {
            "id": "perdas",
            "label": "Perdas recentes:",
            "tipo": "checkbox",
            "opcoes": {
                "Vômitos frequentes": 1.2,
                "Diarreia intensa": 1.2,
                "Febre": 0.6,
                "Suor excessivo": 0.6
            }
        },
        {
            "id": "ingestao",
            "label": "Consegue ingerir líquidos?",
            "tipo": "radio",
            "opcoes": {
                "Não ou vomita tudo": 1.8,
                "Pouco": 0.8,
                "Sim": 0.2
            }
        },
        {
            "id": "riscos",
            "label": "Fatores de risco:",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≤ 4 anos": 0.8,
                "Idade ≥ 67 anos": 0.8,
                "Doença renal/cardiaca": 0.4
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Letargia, confusão ou olhos muito fundos"}, "min_cor": "vermelho"},
        {"se": {"ingestao": "Não ou vomita tudo"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (2.4, "laranja"),
        (1.2, "amarelo"),
        (0.0, "verde")
    ]
}


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
        },
        {
            "id": "condicoes",
            "label": "Condições associadas (se houver):",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≥ 67 anos": 0.8
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
        },
            {
            "id": "fatores_risco",
            "label": "Condições associadas (se houver):",
            "tipo": "multiselect",
            "opcoes": {
                "Idade ≥ 67 anos": 2.0,
                "Idade ≤ 6 anos": 0.7
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
                "Idade ≥ 67 anos": 0.6,
                "Idade ≤ 6 anos": 0.9
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
                "Viagem recente/água/ alimento suspeito": 0.6,
                "Idade ≤ 6 anos": 0.7
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



# === SANGRAMENTO GASTROINTESTINAL (unificado: inclui sangue vivo e fezes pretas) ===
ROTULO = "Sangramento gastrointestinal"
SID = normalizar(ROTULO)

FLUXOS[SID] = {
    "label": ROTULO,
    "perguntas": [
        {
            "id": "quadro",
            "label": "Intensidade/impacto:",
            "tipo": "radio",
            "opcoes": {
                "Sangramento volumoso com tontura/desmaio": 4.0,
                "Sangramento moderado e contínuo": 2.5,
                "Fezes pretas (melena) ou sangue misturado às fezes": 1.8,
                "Sangue leve apenas no papel": 0.6
            }
        },
        {
            "id": "inicio",
            "label": "Início:",
            "tipo": "radio",
            "opcoes": {
                "Súbito (horas)": 1.0,
                "Dias": 0.5,
                "Semanas ou mais": 0.2
            }
        },
        {
            "id": "caracteristica",
            "label": "Característica do sangue:",
            "tipo": "radio",
            "opcoes": {
                "Vermelho vivo (pelo ânus)": 1.5,
                "Preto/borra de café (melena)": 1.5,
                "Coágulos": 1.0
            }
        },
        {
            "id": "riscos",
            "label": "Sinais associados / fatores:",
            "tipo": "multiselect",
            "opcoes": {
                "Vômito com sangue": 3.0,
                "Tontura/palidez/sudorese": 2.5,
                "Dor abdominal forte persistente": 1.2,
                "Uso de anticoagulante/AAS": 1.5,
                "Doença hepática/cirrose": 1.2,
                "Idade ≥ 67 anos": 0.6
            }
        }
    ],
    "regras_excecao": [
        {"se": {"quadro": "Sangramento volumoso com tontura/desmaio"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Vômito com sangue"}, "min_cor": "vermelho"},
        {"se": {"riscos": "Tontura/palidez/sudorese"}, "min_cor": "vermelho"},
        {"se": {"caracteristica": "Preto/borra de café (melena)"}, "min_cor": "laranja"},
        {"se": {"riscos": "Uso de anticoagulante/AAS"}, "min_cor": "laranja"}
    ],
    "mapeamento_cor": [
        (5.0, "vermelho"),
        (3.0, "laranja"),
        (1.2, "amarelo"),
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
                "Cálculo na vesícula conhecido": 0.6,
                "Paciente com menos de 6 meses de vida": 2.5
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
                "Falta de ar intensa": 1.5,
                "Lactente": 1.8
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
                "Idade ≥ 67 anos": 1.0,
                "Idade ≤ 6 anos": 0.8
            }
        }
    ],  # ← vírgula corrigida aqui
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
                "Idade ≥ 67 anos": 0.6,
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
