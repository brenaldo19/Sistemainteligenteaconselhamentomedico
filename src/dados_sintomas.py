from utils import normalizar

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
        "alergia cutânea", "reação alérgica", "lesões na pele", "manchas anormais na pele",
        "coceira na pele", "inchaço incomum"
    ],
    "oftalmologico": [
        "alterações visuais súbitas", "dor ou olho vermelho", "inchaço nos olhos ou face",
        "corpo estranho nos olhos, ouvidos ou nariz"
    ],
    "otorrino": [
        "dor no ouvido", "coriza e espirros", "sangramento nasal", "alteração na audição",
        "dificuldade pra engolir", "corpo estranho na garganta"
    ],
    "obstetrico": [
        "dor durante a gravidez", "trabalho de parto", "redução dos movimentos fetais", "sangramento vaginal"
    ],
    "pediatrico": [
        "febre lactente", "icterícia neonatal", "queda em criança", "choro persistente"
    ],
    "hematologico": [
        "sangramento ativo", "sangramento gastrointestinal", "sangramento nasal",
        "sangramento retal", "inchaço dos linfonodos"
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
    "ginecologico": ["sangramento vaginal"]
}

# sintoma -> sistema (normalizado)
sintoma_para_sistema = {
    normalizar(sintoma): sistema
    for sistema, lista in sistemas_sintomas.items()
    for sintoma in lista
}

sistemas_secundarios = {
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
