import logging

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s"
)

# Buat instance logger
logger = logging.getLogger(__name__)