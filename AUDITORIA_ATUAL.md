# Perseus — auditoria do motor e das saídas

Auditoria concluída em 07/09/2026. O escopo operacional permanece o primeiro bloco contíguo de coleta de cada PDF, sem somar os períodos históricos. A interface não foi redesenhada.

## Funcionando

Fluxo real PDF → período → extração → classificação independente → conferência → revisões → XLSX/PDF/JSON/ZIP executado pelos endpoints locais com os dois PDFs. Setembro também foi processado pelo navegador, com verificação dos dois botões de download e ausência de erros de console.

Os sete campos originais e toda a rastreabilidade dos 4.261 registros são iguais às saídas anteriores. A comparação integral com a planilha histórica confirmou nomes, cursos, datas, status, unidades e tipos; datas numéricas do histórico foram interpretadas como datas Excel, não como divergências. Os identificadores são texto, sem conversão numérica, inclusive 165 identificadores iniciados por zero em agosto e 167 em setembro.

Uma segunda leitura do texto dos PDFs encontrou os mesmos identificadores que a extração tabular. Em 41 registros selecionados — primeiros/últimos, intervalos ao longo do documento, nomes longos, listas longas e classificações ambíguas — 287 campos foram comparados diretamente nas coordenadas das células usando PDFium, leitor independente do pdfplumber. Nenhuma diferença de conteúdo foi encontrada, descontando somente espaços e quebras de linha de apresentação.

## Bugs encontrados e corrigidos

| Problema | Correção comprovada |
|---|---|
| Resumo do Excel e relatório PDF não exibiam claramente a competência junto ao período de coleta e ao status geral. | Os dois rótulos são explícitos e vêm do mesmo resumo utilizado pela interface. |
| Identificador aparecia depois de campos pouco úteis; as revisões começavam por página/linha e motivos técnicos. | Aluno e Identificador vêm primeiro; a revisão inclui problema, explicação administrativa e localização completa. Motivos técnicos permanecem no JSON. |
| Revisões de leitura podiam perder a identificação do aluno e a tabela de origem. | Alertas novos preservam aluno, identificador, curso, período, página, tabela e linha quando disponíveis. |
| Vários motivos de leitura podiam inflar a quantidade de casos. | Uma pendência por registro/local reúne todos os motivos. Registros para revisão, alertas sem registro associado e diferença de quantidade são contagens distintas. |
| Diferença no total não aparecia como item explícito na aba Divergências. | Incluída uma pendência de conferência, sem inventar aluno ou identificador. Setembro tem 28 registros em revisão mais uma pendência de quantidade. |
| Uma data válida seguida de texto inválido podia passar sem alerta sobre esse item. | Cada item do campo de datas é validado; valores originais continuam preservados. |
| Competência/contrato/quantidade faturada divergentes em cabeçalhos das páginas lidas não eram comparados. | Cabeçalhos contraditórios interrompem a execução com mensagem explícita. |
| Um primeiro bloco vazio podia permitir a retomada de um bloco posterior não contíguo. | A mudança de período encerra o bloco inicial mesmo se ele não tiver registros. |
| Exportação aceitava um resumo incompatível com os registros. | Validação antes da saída confere competência, período, contagens e correspondência da auditoria de classificação. |
| O caminho por linha de comando não produzia o mesmo conjunto principal de saídas/classificação. | O comando completo agora classifica depois de extrair e gera XLSX e PDF pelo exportador comum. A função de extração continua independente. |
| Downloads de execuções diferentes tinham o mesmo nome. | Nome, metadados e tela identificam a execução; endpoints usam sua pasta exclusiva e mantêm Cache-Control: no-store. |

Esses problemas foram reproduzidos em testes de regressão ou constatados no código/saídas. As correções de casos excepcionais não alteraram os registros, totais ou classificações dos dois PDFs reais. O mapa e o módulo de classificação permanecem inalterados.

## Resultado agosto

- Documento: Agosto.pdf; 521 páginas; competência da fatura **2026/08**.
- Coleta **07/2026**, de **26/06/2026 a 25/07/2026**.
- Primeiro bloco: páginas **1–91**; a página 92 inicia outro período.
- Informados **2.050**; extraídos **2.050**; diferença **0**; identificadores distintos **2.050**.
- Sem alertas de estrutura **2.050**; classificados automaticamente **2.026**; registros para revisão **24**.
- Status: **Totais conferem; revisão pendente**.
- XLSX com três abas; PDF com três páginas.

## Resultado setembro

- Documento: Setembro.pdf; 537 páginas; competência da fatura **2026/09**.
- Coleta **08/2026**, de **26/07/2026 a 25/08/2026**.
- Primeiro bloco: páginas **1–97**; a página 98 inicia coleta 07/2026, ainda dentro da fatura 2026/09.
- Informados **2.213**; extraídos **2.211**; diferença **−2**; identificadores distintos **2.211**.
- Sem alertas de estrutura **2.211**; classificados automaticamente **2.183**; registros para revisão **28**.
- Status: **Divergência de quantidade**.
- XLSX com três abas e 29 pendências (28 registros + uma diferença de total); PDF com quatro páginas.

A leitura textual de todas as 1.058 páginas confirmou uma única competência de fatura por arquivo. Os demais blocos históricos foram inventariados, mas não incorporados ao conjunto operacional. Não se declara homologação da extração tabular de todos os períodos históricos nem de layouts diferentes.

## Divergências de dados/fontes, não bugs eliminados artificialmente

O primeiro bloco de setembro possui 2.211 identificadores no texto independente, na extração tabular e na planilha histórica, frente a 2.213 no resumo do próprio PDF. A causa empresarial dessa diferença não está demonstrada; não foram identificados dois registros específicos que devessem ser acrescentados.

| Pendência de classificação | Agosto | Setembro |
|---|---:|---:|
| CIB: legenda e script/histórico discordam | 18 | 20 |
| LPI: sem categoria sustentada | 2 | 2 |
| SETRA e PCG: sem categoria sustentada | 0 | 2 |
| Código 15 dentro de uma lista de cursos | 1 | 1 |
| ESGSC/PSO, DIREM/MBAAD e DA/DIR: combinações conflitantes | 3 | 3 |
| Total de registros para revisão | 24 | 28 |

O mapa foi reconstruído a partir de `coletafatura.py` e `Fatura Perseus - SET.xlsx` e coincidiu integralmente com o mapa versionado. A comparação histórica é retrospectiva, não homologação empresarial. Não se removeu curso repetido, não se fundiram pessoas e não se criaram linhas por curso.

## Questões ainda sem evidência suficiente

Precedência das fontes de CIB; significado/categoria de LPI, SETRA, PCG e 15; tratamento das três combinações conflitantes; regra empresarial geral para uma pessoa com mais de um curso/categoria; aprovação formal dos dez mapeamentos sustentados apenas por histórico; origem da diferença de dois registros em setembro. Essas questões permanecem explícitas, sem impedir as verificações objetivas.

## Testes executados

- 44 testes rápidos descobertos: 43 aprovados e um teste real antigo condicionado a variáveis de ambiente ignorado nessa chamada. Os dois PDFs foram testados separadamente no fluxo real, sem amostragem da extração do primeiro bloco.
- Fluxo HTTP real dos dois PDFs: processamento, JSON de estado, downloads, nomes de execução, MIME, attachment, no-store e conteúdo do ZIP.
- Comparação integral dos registros/conferência/classificação com a base anterior e dos sete campos com a planilha histórica.
- 41 registros/287 campos conferidos nas coordenadas originais por leitor independente; todos os identificadores dos blocos comparados com o texto independente.
- Reabertura dos XLSX com openpyxl; comparação célula a célula dos campos operacionais, datas e identificadores; filtros, congelamento, ausência de mesclagem e altura máxima de 70 pontos.
- Reabertura e leitura dos relatórios; presença de todas as pendências, motivos e identificadores.
- Inspeção visual de todas as páginas dos dois relatórios e das três abas, incluindo as listas mais longas. A inspeção das abas usou cópias temporárias com áreas de impressão delimitadas, abertas pelo LibreOffice, para avaliar os campos em escala legível. Essas cópias não são os arquivos finais.
- Navegador: setembro processado novamente, competência/totais verificados, Excel e PDF baixados; nenhum erro de console.
- Sintaxe JavaScript verificada. Validador reproduzível disponibilizado no projeto.

Não havia Microsoft Excel instalado para homologação nativa nessa aplicação. A validação foi feita com openpyxl, LibreOffice e leitores de PDF. Essa limitação não foi tratada como aprovação no Excel.

## Arquivos finais

`agosto/` e `setembro/` contêm o XLSX, o relatório PDF e o JSON da respectiva execução validada. `validacao.json` registra contagens, hashes e nomes exatos. O código atual está em `../perseus_mvp/`; o pacote auditado contém esse projeto e seus testes. As saídas anteriores permanecem como histórico e não devem ser confundidas com esta pasta de auditoria.
