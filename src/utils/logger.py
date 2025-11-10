import logging
import pandas as pd
from datetime import datetime

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Cria e retorna um logger configurado para uso no projeto.

    Este logger utiliza o `StreamHandler` para exibir logs no console (stdout),
    formatados com informações de tempo, nível, nome do módulo e mensagem.

    Args:
        name (str, opcional): Nome do logger, geralmente o nome do módulo chamador.
                              Por padrão, utiliza `__name__`.

    Returns:
        Logger: Instância configurada do logger pronta para uso.

    Exemplo:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Aplicação iniciada com sucesso.")
        2025-11-09 17:34:21,123 - INFO - meu_modulo - Aplicação iniciada com sucesso.
    """
    logger = logging.getLogger(name)

    # Evita adicionar múltiplos handlers ao mesmo logger (duplicando logs)
    if not logger.handlers:
        handler = logging.StreamHandler()

        # Define o formato dos logs (data, nível, nome e mensagem)
        formato = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        handler.setFormatter(logging.Formatter(formato))

        # Associa o handler e define o nível padrão (INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger

def log_error_to_sheet(source: str, error_message: str, path: str = "data/erros.csv"):
    """
    Registra erros de scraping ou execução em uma planilha CSV de auditoria.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    error_entry = {
        "data": timestamp,
        "origem": source,
        "mensagem": error_message,
    }

    try:
        try:
            existing_df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
            df = pd.concat([existing_df, pd.DataFrame([error_entry])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([error_entry])
            

        df.to_csv(path, index=False, sep=";", encoding="utf-8-sig")
        logging.warning(f"Erro registrado em {path}: {error_message}")
    except Exception as e:
        logging.exception(f"Falha ao registrar erro em planilha: {e}")