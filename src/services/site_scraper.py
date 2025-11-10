import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def scrape_xrates(base: str = "USD"):
    """
    Faz scraping da tabela de câmbio no site x-rates.com.
    Retorna uma lista de dicionários no formato:
    [
        {
            "timestamp": "2025-11-09T00:00:00",
            "source": "xrates_site",
            "base": "USD",
            "target": "EUR",
            "rate": 0.94
        },
        ...
    ]
    """
    url = f"https://www.x-rates.com/table/?from={base}&amount=1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        )
    }

    logger.info(f"Scraping {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao acessar o site: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    rates = []
    table = soup.select_one("table.tablesorter.ratesTable")

    if not table:
        logger.warning("Tabela de câmbio não encontrada!")
        return []

    for row in table.select("tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            currency = cols[0].get_text(strip=True)
            rate_text = cols[1].get_text(strip=True).replace(",", "")  # remove vírgula
            try:
                rate = float(rate_text)
            except ValueError:
                logger.warning(f"Não foi possível converter taxa: {rate_text}")
                continue

            rates.append({
                "timestamp": datetime.utcnow().isoformat(),
                "source": "xrates_site",
                "base": base,
                "target": currency,
                "rate": rate
            })

    logger.info(f"Scraped {len(rates)} taxas com sucesso")
    return rates