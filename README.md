# Números que Falam - Descobrindo o Brasil

Dashboard de indicadores demográficos do IBGE com estatística descritiva (Python, Pandas, NumPy, Plotly, Streamlit).

## Os 5 indicadores (um por estudante)

| Nº | Arquivo | Indicador demográfico |
|----|---------|-----------------------|
| 1 | indicador_1_populacao_idade_sexo_raca.py | População por grupo de idade, sexo e raça |
| 2 | indicador_2_alfabetizacao_sexo_raca.py | Alfabetização por sexo e raça |
| 3 | indicador_3_pessoas_indigenas.py | Pessoas indígenas (localização e situação do domicílio) |
| 4 | indicador_4_mulheres.py | Mulheres |
| 5 | indicador_5_rendimento_responsaveis.py | Rendimento dos responsáveis |

Antes de entregar, edite a variável `ESTUDANTE` no topo de cada arquivo com o nome do integrante.

## Como executar

```
pip install -r requirements.txt
streamlit run app.py                                    # painel único (integração do grupo)
streamlit run indicador_1_populacao_idade_sexo_raca.py  # um indicador isolado
python testes_estatistica.py                            # valida a matemática
```

## Estrutura

- `app.py`: painel integrado com navegação por indicador.
- `comum/ibge.py`: cliente da API de Agregados v3 do IBGE (catálogo, metadados, períodos, dados).
- `comum/estatistica.py`: média, mediana, moda, Q1, Q3, IQR, amplitude, variância, desvio padrão, CV e outliers (1,5 x IQR).
- `comum/painel.py`: interface (filtros, cards, histograma, boxplot, ranking, comparação, método).
- `testes_estatistica.py`: confere os cálculos com contas manuais e NumPy.

## Como os dados são obtidos

Cada indicador procura, no catálogo oficial do IBGE, as tabelas do Censo Demográfico cujo nome contém as palavras definidas em `CONFIG["palavras"]`. A tabela, a variável, o período e as categorias podem ser trocados na barra lateral. Os números nunca são digitados à mão: tudo vem da API.

Importante: confira na aba "Dados e método" se a tabela escolhida corresponde ao indicador (o nome aparece ali). Se não, troque a tabela na barra lateral ou ajuste as palavras em `CONFIG`. A primeira consulta pode demorar; depois fica em cache no disco.

## Convenções matemáticas

Quartis por interpolação linear; outliers fora de [Q1 - 1,5 IQR ; Q3 + 1,5 IQR]; variância e desvio padrão populacionais por padrão (opção amostral na barra lateral); moda com valores arredondados a 2 casas (sem moda quando nada se repete).

## Publicação (opcional)

Suba a pasta para um repositório no GitHub e publique em share.streamlit.io apontando para `app.py`.
