import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import ibge
from estatistica import descritiva, fmt, interpretar

AZUL, AZUL_ESC, PRETO, CINZA, CINZA_ESC = (
    "#5BAEE0", "#2B7FB8", "#111111", "#E6EAEE", "#6B7480"
)
CSS = """<style>
h1, h2, h3 {color:#111111; font-weight:600; letter-spacing:0;}
.etiqueta {color:#2B7FB8; font-size:.85rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;}
.fonte {color:#6B7480; font-size:.85rem;}
.st-emotion-cache-19w15or {color:#111111; font-weight:600; letter-spacing:0;}
.leitura {border-left:4px solid #5BAEE0; background:#F3F6F9; padding:.7rem 1rem; margin:.4rem 0; color:#111111;}
div[data-testid="stMetric"] {background:#F3F6F9; border:1px solid #E1E7ED; padding:.6rem .8rem; border-radius:4px;}
</style}"""


def _estilo(fig, titulo=None, altura=420):
    fig.update_layout(template="simple_white", title=titulo, height=altura,
                      font=dict(family="Arial, sans-serif", color=PRETO),
                      colorway=[AZUL, PRETO, "#9AA5B1", AZUL_ESC, "#BFD9EC"],
                      margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(gridcolor=CINZA)
    fig.update_yaxes(gridcolor=CINZA)
    return fig


def _dim(cfg, nome_cls):
    n = ibge.norm(nome_cls)
    if "forma de declaracao" in n:
        return False, None
    for kw, alvo in cfg["dims"].items():
        if kw in n:
            return True, alvo
    return False, None


def _padrao(cfg, cls, nomes):
    total = [i for i, n in nomes.items() if ibge.norm(n) == "total"]
    dim, alvo = _dim(cfg, cls["nome"])
    if not dim:
        return total[:1] or [next(iter(nomes))]
    if alvo:
        achadas = [i for i, n in nomes.items() if alvo in ibge.norm(n)]
        if achadas:
            return achadas
    nao_total = [i for i in nomes if i not in total]
    return nao_total[:30] or total[:1]


def _foco_padrao(cfg, cname, opts):
    dim, alvo = _dim(cfg, cname)
    if dim and alvo:
        for o in opts:
            if alvo in ibge.norm(o):
                return o
    return "Total" if "Total" in opts else opts[0]


def _percentual(df, col, chaves):
    base = df[df[col] == "Total"]
    outros = [c for c in chaves if c != col]
    m = df.merge(base[outros + ["valor"]].rename(columns={"valor": "_tot"}), on=outros, how="left")
    m["valor"] = m["valor"] / m["_tot"] * 100
    return m.drop(columns="_tot")


def renderizar(cfg):
    k = cfg["chave"]
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='etiqueta'>Indicador demográfico {cfg['numero']} de 5 &nbsp;|&nbsp; "
                f"Responsável: {cfg['estudante']}</div>", unsafe_allow_html=True)
    st.title(cfg["titulo"])
    st.write(cfg["descricao"])

    sb = st.sidebar
    sb.header("Fonte dos dados")
    try:
        cands = ibge.candidatas(cfg["palavras"], cfg.get("pesquisa"), cfg.get("preferidas", []), cfg.get("reforco", []))
    except ibge.ErroIBGE as e:
        st.error(str(e))
        st.stop()
    if not cands:
        st.error("Nenhuma tabela do SIDRA encontrada para este indicador. Verifique a lista de palavras em CONFIG['palavras'].")
        st.stop()
    nomes_tab = {c["id"]: c["nome"] for c in cands}
    tabela = sb.selectbox("Tabela do SIDRA", list(nomes_tab), format_func=lambda i: f"{i} - {nomes_tab[i]}", key=f"{k}_tabela")
    try:
        meta = ibge.metadados(tabela)
        periodos = ibge.periodos(tabela)
    except ibge.ErroIBGE as e:
        st.error(str(e))
        st.stop()
    niveis = [n for lst in meta.get("nivelTerritorial", {}).values() for n in lst]
    if "N3" not in niveis:
        st.error("Esta tabela não tem dados por Unidade da Federação. Escolha outra tabela na barra lateral.")
        st.stop()

    vars_ = {str(v["id"]): v for v in meta["variaveis"]}
    ids_v = list(vars_)
    iv = next((i for i, v in enumerate(ids_v) if ibge.norm(cfg["variavel"]) in ibge.norm(vars_[v]["nome"])), 0)
    var_id = sb.selectbox("Variável", ids_v, index=iv, key=f"{k}_{tabela}_var",
                          format_func=lambda i: f"{vars_[i]['nome']} ({vars_[i]['unidade']})")
    periodo = sb.selectbox("Período", periodos, key=f"{k}_{tabela}_per")

    filtros, ordem = {}, {}
    with sb.expander("Recortes (classificações)"):
        st.caption("Escolha as categorias buscadas na API. A categoria Total é sempre incluída.")
        for c in meta.get("classificacoes", []):
            nomes = {str(x["id"]): x["nome"] for x in c["categorias"]}
            ordem[c["nome"]] = list(nomes.values())
            total = [i for i, n in nomes.items() if ibge.norm(n) == "total"]
            padrao = _padrao(cfg, c, nomes)
            sel = st.multiselect(c["nome"], list(nomes), default=padrao, key=f"{k}_{tabela}_{c['id']}",
                                 format_func=lambda i, n=nomes: n[i]) or padrao
            filtros[str(c["id"])] = list(dict.fromkeys(list(sel) + total))
    populacional = sb.radio("Variância e desvio padrão", ["Populacional (÷ n)", "Amostral (÷ n-1)"], key=f"{k}_pop") .startswith("Pop")

    try:
        with st.spinner("Consultando a API do IBGE..."):
            df = ibge.dados(tabela, periodo, var_id, filtros)
    except ibge.ErroIBGE as e:
        st.error(str(e))
        st.stop()
    if df.empty or df["valor"].notna().sum() == 0:
        st.warning("A API não retornou valores para este recorte (podem ser dados inexistentes ou sigilosos). "
                   "Troque a variável, o período ou as categorias.")
        st.stop()

    cols_cls = [c["nome"] for c in meta.get("classificacoes", []) if c["nome"] in df.columns]
    unidade = vars_[var_id]["unidade"]
    chaves = ["nivel", "cod", "periodo"] + cols_cls

    com_total = [c for c in cols_cls if "Total" in set(df[c]) and df[c].nunique() > 1]
    if com_total and sb.checkbox("Converter para % do total", key=f"{k}_pct",
                                 help="Divide cada valor pelo Total da classificação escolhida. Use apenas com contagens."):
        alvo_pct = sb.selectbox("Total de referência", com_total, key=f"{k}_pctcls")
        df = _percentual(df, alvo_pct, chaves)
        unidade = "%"

    ufs_all = df[df["nivel"] == "N3"]
    tem_brasil = (df["nivel"] == "N1").any()

    st.markdown("<div class='fonte'>Fonte: IBGE, SIDRA, tabela "
                f"<a href='https://sidra.ibge.gov.br/tabela/{tabela}' target='_blank'>{tabela}</a> "
                f"| {vars_[var_id]['nome']} | período {periodo} | unidade: {unidade}</div>", unsafe_allow_html=True)

    modos = ["Entre as UFs"] + ([f"Entre as categorias de uma classificação"] if any(
        len([x for x in df[c].unique() if x != "Total"]) >= 2 for c in cols_cls) else [])
    escopo = st.radio("Unidade de análise", modos, horizontal=True, key=f"{k}_{tabela}_escopo")

    foco = {}

    def escolher_foco(excluir=None):
        cs = [c for c in cols_cls if c != excluir]
        cols = st.columns(max(len(cs), 1))
        for col, cname in zip(cols, cs):
            opts = [x for x in ordem[cname] if x in set(df[cname])]
            if len(opts) > 1:
                ip = opts.index(_foco_padrao(cfg, cname, opts))
                foco[cname] = col.selectbox(f"{cname} em foco", opts, index=ip, key=f"{k}_{tabela}_foco_{cname}_{escopo}")
            elif opts:
                foco[cname] = opts[0]

    if escopo == "Entre as UFs":
        c1, c2 = st.columns(2)
        regs = c1.multiselect("Regiões", list(ibge.REGIOES.values()), default=list(ibge.REGIOES.values()), key=f"{k}_regs")
        d = ufs_all[ufs_all["regiao"].isin(regs)]
        ufs = sorted(d["local"].unique())
        sel_ufs = c2.multiselect("UFs", ufs, default=ufs, key=f"{k}_{'_'.join(regs)}_ufs")
        escolher_foco()
        b = d
        for c, v in foco.items():
            b = b[b[c] == v]
        b = b[b["local"].isin(sel_ufs)].dropna(subset=["valor"])
        base = pd.DataFrame({"rotulo": b["local"].values, "valor": b["valor"].values, "regiao": b["regiao"].values})
        ordem_x, titulo_dist, d_cmp = None, "Valor por UF", d[d["local"].isin(sel_ufs)]
    else:
        cands_cls = [c for c in cols_cls if len([x for x in df[c].unique() if x != "Total"]) >= 2]
        c1, c2 = st.columns(2)
        alvo = c1.selectbox("Classificação a percorrer", cands_cls, key=f"{k}_{tabela}_alvo")
        locais = (["Brasil"] if tem_brasil else []) + sorted(ufs_all["local"].unique())
        local = c2.selectbox("Território", locais, key=f"{k}_{tabela}_local")
        escolher_foco(excluir=alvo)
        b = df[df["local"] == local]
        for c, v in foco.items():
            b = b[b[c] == v]
        b = b[b[alvo] != "Total"].dropna(subset=["valor"])
        ordem_x = [x for x in ordem[alvo] if x in set(b[alvo])]
        b = b.assign(_o=b[alvo].map({x: i for i, x in enumerate(ordem_x)})).sort_values("_o")
        base = pd.DataFrame({"rotulo": b[alvo].values, "valor": b["valor"].values, "regiao": local})
        titulo_dist, d_cmp = f"Valor por categoria de {alvo}", None

    if base.empty:
        st.warning("Sem dados para este recorte. Ajuste os filtros.")
        st.stop()

    d = descritiva(base["valor"], populacional)
    base["situacao"] = np.where(d["mask_outlier"].reindex(base.index).fillna(False).values, "Outlier", "Dentro dos limites")

    abas = st.tabs(["Resumo estatístico", "Distribuição", "Ranking", "Comparar grupos", "Dados e método"])

    with abas[0]:
        st.subheader("Medidas calculadas")
        moda = ", ".join(fmt(m) for m in d["modas"][:3]) if d["modas"] else "sem moda"
        linhas = [
            [("Observações (n)", str(d["n"])), ("Média", fmt(d["media"])), ("Mediana", fmt(d["mediana"])), ("Moda", moda)],
            [("Q1", fmt(d["q1"])), ("Q3", fmt(d["q3"])), ("IQR (Q3 - Q1)", fmt(d["iqr"])), ("Amplitude", fmt(d["amplitude"]))],
            [("Variância", fmt(d["variancia"])), ("Desvio padrão", fmt(d["desvio"])),
             ("Coef. de variação", f"{fmt(d['cv'], 1)}%"), ("Outliers (1,5 x IQR)", str(int(d["mask_outlier"].sum())))],
        ]
        for linha in linhas:
            for col, (rot, val) in zip(st.columns(4), linha):
                col.metric(rot, val)
        st.subheader("Interpretação")
        for t in interpretar(d, base["rotulo"], base["valor"], unidade):
            st.markdown(f"<div class='leitura'>{t}</div>", unsafe_allow_html=True)
        st.caption("Complete esta leitura no seminário relacionando os números às desigualdades sociais e regionais.")

    with abas[1]:
        c1, c2 = st.columns(2)
        h = px.histogram(base, x="valor", nbins=max(5, min(12, d["n"])), color_discrete_sequence=[AZUL])
        h.add_vline(x=d["media"], line_dash="dash", line_color=PRETO, annotation_text="média")
        h.add_vline(x=d["mediana"], line_color=AZUL_ESC, annotation_text="mediana", annotation_position="bottom")
        h.update_traces(marker_line_color="white", marker_line_width=1)
        h.update_layout(xaxis_title=unidade, yaxis_title="Frequência")
        c1.plotly_chart(_estilo(h, "Histograma"), use_container_width=True)
        bx = px.box(base, y="valor", points="all", hover_name="rotulo", color_discrete_sequence=[AZUL_ESC])
        bx.update_layout(yaxis_title=unidade)
        c2.plotly_chart(_estilo(bx, "Boxplot"), use_container_width=True)
        if escopo == "Entre as UFs" and base["regiao"].nunique() > 1:
            bx2 = px.box(base, x="regiao", y="valor", points="all", hover_name="rotulo", color_discrete_sequence=[AZUL])
            bx2.update_layout(xaxis_title="", yaxis_title=unidade)
            st.plotly_chart(_estilo(bx2, "Boxplot por região"), use_container_width=True)

    with abas[2]:
        cor = {"Dentro dos limites": AZUL, "Outlier": PRETO}
        if ordem_x is None:
            r = base.sort_values("valor")
            g = px.bar(r, x="valor", y="rotulo", orientation="h", color="situacao", color_discrete_map=cor)
            g.update_layout(xaxis_title=unidade, yaxis_title="", legend_title="")
            _estilo(g, titulo_dist, max(380, 24 * len(r) + 100))
        else:
            g = px.bar(base, x="rotulo", y="valor", color="situacao", color_discrete_map=cor)
            g.update_xaxes(categoryorder="array", categoryarray=ordem_x)
            g.update_layout(xaxis_title="", yaxis_title=unidade, legend_title="")
            _estilo(g, titulo_dist, 460)
        st.plotly_chart(g, use_container_width=True)

    with abas[3]:
        if d_cmp is None:
            st.info("A comparação entre grupos está disponível na unidade de análise 'Entre as UFs'.")
        else:
            comps = [c for c in cols_cls if len([x for x in d_cmp[c].unique() if x != "Total"]) >= 2]
            if not comps:
                st.info("Selecione mais de uma categoria em 'Recortes' para comparar grupos.")
            else:
                alvo_c = st.selectbox("Comparar por", comps, key=f"{k}_{tabela}_cmp")
                m = d_cmp[d_cmp[alvo_c] != "Total"]
                for c, v in foco.items():
                    if c != alvo_c:
                        m = m[m[c] == v]
                m = m.dropna(subset=["valor"])
                ordc = [x for x in ordem[alvo_c] if x in set(m[alvo_c])]
                fb = px.box(m, x=alvo_c, y="valor", points="all", hover_name="local", color_discrete_sequence=[AZUL])
                fb.update_xaxes(categoryorder="array", categoryarray=ordc)
                fb.update_layout(xaxis_title="", yaxis_title=unidade)
                st.plotly_chart(_estilo(fb, f"Distribuição entre UFs por {alvo_c}", 460), use_container_width=True)
                linhas = []
                for g_ in ordc:
                    x = descritiva(m.loc[m[alvo_c] == g_, "valor"], populacional)
                    if x:
                        linhas.append({alvo_c: g_, "n": x["n"], "Média": x["media"], "Mediana": x["mediana"], "Q1": x["q1"],
                                       "Q3": x["q3"], "IQR": x["iqr"], "Desvio padrão": x["desvio"], "CV (%)": x["cv"]})
                st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    with abas[4]:
        st.subheader("Dados utilizados")
        st.dataframe(base.rename(columns={"rotulo": "Rótulo", "valor": "Valor", "regiao": "Região", "situacao": "Situação"}),
                     use_container_width=True, hide_index=True)
        csv = base.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button("Baixar CSV", csv, file_name=f"{k}.csv", mime="text/csv", key=f"{k}_dl")
        st.subheader("Fórmulas")
        st.latex(r"\bar{x}=\frac{1}{n}\sum x_i \qquad \text{Mediana}=\text{valor central dos dados ordenados}")
        st.latex(r"IQR=Q_3-Q_1 \qquad \text{Outlier}: x<Q_1-1{,}5\,IQR \ \text{ou}\ x>Q_3+1{,}5\,IQR")
        st.latex(r"\sigma^2=\frac{\sum (x_i-\bar{x})^2}{n}\ (\text{amostral: } n-1) \qquad \sigma=\sqrt{\sigma^2} \qquad CV=\frac{\sigma}{\bar{x}}\cdot 100")
        st.caption("Quartis por interpolação linear (método do NumPy/Pandas). A variância tem a unidade ao quadrado.")
        st.subheader("Tabela utilizada")
        st.write(f"Tabela {tabela}: {nomes_tab[tabela]}. Confira o nome e as categorias antes de apresentar; "
                 "se necessário, troque a tabela na barra lateral.")
