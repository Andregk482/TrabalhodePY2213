import streamlit as st

from dados import renderizar

ESTUDANTE = "André Antunes"

CONFIG = {
    "numero": 1,
    "chave": "ind1",
    "estudante": ESTUDANTE,
    "titulo": "População por grupo de idade, sexo e raça",
    "descricao": "Estrutura etária e composição da população por sexo e cor ou raça, Censo 2022. Estatísticas calculadas entre as UFs e entre as faixas etárias.",
    "pesquisa": "Censo Demográfico",
    "palavras": ["cor ou raça","sexo","idade"],
    "reforco": ["grupos de idade","população residente"],
    "preferidas": ["9606","9605"],
    "variavel": "população residente",
    "dims": {"idade": None, "sexo": None, "cor ou raça": None},
}


def main():
    renderizar(CONFIG)


if __name__ == "__main__":
    st.set_page_config(page_title=CONFIG["titulo"], layout="wide")
    main()
