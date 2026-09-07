# Arquitetura real e guia de aprendizado

## Fluxo atual

Navegador → servidor Python (`app.py`) → leitor e conferência (`perseus.py`) → exportação (`exportacao.py`) → Excel/CSV/JSON/ZIP → navegador.

Tudo funciona no computador. Não há IA durante a extração, banco de dados, serviço externo, login de usuários ou motor de faturamento. O navegador usa HTML, CSS e JavaScript; a leitura e o processamento são Python.

| Peça | Problema que resolve | Entrada e saída |
|---|---|---|
| `perseus.py`: leitura | O PDF mistura tabelas de alunos, cabeçalhos repetidos e vários períodos. Identifica o período e transforma células em registros. | PDF → sete campos + identificador + página/tabela/linha + células originais |
| `perseus.py`: validação | Uma tabela pode conter campos vazios, datas inválidas, listas de comprimentos diferentes ou identificadores repetidos. Sinaliza sem excluir os registros válidos de sete campos. | Registros → alertas e conferência |
| `exportacao.py` | O CSV pode abrir em uma única coluna. Cria um Excel pronto para leitura com filtros, cabeçalho fixo, larguras e realce das diferenças. | Resultado estruturado → `alunos.xlsx` |
| `perseus.py`: salvar | É necessário guardar os dados técnicos e evitar sobrescrever uma execução. | Resultado → pasta nova com Excel, CSV e JSON |
| `app.py` | A pessoa não deve precisar chamar o extrator manualmente para cada arquivo. Recebe o PDF, inicia uma tarefa separada, informa progresso e disponibiliza downloads. | Upload → cópia local → tarefa → ZIP e arquivos individuais |
| `interface/index.html` | Organiza a seleção, leitura e conferência em uma tela. | Botões, instruções e tabelas visíveis |
| `interface/style.css` | Torna a tela legível e distingue sucesso, atenção e erro. | Aparência e adaptação à largura da tela |
| `interface/app.js` | Mantém a tela sincronizada com o Python e mostra progresso, resultado e falhas. | Consulta de estado → atualização da tela |
| `test_perseus.py`, `test_mvp.py`, `test_app.py` | Detectam mudanças que alterem comportamentos conhecidos. | Dados fictícios e PDFs reais opcionais → aprovação ou falha |

Um **script** é um arquivo de instruções executáveis. `python perseus.py arquivo.pdf --saida pasta_nova` executa o script sem interface. O MVP reúne esse processamento com uma tela e controle de tarefas.

## Como o leitor trabalha

1. Calcula SHA-256, uma impressão digital dos bytes do PDF.
2. Na primeira página, reconhece contrato, competência e quantidade faturada; esses dados são metadados, não registros de alunos.
3. Reconhece o primeiro período e seu intervalo. A interface processa o primeiro bloco contíguo. Na linha de comando existe `--periodo MM/AAAA` e `--periodo todos`; esses modos não foram validados com o relatório inteiro nesta rodada.
4. Reconhece a tabela pelo cabeçalho exato de sete colunas. Normaliza espaços/quebras de linha, mas preserva as células originais no JSON.
5. Mantém cursos, datas e status separados por vírgula na mesma linha do aluno. Não converte dois cursos em dois alunos nem decide a licença.
6. Conta linhas e identificadores distintos por período e calcula `extraídos − coletado informado`. Compara coletado, não “quantidade faturada”.
7. Confere novamente a impressão digital do PDF. A pasta de saída precisa ser nova.

“Limpar o cabeçalho” significa excluí-lo da base de alunos exportada. Não significa apagar visualmente o cabeçalho do PDF. A origem continua disponível para auditoria.

## Auditoria do protótipo recebido

O ZIP já continha leitor, conferência, interface local, consulta de progresso, exportação CSV/JSON/ZIP e cinco testes unitários. Não havia Excel nem testes que abrissem os PDFs reais. Também não havia implementação de licenças, planilha mestre ou comparação mensal.

Um ponto corrigido: antes, o resumo só registrava o período depois de encontrar uma linha de aluno. Agora registra o período declarado mesmo sem linhas, para mostrar total extraído zero e a divergência. Contradições nos totais são detectadas antes de processar a tabela.

Mantidos: sete campos, regras de validação, primeiro bloco contíguo, registros repetidos preservados, JSON com origem, servidor restrito a 127.0.0.1, token local, limite de 80 MB e pastas de execução novas.

## Limites do MVP

A extração depende do layout tabular atual e de texto pesquisável. Não tem OCR. Alertas e igualdade de total não garantem exatidão campo a campo. Mudanças no layout exigem novos testes. Tarefas ficam na memória e não retomam processamento após fechar o Python; arquivos já salvos permanecem. Uso simultâneo de vários usuários, instalação por clique e distribuição para produção ainda não foram implementados.

A planilha é um retrato da execução: editar células não recalcula a extração. Para nova conferência, processe o PDF novamente.

## Etapas futuras conforme o requisito da usuária

Validar a planilha de referência e seus campos → aprovar regras de licenças e casos ambíguos → preencher cópia da planilha mestre → consolidar por áreas aprovadas → comparar com o mês anterior usando as mesmas definições. Essas etapas dependem de decisões de negócio; contagem de registros não é automaticamente contagem de licenças.


## Classificação independente
`evidencia_classificacao.py` lê os literais do script e células históricas, produzindo mapa versionado e conflitos. `classificacao.py` consome o resultado do módulo 1, preserva registros e gera auditoria. `validar_classificacao.py` faz pareamento unívoco e compara com STATUS_CURSO sem realimentar o classificador. A extração permanece independente. A interface chama a classificação depois da extração; a exportação inclui suas colunas e casos de revisão nas abas existentes.
