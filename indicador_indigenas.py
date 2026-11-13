import streamlit as st

from dados import renderizar
ESTUDANTE = "Matheus Cordeiro"

CONFIG = {
    "numero": 3,
    "chave": "ind3",
    "estudante": ESTUDANTE,
    "titulo": "Pessoas indígenas: localização e situação do domicílio",
    "descricao": "Distribuição territorial da população indígena e comparação entre situação urbana e rural, Censo 2022.",
    "pesquisa": "Censo Demográfico",
    "palavras": ["indígena"],
    "reforco": ["situação do domicílio","localização","pessoas indígenas"],
    "preferidas": [],
    "variavel": "indígena",
    "dims": {"situação": None, "localiza": None},
}


def main():
    renderizar(CONFIG)


if __name__ == "__main__":
    st.set_page_config(page_title=CONFIG["titulo"], layout="wide")
    main()
