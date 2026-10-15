# Perseus — conferência e referência de coleta

PDF Perseus → primeiro bloco de coleta → extração → conferência → classificação provisória de `STATUS_CURSO` → Excel e PDFs.

## Abrir no Mac

Encerre um servidor anterior com Control+C e execute `./iniciar.command`. Selecione o PDF **Alunos Coletados para Fatura** e clique em Processar relatório.

## Abrir no Windows

1. Extraia/clone o projeto em uma pasta comum, como Documentos ou Área de Trabalho.
2. Tenha Python 3.12 ou superior instalado.
3. Dê dois cliques em `iniciar_windows.bat`.
4. Na primeira execução o iniciador cria `.venv` e instala as dependências automaticamente.
5. Mantenha a janela preta aberta enquanto usa o sistema. A interface abre em `http://127.0.0.1:8878`.

Se o Python não for encontrado, reinstale-o marcando **Add Python to PATH** e execute o iniciador novamente.

## O que já está confiável

A extração e a conferência de quantidade são independentes da classificação. No relatório de setembro validado, o Perseus informa 2.213 registros e o extrator encontra 2.211, diferença −2. Nenhum aluno é inventado para fechar a conta.

O valor `15` foi confirmado como **código de curso real**. Ele não deve ser tratado como erro, anomalia ou coluna deslocada.

Também há significados de cursos já esclarecidos pela área, como `LPI`, `TEOC`, `EFB`, `PCG` e `SETRA`, além do conceito de DI como vínculo de disciplina isolada.

## STATUS_CURSO ainda é provisório

A área informou que a categoria final do aluno não é definida apenas por semestre nem por uma tabela simples `sigla → categoria`. Existe um **cálculo empresarial da situação do aluno** que ainda precisa ser reconstruído.

Por isso, a distribuição em GRADUAÇÃO, DI, MBA, POS, MÚLTIPLAS CATEGORIAS etc. deve ser tratada como **provisória** neste momento. Saber que um código representa determinado curso não é suficiente, sozinho, para fixar o `STATUS_CURSO` final.

A planilha rosa histórica continua útil como referência para descobrir esse cálculo. A compatibilidade histórica de agosto/setembro permanece isolada para comparação e auditoria, sem virar automaticamente regra para meses futuros.

## Biblioteca de divergências

A pasta `biblioteca/` contém:

- `mapeamentos_operacionais.json` — fatos confirmados, códigos conhecidos sem regra final, compatibilidades históricas e pendências;
- `README.md` — explicação das camadas;
- `nao_localizados.json` — criado localmente e ignorado pelo Git; guarda somente siglas, contagens e competências.

## Saídas

O XLSX possui `Resumo`, `Referência`, `Alunos` e `Divergências`. Também são gerados relatório executivo PDF, lista completa em PDF, CSV/JSON, `biblioteca_divergencias.json` e ZIP técnico.

Identificadores permanecem texto, inclusive zeros à esquerda.

## Testes

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
node --test test_interface.cjs
```

O GitHub Actions valida a branch `feat/nova-interface` em **Linux e Windows**.

## Organização

- `perseus.py`: extração e conferência do PDF.
- `classificacao.py`: classificação provisória e rastreabilidade das fontes.
- `regras_status_curso.json`: legenda oficial.
- `biblioteca/`: fatos confirmados, compatibilidade histórica e memória local de pendências.
- `referencia.py`: `COMPETENCIA`, cores e consolidação.
- `exportacao.py`: XLSX e relatório executivo.
- `pdf_alunos.py`: lista completa em PDF.
- `app.py` + `interface/`: servidor local e interface.
- `iniciar.command`: iniciador do Mac.
- `iniciar_windows.bat`: iniciador do Windows.
- `REGRA_STATUS_CURSO.md`: regra detalhada e estado atual da reconstrução.


## Preparação da integração com Portal UNH

O novo `servico_interno.py` implementa a primeira API **somente entre servidores**, escutando exclusivamente `127.0.0.1:8879` e exigindo `PERSEUS_SERVICE_KEY`. A interface original `app.py` permanece independente em `127.0.0.1:8878`. **Não está liberado para colaboradores pela rede**: falta autenticação/identidade institucional no backend do Portal. Leia `API_INTERNA.md` antes de testar ou implantar.
