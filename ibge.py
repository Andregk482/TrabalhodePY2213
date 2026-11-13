import re
import time
import unicodedata

import pandas as pd
import requests
import streamlit as st

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
HEADERS = {"User-Agent": "numeros-que-falam/1.0 (projeto escolar)"}
REGIOES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
LIMITE_VALORES = 90000  # a API recusa consultas acima de 100 mil valores


class ErroIBGE(Exception):
    pass


def norm(texto):
    """Minusculas e sem acentos, para comparar nomes."""
    t = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


def _get(url, tentativas=3):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(url, headers=HEADERS, timeout=90)
            if 400 <= r.status_code < 500:
                raise ErroIBGE(f"A API recusou a consulta ({r.status_code}): {r.text[:200]}")
            r.raise_for_status()
            return r.json()
        except ErroIBGE:
            raise
        except (requests.RequestException, ValueError) as e:
            ultimo = e
            time.sleep(1.5 * (i + 1))
    raise ErroIBGE(f"Nao foi possivel consultar a API do IBGE: {ultimo}")


@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def catalogo():
    js = _get(BASE)
    out = []
    for pesq in js:
        for ag in pesq.get("agregados", []):
            out.append({"id": str(ag["id"]), "nome": ag["nome"], "pesquisa": pesq.get("nome", "")})
    return out


def candidatas(palavras, pesquisa=None, preferidas=(), reforco=(), limite=20):
    """Tabelas cujo nome contem TODAS as palavras; reforco apenas muda a ordem."""
    cat = catalogo()
    ps = [norm(p) for p in palavras]
    pref = {str(p) for p in preferidas}

    def busca(com_pesquisa):
        res = []
        for t in cat:
            if com_pesquisa and pesquisa and norm(pesquisa) not in norm(t["pesquisa"]):
                continue
            n = norm(t["nome"])
            if all(p in n for p in ps):
                pontos = (100 if t["id"] in pref else 0) + 10 * sum(norm(r) in n for r in reforco)
                num = int(t["id"]) if t["id"].isdigit() else 0
                res.append((pontos, num, t))
        res.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [r[2] for r in res[:limite]]

    return busca(True) or busca(False)


@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def metadados(tabela):
    return _get(f"{BASE}/{tabela}/metadados")


@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def periodos(tabela):
    js = _get(f"{BASE}/{tabela}/periodos")
    return sorted((str(p["id"]) for p in js), reverse=True)


def _parse(js, nivel):
    linhas = []
    for var in js:
        unidade = var.get("unidade")
        for res in var.get("resultados", []):
            cls = {c["nome"]: next(iter(c["categoria"].values())) for c in res.get("classificacoes", [])}
            for s in res.get("series", []):
                loc = s["localidade"]
                nv = loc["nivel"]["id"] if isinstance(loc.get("nivel"), dict) else nivel
                nome = re.sub(r"\s-\s[A-Z]{2}$", "", loc["nome"]) if nv == "N3" else loc["nome"]
                for per, val in s["serie"].items():
                    linhas.append({"nivel": nv, "cod": str(loc["id"]), "local": nome,
                                   "periodo": str(per), "valor": val, "unidade": unidade, **cls})
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")  # "-", "..", "X" viram NaN
    df["regiao"] = df.apply(lambda r: REGIOES.get(r["cod"][0], "") if r["nivel"] == "N3" else "Brasil", axis=1)
    return df


@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def dados(tabela, periodo, variavel, filtros):
    """filtros: {id_classificacao: [ids_categorias]}. Retorna Brasil (N1) e UFs (N3)."""
    combos = 1
    for ids in filtros.values():
        combos *= max(len(ids), 1)
    if combos * 28 > LIMITE_VALORES:
        raise ErroIBGE("O recorte escolhido e grande demais para a API. Reduza as categorias em 'Recortes'.")
    cls = "|".join(f"{c}[{','.join(ids)}]" for c, ids in filtros.items())
    partes = []
    for nivel in ("N1", "N3"):
        url = f"{BASE}/{tabela}/periodos/{periodo}/variaveis/{variavel}?localidades={nivel}[all]"
        if cls:
            url += f"&classificacao={cls}"
        try:
            partes.append(_parse(_get(url), nivel))
        except ErroIBGE:
            if nivel == "N3":
                raise
    partes = [p for p in partes if not p.empty]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
