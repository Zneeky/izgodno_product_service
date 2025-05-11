import logging
import logging.config
import os
import json_log_formatter

class CustomJSONFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message, extra, record):
        extra['message'] = message  # 🔁 ensure the event name appears
        extra['timestamp'] = self.formatTime(record, self.datefmt)
        extra['level'] = record.levelname
        extra['logger'] = record.name
        return extra

def setup_logging(app_log_file='logs/app.log', llm_log_file='logs/llm.log'):
    os.makedirs(os.path.dirname(app_log_file), exist_ok=True)
    os.makedirs(os.path.dirname(llm_log_file), exist_ok=True)

    formatter = CustomJSONFormatter()

    # Main application log handler
    app_handler = logging.FileHandler(app_log_file)
    app_handler.setFormatter(formatter)

    # LLM-specific logger
    llm_handler = logging.FileHandler(llm_log_file)
    llm_handler.setFormatter(formatter)

    # Configure root logger for app
    logging.basicConfig(
        level=logging.INFO,
        handlers=[app_handler]
    )

    # Configure the `llm_match` logger separately
    llm_logger = logging.getLogger("llm_match")
    llm_logger.setLevel(logging.INFO)
    llm_logger.addHandler(llm_handler)
    llm_logger.propagate = False  # Prevent LLM logs from also going to app.log
