# src/utils/logger.py

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

class CustomLogger:
    _instance: Optional['CustomLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = "logs"):
        if not hasattr(self, 'logger'):
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.setup_logger()

    def setup_logger(self):
        """Setup logging configuration."""
        # Create timestamp for log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'crawler_{timestamp}.log'
        
        # Create logger
        self.logger = logging.getLogger('LaptopCrawler')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters and handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File Handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self.logger

    @classmethod
    def cleanup_old_logs(cls, days: int = 30):
        """Clean up log files older than specified days."""
        if cls._instance:
            current_time = datetime.now()
            for log_file in cls._instance.log_dir.glob('*.log'):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (current_time - file_time).days > days:
                    try:
                        log_file.unlink()
                    except Exception as e:
                        cls._instance.logger.error(f"Error deleting old log file {log_file}: {str(e)}")

