# Diagnóstico da rodada — 06/09/2026

## O que foi comprovado

O ZIP recebido foi extraído em uma cópia de trabalho. O desenvolvimento foi feito em outra pasta. Os PDFs reais foram encontrados em Downloads; `/mnt/data` não existe neste computador. Nenhum original foi editado. Os hashes dos PDFs foram conferidos antes e depois da extração.

| PDF | Páginas no arquivo | Páginas com registros do bloco | Coleta | Informados | Extraídos | IDs distintos | Diferença |
|---|---:|---|---|---:|---:|---:|---:|
| Agosto | 521 | 1–91 | 07/2026 | 2.050 | 2.050 | 2.050 | 0 |
| Setembro | 537 | 1–97 | 08/2026 | 2.213 | 2.211 | 2.211 | -2 |

A interface mantém o primeiro bloco de coleta, como no protótipo. Lê também a página seguinte para detectar a mudança de período. Não foi validada a extração de todos os blocos históricos das 521/537 páginas.

O código original foi executado primeiro como referência. O MVP foi executado depois com testes que compararam **todos os dicionários de registros**, incluindo células originais e rastreabilidade, e os resumos de conferência: igualdade integral nos dois meses. A inclusão de Excel não mudou essa base.

Nos dois meses: sete campos principais preenchidos, identificadores distintos em todas as linhas e nenhum alerta de estrutura/data/duplicidade. Múltiplos cursos preservados em uma linha: 393 em agosto e 417 em setembro. Isso não equivale a uma auditoria humana completa de cada campo.

Os totais “Quantidade Faturada” (1.984 e 2.017) são apenas metadados transcritos. O MVP não deduz como foram calculados e não os usa como quantidade esperada de alunos.

## O que não fechou

**Setembro não conciliou: faltam dois registros em relação ao resumo.** O resultado continua disponível para revisão e deve aparecer em amarelo.

Uma leitura adicional do texto, com busca por identificadores numéricos e DIs entre parênteses nas páginas 1–97, encontrou 2.211 ocorrências e 2.211 identificadores distintos, exatamente o conjunto das tabelas. É uma segunda estratégia de leitura, mas usa a mesma biblioteca de PDF. Ela reforça a consistência da extração sem provar que o resumo do Perseus está errado. Identificadores em outro formato ou conteúdo não textual podem escapar desse método.

Foram inspecionadas visualmente páginas de início/fim do bloco de setembro. Não foi identificada e corrigida uma causa para os dois registros; não houve preenchimento artificial para “bater” o total.

## Testes e verificações

- Suíte com os PDFs reais: 12 testes passaram, sem ignorados. Inclui execução dos dois PDFs, hashes, sete campos, contagem de IDs e comparação integral com o código original.
- Após acrescentar testes do servidor: 14 testes rápidos passaram; 1 teste real foi explicitamente ignorado nessa execução rápida. O teste real já havia passado na execução anterior. As mudanças posteriores foram de apresentação Excel e testes, sem alteração do extrator.
- Casos rápidos: período versus competência; vários cursos; identificador ausente; datas inválidas/fora do intervalo; listas de tamanhos diferentes; saída existente preservada; duplicidade preservada e sinalizada; tabela vazia ainda conferida; linha malformada registrada no JSON; metadados contraditórios; mudança de período; Excel reaberto; fórmulas do texto neutralizadas; CSV/JSON preservados; geração de ZIP; falha com mensagem; rota e tipo de arquivo Excel.
- Excel gerado para os dois meses e reaberto. Filtros, congelamento de cabeçalho, identificadores como texto, datas simples como datas e listas de datas preservadas. Conferência com realce condicional para diferenças. Verificação visual das três abas com renderização do arquivo.
- JavaScript passou na checagem de sintaxe. Tela inicial inspecionada no navegador. Setembro processado pela interface, incluindo tela de progresso e conferência final. Excel, CSV, JSON e ZIP baixados pela rota HTTP retornaram 200, com tipo de arquivo correto. O Excel baixado foi reaberto com 2.211 registros e identificador 0000544 preservado. Arquivo inválido testado na tela: mensagem “O arquivo selecionado não é um PDF válido”.

## Limitações e próximos passos

O MVP é demonstrável para **Extração e Conferência**. Não representa faturamento completo nem homologação da empresa.

Continuam em aberto: causa da diferença de setembro; confronto campo a campo com uma base oficial independente; comportamento em outros meses e layouts; PDFs digitalizados ou protegidos; empacotamento/instalação por clique; testes em Windows e instalação limpa de dependências.

Requisitos registrados para as próximas etapas: saída conforme a planilha de referência; preenchimento por licenças; totalização por área (lista exata a aprovar); comparação mensal de aumento/diminuição. Antes de implementar, validar os campos da planilha, o mapeamento curso/licença, CIB, múltiplas categorias e critérios de contagem. Nenhuma dessas regras foi inventada nesta rodada.

## Como apresentar

1. Abra o MVP e explique: “Esta etapa transforma um PDF em uma base de alunos e confere as quantidades.”
2. Use agosto para mostrar 2.050 versus 2.050 e abra o Excel com filtros.
3. Use setembro para mostrar 2.211 versus 2.213 e explicar por que a diferença precisa de investigação.
4. Mostre a página de origem e os campos preservados. Diga que licenças, planilha mestre e comparação mensal são as próximas etapas, dependentes das regras aprovadas.

Os logs desta rodada acompanham `evidencias/`. As planilhas reais são entregues separadamente do pacote de código.
