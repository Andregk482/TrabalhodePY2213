
import streamlit as st

from dados import renderizar

ESTUDANTE = "Miguel Figuereiro"

CONFIG = {
    "numero": 2,
    "chave": "ind2",
    "estudante": ESTUDANTE,
    "titulo": "Alfabetização por sexo e raça",
    "descricao": "Taxa de alfabetização das pessoas de 15 anos ou mais, por sexo e cor ou raça, Censo 2022. Compara desigualdades educacionais entre grupos e UFs.",
    "pesquisa": "Censo Demográfico",
    "palavras": ["alfabetiza","cor ou raça"],
    "reforco": ["sexo","grupos de idade","taxa"],
    "preferidas": ["9543"],
    "variavel": "taxa de alfabetização",
    "dims": {"cor ou raça": None, "sexo": None},
}


def main():
    renderizar(CONFIG)


if __name__ == "__main__":
    st.set_page_config(page_title=CONFIG["titulo"], layout="wide")
    main()
