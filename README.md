# RPA - Cotação Automatizada

Um pequeno projeto de RPA para coletar cotações de câmbio a partir de múltiplas fontes (API e scraping de site), consolidar os dados e exportá-los para CSV. O objetivo é fornecer um pipeline simples, resiliente e fácil de executar localmente.

## Destaques
- Coleta via API (Frankfurter) com tratamento de erros e retries.
- Scraping de site (x-rates.com) com parsing via BeautifulSoup.
- Normalização e exportação em CSV (formato compatível com Excel PT-BR).
- Log de erros em `data/erros.csv` para auditoria.

---

## Requisitos
- Python 3.10+ (testado com 3.10/3.11)
- Sistema: Windows / Linux / macOS

As dependências do projeto estão listadas em `requirements.txt`.

## Instalação (Windows PowerShell)
Crie um ambiente virtual e instale as dependências:

```powershell
# criar venv
python -m venv .venv
# ativar (PowerShell)
.\.venv\Scripts\Activate.ps1
# atualizar pip
pip install --upgrade pip
# instalar dependências
pip install -r .\requirements.txt
```

Observação: se preferir outro shell (cmd, bash), use o comando de ativação apropriado (`.venv\Scripts\activate` no cmd, `source .venv/bin/activate` no bash).

## Execução
A partir da raiz do repositório, com o virtualenv ativado:

```powershell
python src\main.py
```

Após execução bem-sucedida:
- `data/taxas_cambio.csv` será atualizado/gerado com as cotações coletadas.
- `data/erros.csv` conterá registros de erros ocorridos durante execução (auditoria).

### Comportamento esperado
- O script tenta coletar taxas via API e, separadamente, via scraping do site. Se uma fonte falhar, o erro é registrado em `data/erros.csv` e a execução continua com as outras fontes.

---

## Estrutura de pastas e descrição dos arquivos
A estrutura principal do projeto é a seguinte:

```
README.md
requirements.txt
data/
		erros.csv            # (saída) log de erros (se não existir, será criado)
		taxas_cambio.csv     # (saída) cotações consolidadas
src/
		main.py              # ponto de entrada da aplicação
		models/
				model.py         # modelo de dados: DataPoint (dataclass)
		services/
				api_scraper.py   # consulta a API (Frankfurter) e conversão para DataPoint
				site_scraper.py  # scraping do site x-rates.com usando BeautifulSoup
		utils/
				logger.py        # utilitários de logging e função para registrar erros em CSV
				output_utils.py  # normalização de dados e salvamento em CSV (formato PT-BR)
				site_utils.py    # criação de Session requests com política de retries
```

A seguir, descrição detalhada de cada arquivo em `src/`:

### `src/main.py`
- Ponto de entrada (`if __name__ == "__main__": main()`).
- Orquestra a coleta de dados das fontes (`buscar_taxas_cambio` e `scrape_xrates`), consolida os resultados e delega a gravação via `save_to_csv`.
- Registra erros usando `log_error_to_sheet` para manter um histórico em CSV.

### `src/models/model.py`
- Define a dataclass `DataPoint` com os campos:
	- `timestamp: datetime` — momento da coleta
	- `source: str` — origem (ex: `api_frankfurter`, `xrates_site`)
	- `base: str` — moeda base (ex: `USD`)
	- `target: str` — moeda alvo (ex: `BRL`)
	- `rate: float` — taxa de câmbio
- Método `to_dict()` para serialização e `__post_init__` que valida `rate > 0`.

### `src/services/api_scraper.py`
- Contém a lógica de requisição à API (Frankfurter): constrói URL, faz `GET` com `requests.Session` configurada, trata `Timeout`, `ConnectionError`, `HTTPError` e erros gerais.
- Funções internas:
	- `_obter_resposta_api(url, timeout)` → faz a requisição e retorna `Response` ou lança `RuntimeError` com mensagem amigável.
	- `_extrair_json(resp)` → valida e extrai o campo `rates` do JSON.
	- `_parsear_timestamp(data_str)` → converte a string de data retornada pela API para `datetime`.
	- `_construir_datapoints(dados, timestamp, fonte)` → mapeia `rates` para objetos `DataPoint`.
- Exporta `buscar_taxas_cambio(base: str = "USD") -> List[DataPoint]`.

### `src/services/site_scraper.py`
- Faz scraping da página `x-rates.com` para ler a tabela de taxas.
- Usa `requests` (com header User-Agent) e `BeautifulSoup` para parsear o HTML.
- Retorna uma lista de dicionários com chaves: `timestamp`, `source`, `base`, `target`, `rate`.
- Implementado com tratamento de erros básicos (retorna lista vazia em caso de falha).

### `src/utils/site_utils.py`
- Fornece `make_session()` que cria e retorna `requests.Session` configurada com `Retry` (urllib3) e `HTTPAdapter`.
- Parâmetros configuráveis: `retries`, `backoff`, `status_forcelist`.
- A sessão inclui um `User-Agent` padrão.

### `src/utils/logger.py`
- `get_logger(name)` cria logger com `StreamHandler` e um formato padronizado.
- `log_error_to_sheet(source, error_message, path='data/erros.csv')`: registra erros em um CSV (cria se não existir). Utiliza `pandas` para ler/concatenar/escrever.

### `src/utils/output_utils.py`
- Contém helpers para normalizar as entradas (`_to_dict`) e `save_to_csv(data_points, path='data/output.csv', mode='w')`.
- Normaliza nomes de campos, converte `rate` para numérico, formata `data` para `dd/mm/YYYY`, renomeia colunas para PT-BR (`data`, `origem`, `base`, `moeda`, `cotação`) e salva em CSV com `;` e `utf-8-sig`.

---

## Arquivos de saída
- `data/taxas_cambio.csv` (ou `data/output.csv` dependendo do parâmetro em `save_to_csv`) — contém as cotações consolidadas.
- `data/erros.csv` — log de erros e exceções ocorridas durante a coleta (útil para auditoria e reprocessamento).

## Observações e boas práticas
- Redes: como o processo depende de requisições HTTP (API + scraping), considere usar variáveis de ambiente ou timeouts mais agressivos em ambientes não confiáveis.
- Agendamento: para execução periódica, utilize um agendador (Task Scheduler no Windows, cron em Linux) ou uma solução de orquestração.
- Robustez: atualmente o scraping é simples e pode quebrar se a estrutura do site mudar — uma opção é usar parsers mais resistentes (`lxml`) ou usar endpoints oficiais quando disponíveis.
- CSV/Excel: o projeto salva em CSV compatível com Excel PT-BR. Se quiser exportar diretamente para `.xlsx`, inclua `openpyxl` e ajuste `pandas.DataFrame.to_excel()`.

## Troubleshooting (problemas comuns)
- Erro ao importar módulos: verifique se o virtualenv está ativado e se as dependências foram instaladas (`pip install -r requirements.txt`).
- Erro de permissão ao gravar em `data/`: verifique permissões do diretório e se o processo tem acesso de escrita.
- CSV com colunas em branco ou dados corrompidos: verifique os logs e `data/erros.csv` para entender qual fonte falhou.
- Timeout/HTTPError: tente aumentar `timeout` nas funções de requisição ou ajustar a política de retries em `site_utils.make_session()`.

## Sugestões de próximos passos
- Adicionar testes automatizados (pytest) para: parsing HTML, conversão de `DataPoint`, e escrita CSV.
- Implementar CI (GitHub Actions) que rode lint, type-check e testes.
- Separar configurações (timeouts, URLs, paths) para um arquivo `config` ou variáveis de ambiente.
- Capturar versões exatas das dependências (pinning) para reprodutibilidade em produção.

---

## Autor e contato
Projeto mantido por Gabriel-Ctrll. Para dúvidas ou melhorias, abrir issue/PR no repositório.

---
