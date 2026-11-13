import streamlit as st

from dados import renderizar
ESTUDANTE = "João Vitor"

CONFIG = {
    "numero": 5,
    "chave": "ind5",
    "estudante": ESTUDANTE,
    "titulo": "Rendimento dos responsáveis pelo domicílio",
    "descricao": "Distribuição do rendimento das pessoas responsáveis pelos domicílios: média versus mediana, quartis, IQR e outliers entre as UFs.",
    "pesquisa": "Censo Demográfico",
    "palavras": ["rendimento","respons"],
    "reforco": ["domicílio","mensal","média"],
    "preferidas": [],
    "variavel": "rendimento",
    "dims": {"sexo": None, "cor ou raça": None, "situação": None},
}


def main():
    renderizar(CONFIG)


if __name__ == "__main__":
    st.set_page_config(page_title=CONFIG["titulo"], layout="wide")
    main()
