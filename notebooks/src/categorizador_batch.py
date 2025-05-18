
from tqdm import tqdm
import pandas as pd
import torch
import pickle
from flashtext import KeywordProcessor
from sentence_transformers import SentenceTransformer, util
from src.categorizar_texto import termo_em_texto, normalizar_texto, expandir_mapeamento

def preparar_para_categoria(mapeamento: dict, model: SentenceTransformer):
    expandido = expandir_mapeamento(mapeamento)
    embeddings = {
        categoria: model.encode(termos, convert_to_tensor=True)
        for categoria, termos in expandido.items()
    }
    return expandido, embeddings

def categorizar_coluna_batch(
    serie_textos: pd.Series,
    mapeamento_expandido: dict,
    mapeamento_embeddings: dict,
    model: SentenceTransformer,
    threshold: float = 0.6,
    desc: str = "Categorizando",
    use_cache: bool = True,
    cache_path: str = None
) -> pd.Series:
    textos = serie_textos.fillna("").astype(str)
    textos_norm = textos.map(normalizar_texto)

    # Opcional: carregar cache
    if use_cache and cache_path:
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except:
            pass

    # Criar keyword processor para busca rápida
    keyword_processor = KeywordProcessor()
    for categoria, termos in mapeamento_expandido.items():
        for termo in termos:
            keyword_processor.add_keyword(termo, categoria)

    # Pré-alocação
    categorias = pd.Series(index=serie_textos.index, dtype=object)

    # 1. Busca direta com FlashText
    for i, texto in enumerate(tqdm(textos_norm, desc=f"{desc} (busca direta)")):
        resultado = keyword_processor.extract_keywords(texto, span_info=False)
        if resultado:
            categorias.iat[i] = resultado[0]

    # 2. Deduplicar os que ainda estão sem categoria
    faltantes = categorias[categorias.isna()]
    unicos = [u for u in faltantes.unique() if isinstance(u, str) and u.strip()]
    mapa_resultado = {}

    with torch.no_grad():
        emb_unicos = model.encode(unicos, batch_size=32, convert_to_tensor=True, show_progress_bar=False)

        for i, texto_vec in enumerate(emb_unicos):
            melhor_score = 0.0
            melhor_categoria = "Outros"
            for categoria, emb_categoria in mapeamento_embeddings.items():
                score = util.cos_sim(texto_vec, emb_categoria).max().item()
                if score > melhor_score and score >= threshold:
                    melhor_score = score
                    melhor_categoria = categoria
            mapa_resultado[unicos[i]] = melhor_categoria

    # Mapear de volta para os índices originais
    for i, texto in faltantes.items():
        categorias.at[i] = mapa_resultado.get(texto, "Outros")

    # Opcional: salvar cache
    if use_cache and cache_path:
        with open(cache_path, "wb") as f:
            pickle.dump(categorias, f)

    return categorias
