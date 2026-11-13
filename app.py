
import streamlit as st

import indicador_populacao as i1
import indicador_alfabetizacao as i2
import indicador_indigenas as i3
import indicador_mulheres as i4
import indicador_rendimento as i5

st.set_page_config(page_title="PYMATIB", layout="wide")

MODULOS = [i1, i2, i3, i4, i5]


def inicio():
    st.markdown("<div class='etiqueta' style='color:#2B7FB8;font-weight:600;text-transform:uppercase'>"
                "Projeto PYMATIB | Python e Matemática</div>", unsafe_allow_html=True)
    st.title("Números que Falam - Descobrindo o Brasil")
    st.write("Painel de indicadores demográficos do IBGE com estatística descritiva. ")
    st.subheader("Grupo e indicadores")
    st.table({"Nº": [m.CONFIG["numero"] for m in MODULOS],
              "Indicador demográfico": [m.CONFIG["titulo"] for m in MODULOS],
              "Estudante responsável": [m.ESTUDANTE for m in MODULOS]})

paginas = [st.Page(inicio, title="Apresentação do grupo", url_path="inicio", default=True)]
for m in MODULOS:
    paginas.append(st.Page(m.main, title=f"{m.CONFIG['numero']}. {m.CONFIG['titulo'].split(':')[0]}",
                           url_path=f"indicador-{m.CONFIG['numero']}"))
st.navigation(paginas).run()
