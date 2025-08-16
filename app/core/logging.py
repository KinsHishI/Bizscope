from loguru import logger

logger.add("logs/app.log", rotation="10 MB", backtrace=True, diagnose=True)
