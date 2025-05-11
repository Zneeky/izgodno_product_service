import logging
import json
from uuid import UUID

llm_logger = logging.getLogger("llm_match")

def log_llm_decision(input_product: dict, candidates: list[dict], result: list[dict]):
    llm_logger.info(
        "LLM_MATCH_RESULT",  # ← this is just a label
        extra={
            "input_product": input_product,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "result": result
        }
    )
