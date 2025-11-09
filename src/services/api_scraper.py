from datetime import datetime
from typing import Dict, List, Optional
from requests import Response, exceptions
from utils.site_utils import make_session
from models.model import DataPoint
from utils.logger import get_logger

logger = get_logger(__name__)


def _obter_resposta_api(url: str, timeout: int = 10) -> Response:
    """
    Faz a requisição GET para a URL e trata erros de transporte/HTTP.
    Retorna o objeto Response em caso de sucesso ou lança RuntimeError.
    """
    sessao = make_session()
    logger.debug("Fazendo requisição GET para %s", url)
    try:
        resp = sessao.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp
    except exceptions.Timeout as e:
        logger.error("Timeout ao acessar %s: %s", url, e)
        raise RuntimeError("Timeout ao acessar a API de câmbio.") from e
    except exceptions.ConnectionError as e:
        logger.error("Erro de conexão ao acessar %s: %s", url, e)
        raise RuntimeError("Falha de conexão com a API de câmbio.") from e
    except exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", "desconhecido")
        logger.error("Erro HTTP %s ao acessar %s: %s", status, url, e)
        raise RuntimeError(f"Erro HTTP {status} ao consultar a API.") from e
    except Exception as e:
        logger.exception("Erro inesperado ao acessar %s: %s", url, e)
        raise RuntimeError("Erro desconhecido ao acessar a API de câmbio.") from e


def _extrair_json(resp: Response) -> Dict:
    """
    Converte a resposta para JSON e valida a presença do campo 'rates'.
    Lança RuntimeError em caso de formato inválido ou dados incompletos.
    """
    try:
        dados = resp.json()
    except ValueError as e:
        logger.error("Resposta da API não é JSON válido.")
        raise RuntimeError("Resposta inválida: formato JSON incorreto.") from e

    if not dados or "rates" not in dados or not isinstance(dados["rates"], dict):
        logger.error("JSON da API está incompleto ou inválido: %s", dados)
        raise RuntimeError("A API retornou dados inválidos ou incompletos.")
    return dados


def _parsear_timestamp(data_str: Optional[str]) -> datetime:
    """
    Converte a string 'date' retornada pela API para datetime.
    Se a conversão falhar ou a string for None, retorna datetime.utcnow().
    """
    if not data_str:
        logger.debug("Campo 'date' ausente. Usando datetime.utcnow().")
        return datetime.utcnow()
    try:
        # API geralmente fornece 'YYYY-MM-DD'
        return datetime.fromisoformat(f"{data_str}T00:00:00")
    except Exception:
        logger.warning("Formato de data inválido '%s'. Usando datetime.utcnow().", data_str)
        return datetime.utcnow()


def _construir_datapoints(dados: Dict, timestamp: datetime, fonte: str = "api_frankfurter") -> List[DataPoint]:
    """
    Converte o dicionário 'rates' em uma lista de DataPoint,
    ignorando entradas inválidas e registrando avisos.
    """
    moeda_base = dados.get("base")
    taxas = dados["rates"]
    resultados: List[DataPoint] = []

    for codigo, valor in taxas.items():
        try:
            taxa_float = float(valor)
        except Exception as e:
            logger.warning("Taxa inválida para %s: %s (valor: %s)", codigo, e, valor)
            continue

        try:
            dp = DataPoint(
                timestamp=timestamp,
                source=fonte,
                base=moeda_base,
                target=codigo,
                rate=taxa_float,
            )
            resultados.append(dp)
        except Exception as e:
            logger.warning("Erro ao criar DataPoint para %s: %s", codigo, e)

    return resultados


def buscar_taxas_cambio(base: str = "USD") -> List[DataPoint]:
    """
    Função de alto nível que orquestra a consulta à API de câmbio
    e retorna uma lista de DataPoint com as taxas encontradas.

    Erros críticos lançam RuntimeError com mensagens descritivas.
    """
    url = f"https://api.frankfurter.app/latest?from={base}"
    logger.info("Iniciando busca de taxas com base %s", base)

    resp = _obter_resposta_api(url)
    dados = _extrair_json(resp)

    ts = _parsear_timestamp(dados.get("date"))
    datapoints = _construir_datapoints(dados, ts)

    if not datapoints:
        logger.warning("Nenhum DataPoint válido foi gerado a partir da resposta da API.")
        raise RuntimeError("A API não retornou nenhuma taxa válida.")

    logger.info("Busca finalizada: %d taxas processadas.", len(datapoints))
    return datapoints