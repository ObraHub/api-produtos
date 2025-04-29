from fastapi import FastAPI, Query
import pandas as pd
from rapidfuzz import process, fuzz

# Carregar a base
df = pd.read_excel("PRODUTOSV1.XLS.xlsx", skiprows=2)
df = df[["Código", "Descrição", "Preço", "Unid", "Estoque"]].dropna(subset=["Descrição"])
df["Preço"] = pd.to_numeric(df["Preço"], errors="coerce").fillna(0).round(2)
df["Estoque"] = pd.to_numeric(df["Estoque"], errors="coerce").fillna(0).astype(int)

# Categoria inteligente baseada em palavras-chave
def identificar_categoria(nome):
    nome = nome.lower()
    if "cimento" in nome: return "cimento"
    if "tinta" in nome: return "tinta"
    if "ferro" in nome: return "ferro"
    if "torneira" in nome: return "torneira"
    if "tubo" in nome: return "tubo"
    if "madeira" in nome or "ripa" in nome or "caibro" in nome: return "madeira"
    if "revestimento" in nome or "porcelanato" in nome or "piso" in nome: return "piso"
    return "geral"

# Perguntas específicas por categoria
perguntas_por_categoria = {
    "cimento": ["Qual tipo? CP II ou CP IV?", "Qual peso? 25kg ou 50kg?"],
    "tinta": ["Qual tipo? Acrílica, esmalte, óleo?", "Qual volume? 3,6L ou 18L?", "Qual cor?"],
    "ferro": ["Qual a bitola? 6mm, 8mm, 10mm?"],
    "torneira": ["É para parede ou mesa?", "Vai ser usada na cozinha, banheiro ou tanque?"],
    "tubo": ["Qual diâmetro? 20mm, 40mm, 100mm?", "É para esgoto, água fria ou elétrica?"],
    "madeira": ["Qual tipo de madeira? Ripa, caibro ou viga?", "Quais medidas você precisa?"],
    "piso": ["Qual tipo? Cerâmico, porcelanato?", "Qual medida? 60x60, 90x90?", "Qual acabamento ou cor?"]
}

# Simplificar nome
def simplificar_nome(nome):
    import re
    nome = str(nome).lower()
    nome = re.sub(r'\([^)]*\)', '', nome)
    nome = re.sub(r'[^a-z0-9\s]', '', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome

df["Nome Simplificado"] = df["Descrição"].apply(simplificar_nome)

app = FastAPI()

@app.get("/buscar-produto")
def buscar_produto(nome: str = Query(..., description="Nome ou descrição do produto")):
    nome_simplificado = simplificar_nome(nome)
    categoria = identificar_categoria(nome)

    # Se for uma palavra genérica, não buscar produto ainda
    palavras_genericas = ["ferro", "cimento", "tinta", "tubo", "madeira", "piso", "torneira"]
    if any(p in nome_simplificado for p in palavras_genericas):
        if len(nome_simplificado.split()) <= 2:
            sugestoes = perguntas_por_categoria.get(categoria, ["Você pode me dar mais detalhes sobre o produto?"])
            return {
                "erro": "Descrição muito genérica.",
                "possivel_categoria": categoria,
                "perguntas_ia": sugestoes
            }

    # Fazer a busca de produtos
    nomes_base = df["Nome Simplificado"].tolist()
    resultado = process.extractOne(nome_simplificado, nomes_base, scorer=fuzz.WRatio)

    if resultado and resultado[1] > 85:
        produto_encontrado = df[df["Nome Simplificado"] == resultado[0]].iloc[0]
        return {
            "nome": produto_encontrado["Descrição"],
            "preco": float(produto_encontrado["Preço"]),
            "estoque": int(produto_encontrado["Estoque"]),
            "codigo": int(produto_encontrado["Código"])
        }
    else:
        sugestoes = perguntas_por_categoria.get(categoria, ["Você pode me dar mais detalhes sobre o produto?"])
        return {
            "erro": "Produto não encontrado com confiança suficiente.",
            "possivel_categoria": categoria,
            "perguntas_ia": sugestoes
        }