from .utils import normalizar, max_cor
from .utils import classificar_imc  # se precisar aqui
from dados_sintomas import sintoma_para_sistema, sistemas_secundarios

def gerar_sistemas_afetados_por_fatores(idade, imc_class, gravida, condicoes_brutas):
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
    return sistemas_secundarios.get(normalizar(grupo_primario), [])

def verificar_se_deve_subir_cor(sintomas_escolhidos, sistemas_afetados):
    sistemas_norm = {normalizar(s) for s in (sistemas_afetados or [])}
    for s in sintomas_escolhidos or []:
        sistema = sintoma_para_sistema.get(normalizar(s))
        if sistema and sistema in sistemas_norm:
            return True
    return False

def classificar_combinacao(cores):
    """Combina conservador: nunca abaixo da maior individual; escala por soma de pesos."""
    pesos = {"verde": 0.2, "amarelo": 1.0, "laranja": 3.5, "vermelho": 6.5}
    total = sum(pesos.get(c, 0) for c in (cores or []))
    cor_individual_max = max_cor(*(cores or ["verde"]))
    if any(c == "vermelho" for c in (cores or [])):
        cor_por_total = "vermelho"
    elif total >= 4.5:
        cor_por_total = "vermelho"
    elif total >= 2.2:
        cor_por_total = "laranja"
    elif total >= 1.0:
        cor_por_total = "amarelo"
    else:
        cor_por_total = "verde"
    return max_cor(cor_individual_max, cor_por_total)

def calcular_ajuste_por_fatores_conservador(
    sintomas_escolhidos, cores_individuais, idade=None, gravida=False
):
    # 1) tudo verde? não ajusta
    if not cores_individuais or all(c == "verde" for c in cores_individuais):
        return 0
    # 2) só ajusta se existir >= amarelo
    if not any(c in ("amarelo", "laranja", "vermelho") for c in cores_individuais):
        return 0

    risco_alto = False
    if idade is not None and (idade <= 4 or idade >= 67):
        risco_alto = True
    if str(gravida).strip().lower() in ["sim", "true", "1"]:
        risco_alto = True

    # 3) duplicidade de sistema entre sintomas
    contagem_por_sistema = {}
    for s in sintomas_escolhidos or []:
        sist = sintoma_para_sistema.get(normalizar(s))
        if sist:
            contagem_por_sistema[sist] = contagem_por_sistema.get(sist, 0) + 1
    duplicidade = any(q >= 2 for q in contagem_por_sistema.values())

    return 1 if (risco_alto or duplicidade) else 0
