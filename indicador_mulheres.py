import streamlit as st

from dados import renderizar

ESTUDANTE = "João Pedro"

CONFIG = {
    "numero": 4,
    "chave": "ind4",
    "estudante": ESTUDANTE,
    "titulo": "Mulheres: população feminina por UF e faixa etária",
    "descricao": "Indicadores da população feminina, recortes e comparações territoriais, Censo 2022. Use a opção de percentual do total para ver a participação das mulheres.",
    "pesquisa": "Censo Demográfico",
    "palavras": ["sexo","grupos de idade"],
    "reforco": ["população residente"],
    "preferidas": ["9514"],
    "variavel": "população residente",
    "dims": {"sexo": "mulheres", "idade": None},
}


def main():
    renderizar(CONFIG)


if __name__ == "__main__":
    st.set_page_config(page_title=CONFIG["titulo"], layout="wide")
    main()
