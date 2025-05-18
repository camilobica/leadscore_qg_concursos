# categorizar_texto.py (versão enxuta com dicionários)

import unicodedata
import re
from collections import defaultdict
from src.mapeamento_escolaridade import mapeamento_escolaridade
from src.mapeamento_estados import mapeamento_estados
from src.mapeamento_outros_idiomas import mapeamento_outros_idiomas
from src.mapeamento_motivo_fluencia import mapeamento_motivo_fluencia
from src.mapeamento_paises import mapeamento_paises
from src.mapeamento_problema_aprender import mapeamento_problema_aprender
from src.mapeamento_profissoes import mapeamento_profissoes

# ========================================
# 🔧 FUNÇÃO DE NORMALIZAÇÃO
# ========================================
def normalizar_texto(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z\s]', '', texto)
    return texto

# ========================================
# 🔁 GERAR VARIAÇÕES DE UM TERMO
# ========================================
def gerar_variacoes_termo(termo):
    variacoes = set()
    termo_norm = normalizar_texto(termo)
    variacoes.add(termo_norm)

    if not termo_norm.endswith("s"):
        variacoes.add(termo_norm + "s")

    if termo_norm.endswith("gem"):
        variacoes.add(termo_norm.replace("gem", "jem"))

    if termo_norm.endswith("cao"):
        variacoes.add(termo_norm.replace("cao", "car"))
    if termo_norm.endswith("ncia"):
        variacoes.add(termo_norm.replace("ncia", "nte"))
    if termo_norm.endswith("dade"):
        variacoes.add(termo_norm.replace("dade", ""))

    return list(variacoes)

# ========================================
# ⬆️ EXPANDIR MAPEAMENTO COM VARIAÇÕES
# ========================================
def expandir_mapeamento(mapeamento_original):
    novo_mapeamento = defaultdict(set)
    for categoria, termos in mapeamento_original.items():
        for termo in termos:
            variacoes = gerar_variacoes_termo(termo)
            for v in variacoes:
                novo_mapeamento[categoria].add(v)
    return {cat: sorted(list(terms)) for cat, terms in novo_mapeamento.items()}

# ========================================
#  NOVO: FUNÇÃO DE CHECAGEM MAIS ROBUSTA (por palavra inteira)
# ========================================
def termo_em_texto(termos, texto):
    texto = normalizar_texto(texto)  # <= Isso precisa estar aqui!
    return any(re.search(rf"\b{re.escape(termo)}\b", texto) for termo in termos)

