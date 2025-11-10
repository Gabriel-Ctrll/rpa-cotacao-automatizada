import pandas as pd
from typing import List, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def _to_dict(item: Any) -> dict:
    """
    Converte um item (dict ou objeto) para dicionário homogêneo esperado.
    Garante as chaves: timestamp, source, base, target, rate (rate como float).
    """
    # 1) já é dict
    if isinstance(item, dict):
        d = dict(item)  # cópia
    else:
        # 2) tem to_dict()
        if hasattr(item, "to_dict") and callable(getattr(item, "to_dict")):
            d = dict(item.to_dict())
        else:
            # 3) fallback para vars() / __dict__
            try:
                d = dict(vars(item))
            except TypeError:
                # impossível converter, retorna dict vazio
                d = {}

    # Normalizações de nomes que podem vir da fonte
    if "currency" in d and "target" not in d:
        d["target"] = d.pop("currency")

    # Alguns scrapers podem usar 'rate' como string com vírgula
    if "rate" in d and d["rate"] is not None:
        try:
            txt = str(d["rate"]).replace(".", "").replace(",", ".")
            d["rate"] = float(txt)
        except Exception:
            # tenta converter direto para float; se falhar, define NaN
            try:
                d["rate"] = float(d["rate"])
            except Exception:
                d["rate"] = None

    # Se não existir timestamp, colocamos o utcnow como fallback
    if "timestamp" not in d or d["timestamp"] in (None, ""):
        d["timestamp"] = datetime.utcnow().isoformat()

    # Garante campos mínimos mesmo que vazios
    for k in ("source", "base", "target", "rate"):
        d.setdefault(k, None)

    return d


def save_to_csv(data_points: List[Any], path: str = "data/output.csv", mode: str = "w"):
    """
    Salva uma lista de dicts ou objetos em CSV:
      - aceita dicts ou objetos com to_dict()/atributos
      - normaliza nomes (timestamp, source, base, target, rate)
      - renomeia colunas para PT-BR (data, origem, base, moeda, cotação)
      - formata data como dd/mm/YYYY
      - arredonda cotação a 4 casas e força numérico
      - salva com separador ';' e encoding utf-8-sig (compatível Excel PT-BR)
    """
    if not data_points:
        logger.warning("No data to save")
        return

    # converte todos os itens para dicionários homogeneizados
    records = []
    for item in data_points:
        try:
            rec = _to_dict(item)
            records.append(rec)
        except Exception as e:
            logger.warning("Falha ao converter item para dict: %s -- %s", item, e)

    if not records:
        logger.warning("Nenhum registro válido para salvar")
        return

    # cria DataFrame
    df = pd.DataFrame(records)

    # renomeia colunas para PT-BR e contempla 'target' ou 'moeda'
    rename_map = {
        "timestamp": "data",
        "source": "origem",
        "base": "base",
        "target": "moeda",
        "rate": "cotação"
    }
    df = df.rename(columns=rename_map)

    # Se houver coluna 'moeda' vazia e existir outra coluna útil, tenta ajustar
    if "moeda" not in df.columns and "currency" in df.columns:
        df = df.rename(columns={"currency": "moeda"})

    # Formata a coluna data (dd/mm/YYYY). Se não houver 'data', cria com hoje.
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%d/%m/%Y")
    else:
        df["data"] = datetime.utcnow().strftime("%d/%m/%Y")

    # Normaliza cotação para numérico e arredonda
    if "cotação" in df.columns:
        df["cotação"] = pd.to_numeric(df["cotação"], errors="coerce").round(4)

    # Garante ordem de colunas desejada, se existirem
    desired_order = ["data", "origem", "base", "moeda", "cotação"]
    cols = [c for c in desired_order if c in df.columns] + [c for c in df.columns if c not in desired_order]
    df = df.loc[:, cols]

    # Salva em CSV compatível com Excel PT-BR
    try:
        df.to_csv(path, index=False, mode=mode, sep=";", encoding="utf-8-sig")
        logger.info("Saved %d rows to %s", len(df), path)
    except Exception as e:
        logger.exception("Erro ao salvar CSV: %s", e)
        raise