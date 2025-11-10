from utils.logger import get_logger
from utils.output_utils import save_to_csv
from utils.logger import log_error_to_sheet
from services.api_scraper import buscar_taxas_cambio
from services.site_scraper import scrape_xrates

logger = get_logger(__name__)

def main():
    """
    Função principal para buscar taxas de câmbio de múltiplas fontes e salvar no CSV.
    """
    logger.info("=== Iniciando coleta de taxas de câmbio ===")

    base = "USD"
    todas_taxas = []

    # --- API SCRAPER ---
    try:
        taxas_api = buscar_taxas_cambio(base)
        if taxas_api:
            todas_taxas.extend(taxas_api)
            logger.info(f"API retornou {len(taxas_api)} taxas.")
        else:
            raise ValueError("API retornou lista vazia")
    except Exception as e:
        msg = f"Erro ao buscar da API: {e}"
        logger.error(msg)
        log_error_to_sheet("api_scraper", msg)

    # --- SITE SCRAPER ---
    try:
        taxas_site = scrape_xrates(base)
        if taxas_site:
            todas_taxas.extend(taxas_site)
            logger.info(f"Site X-Rates retornou {len(taxas_site)} taxas.")
        else:
            raise ValueError("Site retornou lista vazia")
    except Exception as e:
        msg = f"Erro ao buscar do site: {e}"
        logger.error(msg)
        log_error_to_sheet("site_scraper", msg)
        
    if todas_taxas:
        try:
            save_to_csv(todas_taxas, path="data/taxas_cambio.csv")
            logger.info("=== Processamento concluído com sucesso ===")
        except Exception as e:
            msg = f"Erro ao salvar CSV final: {e}"
            logger.error(msg)
            log_error_to_sheet("save_to_csv", msg)
    else:
        msg = "Nenhum dado de câmbio obtido de nenhuma fonte"
        logger.warning(msg)
        log_error_to_sheet("main", msg)

if __name__ == "__main__":
    main()