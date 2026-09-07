# Perseus — motor e saídas auditados

PDF Perseus → primeiro bloco de coleta → extração → classificação observacional → conferência → Excel e relatório PDF.

## Usar neste Mac

Encerre o servidor anterior com Control+C e abra `iniciar.command` nesta pasta. Mantenha o Terminal aberto. Selecione o PDF e clique em Processar PDF. Após a conferência, use **Baixar Excel** ou **Baixar relatório em PDF**. CSV/JSON/ZIP ficam nas opções técnicas.

Os dois PDFs reais estão em `exemplos/`. Fatura agosto de 2026 contém coleta julho de 2026; fatura setembro contém coleta agosto. A competência é lida do documento, nunca deduzida do nome do arquivo.

O XLSX tem Resumo, Alunos e Divergências. Identificadores são texto; listas de cursos/datas/status permanecem como na origem, sem criar alunos adicionais. Uma data única é armazenada como data Excel. Motivos administrativos aparecem na revisão; motivos técnicos e células originais permanecem no JSON.

Cada execução tem pasta e nome próprios. Interface, Excel e PDF usam o mesmo resumo validado. Edições manuais do Excel não refazem a conferência do PDF. Resultados anteriores não são atualizados; reprocesse o documento.

## Validação

Agosto: 2.050 informados e 2.050 extraídos, 24 registros em revisão. Setembro: 2.213 informados e 2.211 extraídos, 28 registros em revisão e uma pendência de quantidade. Nenhuma contagem foi forçada. Os 4.261 registros e suas classificações permaneceram iguais à base anterior.

O mapa é observacional. CIB, cursos sem evidência e combinações conflitantes continuam para revisão. Não calcula faturamento/licenças, não decide a regra empresarial de múltiplos cursos e não preenche a planilha mestre.

## Instalação em outro ambiente

Com Python 3.12 ou 3.13:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Para outra porta, use `python app.py --porta 8879`. A instalação em outros computadores não foi homologada.

## Testes

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
python validar_reais.py --saida resultados_teste_novos
```

O último comando processa os dois exemplos reais, valida os arquivos gerados e compara os identificadores com uma leitura textual independente. A pasta de saída deve ser nova. Para revalidar uma entrega existente com subpastas agosto/setembro:

```sh
python validar_reais.py --resultados-existentes /caminho/para/auditoria
```

O teste antigo em `test_mvp.py` usa `PERSEUS_AGOSTO` e `PERSEUS_SETEMBRO`; sem essas variáveis é ignorado explicitamente. A validação real acima independe dessas variáveis.

## Organização

- `perseus.py`: extração, validações de leitura e gravação do conjunto de saídas.
- `classificacao.py` e `regras_classificacao.json`: classificação independente e mapa preservados.
- `apresentacao.py`: validação de consistência, resumo comum, contagem por registro e explicações administrativas.
- `exportacao.py`: XLSX e PDF.
- `app.py`: servidor local, execução identificada e downloads isolados.
- `test_auditoria.py`: regressões desta rodada; demais testes preservados/adaptados à ordem das colunas.

Os documentos DIAGNOSTICO.md e RELATORIO_CLASSIFICACAO.md antigos são históricos. Consulte AUDITORIA_ATUAL.md para o diagnóstico desta entrega. Os PDFs digitalizados, protegidos por senha ou com layout diferente não foram homologados; não há OCR. O fluxo padrão processa integralmente o primeiro bloco contíguo, sem somar os blocos históricos do restante do arquivo.
