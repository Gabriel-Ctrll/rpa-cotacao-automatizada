import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session(
    retries: int = 3,
    backoff: float = 0.3,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Session:
    """
    Cria e retorna uma sessão HTTP configurada com política automática de retries.

    Esta função é usada para criar uma sessão HTTP resiliente, com tentativas automáticas
    de reconexão em caso de erros transitórios de rede ou respostas HTTP específicas
    (ex: 500, 502, 503, 504, 429).

    Args:
        retries (int, opcional): Número total de tentativas em falhas de requisição.
                                 Padrão: 3.
        backoff (float, opcional): Fator de tempo de espera exponencial entre tentativas.
                                   Exemplo: 0.3 → 0.3s, 0.6s, 1.2s...
                                   Padrão: 0.3.
        status_forcelist (tuple[int, ...], opcional): Lista de códigos HTTP que devem
                                                      acionar novo retry.
                                                      Padrão: (429, 500, 502, 503, 504).

    Returns:
        Session: Objeto `requests.Session` configurado com:
            - Política de retries (`Retry`);
            - Cabeçalho `User-Agent` padrão;
            - Suporte a HTTP e HTTPS.

    Exemplo:
        >>> from utils.site_utils import make_session
        >>> sessao = make_session()
        >>> resp = sessao.get("https://api.frankfurter.app/latest?from=USD")
        >>> print(resp.status_code)
        200
    """

    # Cria sessão persistente (reutilizável)
    session = requests.Session()

    # Define política de retry com backoff exponencial
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )

    # Adiciona adaptadores HTTP com suporte a retry
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Define um cabeçalho User-Agent padrão (importante para evitar bloqueios)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; RPA-Test/1.0; +https://github.com/yourname)"
    })

    return session