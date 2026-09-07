# Classificação Perseus — validação observacional

Implementado no projeto existente: `classificacao.py`, `evidencia_classificacao.py`, `validar_classificacao.py`, `regras_classificacao.json` e testes. A extração não foi modificada. No fechamento do MVP, a classificação foi integrada à interface e ao Excel, preservando também o uso separado sobre `resultado.json`. Não consolida nem calcula faturamento.

## Resultado por registro

| Referência | Registros PDF / histórico | Coincidências | Diferenças de status em revisão | Divergências entre classificações definitivas |
|---|---:|---:|---:|---:|
| Agosto | 2.050 / 2.050 | 2.026 (98,83%) | 24 | 0 |
| Setembro | 2.211 / 2.211 | 2.183 (98,73%) | 28 | 0 |

Os 4.261 registros têm pareamento unívoco por identificador textual, sem perda de zeros iniciais. Não há identificadores históricos ausentes nem diferenças no campo Curso entre extração e histórico. As 52 revisões são diferenças reais em relação ao STATUS_CURSO gravado, não coincidências. O resultado não comprova correção empresarial de todos os rótulos históricos.

O mapa completo usa agosto e setembro, portanto a comparação principal é retrospectiva. Como verificação adicional, o mapa foi reconstruído usando somente script, legenda e agosto, e aplicado a setembro sem incorporar seus rótulos: os resultados quantitativos foram exatamente os mesmos. Isso não equivale a homologação futura.

## Evidência e regras

68 siglas encontradas; 67 têm categoria observacional única e CIB permanece conflitante. Dez siglas são sustentadas somente por registros históricos de uma única sigla (inclusive repetições), sem regra explícita no script/legenda: ARTVI, CBIOL, EFB, EFL, GECOO, GESSP, LEPOL, QUIM, TEOC → Graduação; GEQUA → Pós. O mapa identifica essa origem sem tratá-la como aprovação formal.

Cada registro é independente; não se agrupa por pessoa. Divide-se Curso apenas por vírgula, normalizando espaços externos e caixa para a busca exata. Não há busca por substring. Repetições e texto original ficam preservados; categorias repetidas são contadas uma vez. Um único curso conhecido recebe só sua categoria.

Múltiplas categorias exige todos os cursos conhecidos, ausência de conflito e conjunto de categorias com consenso nos exemplos históricos: DI/Graduação; Curso livre/Graduação; Curso livre/DI/Graduação; DI/MBA; DI/Pós; Graduação/Mestrado. Novos conjuntos ficam para revisão. Isso generaliza apenas conjuntos de categorias sustentados pelos registros, não a quantidade de cursos.

## O que divergiu e continua sem regra suficiente

| Caso | Agosto | Setembro | Motivo |
|---|---:|---:|---|
| Registros contendo CIB | 18 | 20 | Legenda A22:B22 indica DI; script e curso isolado histórico indicam Graduação. Nenhuma precedência foi inventada. |
| LPI | 2 | 2 | Sem mapa; histórico Não mapeado. |
| SETRA / PCG | 0 | 2 | Uma ocorrência de cada em setembro, sem mapa; histórico Não mapeado. |
| 15, CEXT, CSAP, GN | 1 | 1 | Histórico DI; 15 não tem categoria sustentada e não foi ignorado. |
| ESGSC, PSO | 1 | 1 | Mapa aponta Pós/Pós; histórico Graduação. |
| DIREM, MBAAD | 1 | 1 | Mapa aponta Pós/MBA; histórico Graduação. |
| DA, DIR | 1 | 1 | Mapa aponta Pós/Graduação; histórico Graduação. |
| Total em revisão | 24 | 28 | Contagens por registro, sem duplicar motivos. |

Os conflitos de combinações são armazenados separadamente e impedem classificação definitiva desses casos. Não alteram as categorias individuais das siglas. A auditoria conserva categorias parciais conhecidas mesmo quando a categoria final fica vazia e o status é REVISAR. Mais de um motivo pode afetar o mesmo registro.

## Preservação do módulo 1 e testes

Os dois PDFs reais foram processados novamente. Registros e conferência foram comparados integralmente com os resultados anteriores: iguais. Agosto extrai 2.050 de 2.050 informados; setembro extrai 2.211 de 2.213 informados. A diferença −2 já existia e continua sem causa comprovada. O classificador não cria os dois registros faltantes.

15 testes existentes passaram, incluindo teste dos dois PDFs reais e comparação com a base anterior. 13 novos testes passaram. A descoberta final encontrou 28 testes (27 passaram nessa execução rápida; o teste dos PDFs foi omitido ali porque já havia passado na execução real anterior). Os novos testes cobrem curso único, repetição, mesma categoria, múltiplas sustentadas e não sustentadas, CIB, desconhecidos, conflitos, busca exata, vazios, preservação dos originais, independência por registro, auditoria e pareamento duplicado.

## Arquivos e rastreabilidade

`mapa_siglas.csv`: mapa e referências exatas. `conflitos.json`: conflitos por fonte e combinação. `validacao/agosto` e `validacao/setembro`: auditorias JSON completas e CSVs com STATUS_CURSO histórico, resultado, motivo e célula da planilha. JSON preserva registro e células originais do PDF; CSV inclui página/linha e referência do mapa. A auditoria registra hash do mapa canônico, e o mapa guarda hashes do script/planilha.

Fontes reais: coletafatura.py; Fatura Perseus - SET.xlsx (Legenda_Cursos_Status e abas Fatura_Final_Ref_Agosto_2026 / Fatura_Final_Ref_Setembro); PDFs de agosto/setembro; manual Coleta da fatura - google colab.docx. O manual, passos 4–5, confirma classificação posterior à extração e anterior à consolidação, mas não resolve as ambiguidades de categorias. O script legado contém versões por correspondência inteira e por substring; foi lido por análise de literais, sem executar comandos Colab. O comportamento por substring não foi reproduzido.

As categorias não mapeadas, a precedência de CIB, os três conflitos de combinações, o significado de 15 e a aprovação formal dos dez mapeamentos somente históricos permanecem pendentes. Nenhum ajuste foi feito para fechar totais.
