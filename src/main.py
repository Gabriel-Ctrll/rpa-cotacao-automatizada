from utils.logger import get_logger
from services.api_scraper import buscar_taxas_cambio  # ajuste o caminho conforme sua estrutura

logger = get_logger(__name__)


def main():
    """
    Função principal para testar a busca de taxas de câmbio.
    """
    logger.info("=== Iniciando teste da API de câmbio ===")

    try:
        # Define a moeda base que será usada na consulta
        base = "USD"

        # Chama a função principal do módulo
        taxas = buscar_taxas_cambio(base)

        # Exibe os resultados de forma organizada
        print(f"Taxas de câmbio com base em {base}:\n")
        for item in taxas:
            print(f"{item.base} → {item.target}: {item.rate:.4f} | Data: {item.timestamp.date()}")

        logger.info("=== Teste finalizado com sucesso ===")

    except RuntimeError as erro:
        logger.error("Erro durante a execução: %s", erro)
        print(f"Erro ao buscar taxas de câmbio: {erro}")

    except Exception as erro_inesperado:
        logger.exception("Erro inesperado: %s", erro_inesperado)
        print(f"Erro inesperado: {erro_inesperado}")


if __name__ == "__main__":
    main()