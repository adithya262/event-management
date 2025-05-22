import sys
import json
from datetime import datetime
from loguru import logger
from app.core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware
import time

class CustomizeLogger:
    @classmethod
    def make_logger(cls, config_path: str):
        config = cls.load_logging_config(config_path)
        logging_config = config.get('logger')

        logger = cls.customize_logging(
            filepath=logging_config.get('path'),
            level=logging_config.get('level'),
            retention=logging_config.get('retention'),
            rotation=logging_config.get('rotation'),
            format=logging_config.get('format')
        )
        return logger

    @classmethod
    def customize_logging(cls,
                        filepath: str,
                        level: str,
                        rotation: str,
                        retention: str,
                        format: str
    ):
        logger.remove()
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format
        )
        logger.add(
            str(filepath),
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format
        )
        return logger

    @classmethod
    def load_logging_config(cls, config_path):
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.start_time = time.time()
        # Log request
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - request.state.start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)}"
            )
            raise

# Initialize logger
logger = CustomizeLogger.make_logger("logging_config.json") 