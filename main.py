from fastapi import FastAPI, Query
import pandas as pd
from rapidfuzz import process, fuzz

# Carregar a base de produtos
df = pd.read_excel("PRODUTOSV1_CORRIGIDO.xlsx")
df = df[["Código", "Descrição", "Preço", "Unid", "Estoque"]].dropna(subset=["Descrição"])
df["Preço"] = pd.to_numeric(df["Preço"], errors="coerce").fillna(0).round(2)
df["Estoque"] = pd.to_numeric(df["Estoque"], errors="coerce").fillna(0).astype(int)

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
def buscar_produto(nome: str = Query(..., description="Nome do produto a ser buscado")):
    nome_simplificado = simplificar_nome(nome)
    nomes_base = df["Nome Simplificado"].tolist()
    resultado = process.extractOne(nome_simplificado, nomes_base, scorer=fuzz.WRatio)

    if resultado and resultado[1] > 70:
        produto_encontrado = df[df["Nome Simplificado"] == resultado[0]].iloc[0]
        return {
            "nome": produto_encontrado["Descrição"],
            "preco": produto_encontrado["Preço"],
            "estoque": int(produto_encontrado["Estoque"]),
            "codigo": produto_encontrado["Código"]
        }
    else:
        return {"erro": "Produto não encontrado com confiança suficiente."}