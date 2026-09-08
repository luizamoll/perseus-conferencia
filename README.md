# Perseus — conferência e referência de coleta

PDF Perseus → primeiro bloco de coleta → extração → `STATUS_CURSO` pela legenda oficial → conferência → consolidação da referência → Excel e PDFs.

## Usar neste Mac

Encerre o servidor anterior com Control+C e abra `iniciar.command` nesta pasta. Mantenha o Terminal aberto. Selecione o PDF **Alunos Coletados para Fatura** e clique em Processar relatório.

Após a conferência, a interface mostra os totais do documento, o quadro colorido da referência por `STATUS_CURSO`, as pendências e os arquivos para download.

Os dois PDFs reais estão em `exemplos/`. Fatura agosto de 2026 contém coleta julho de 2026; fatura setembro contém coleta agosto. A competência da fatura é lida do documento, nunca deduzida do nome do arquivo.

## Regra de negócio de STATUS_CURSO

A fonte oficial é `regras_status_curso.json`, transcrita da aba `Legenda_Cursos_Status` da planilha de referência fornecida. O histórico mensal pode ser comparado, mas não decide a categoria.

Regras principais:

- mesma categoria, mesmo com siglas repetidas → mantém a categoria;
- categorias diferentes no mesmo registro → `MÚLTIPLAS CATEGORIAS`;
- qualquer sigla ausente da legenda → `NÃO LOCALIZADO` e `REVISAR`;
- `CIB` → `DI`;
- `EVE` → `CURSO LIVRE`.

Veja `REGRA_STATUS_CURSO.md` para a regra completa, nomenclatura de `COMPETENCIA` e cores mensais.

## Saídas

O XLSX tem quatro abas:

1. **Resumo** — totais e metadados da execução;
2. **Referência** — consolidação por `STATUS_CURSO`, com a cor do mês;
3. **Alunos** — dados extraídos + `STATUS_CURSO` + `COMPETENCIA`;
4. **Divergências** — somente o que precisa de atenção.

Também são gerados:

- relatório PDF executivo;
- PDF com a lista completa de alunos;
- CSV/JSON e ZIP técnico.

Identificadores permanecem como texto, inclusive zeros à esquerda. O sistema não cria nem remove registros para fechar totais.

## Conferência de quantidade validada

A base de extração permanece a mesma:

- Agosto/2026: 2.050 informados e 2.050 extraídos.
- Setembro/2026: 2.213 informados e 2.211 extraídos; diferença -2 preservada.

A nova classificação por legenda oficial deve ser reprocessada para atualizar as quantidades por `STATUS_CURSO`; os totais de alunos não são forçados.

## Instalação em outro ambiente

Com Python 3.12 ou 3.13:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

No Mac já preparado, prefira `./iniciar.command`.

## Testes

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
node --test test_interface.cjs
python validar_reais.py --saida resultados_teste_novos
```

`validar_reais.py` processa os dois PDFs de exemplo e verifica extração, identificadores, `STATUS_CURSO`, `COMPETENCIA`, consolidação, Excel e relatório executivo.

## Organização

- `perseus.py`: extração e conferência do PDF; motor preservado.
- `classificacao.py`: aplicação da legenda oficial.
- `regras_status_curso.json`: mapa oficial Curso → categoria.
- `referencia.py`: `COMPETENCIA`, cores e consolidação mensal.
- `apresentacao.py`: resumo comum e explicações de pendências.
- `exportacao.py`: XLSX e relatório PDF executivo.
- `pdf_alunos.py`: PDF complementar com todos os registros.
- `app.py` + `interface/`: servidor local e interface.
- `REGRA_STATUS_CURSO.md`: contexto de negócio que não deve se perder.

Os documentos `DIAGNOSTICO.md` e `RELATORIO_CLASSIFICACAO.md` são históricos. PDFs digitalizados, protegidos por senha ou com layout diferente não foram homologados; não há OCR. O fluxo padrão processa o primeiro bloco contíguo do relatório.
