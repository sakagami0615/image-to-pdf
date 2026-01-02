"""ログ出力モジュール."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from .settings import LOG_DATE_FORMAT, LOG_DIR, LOG_MESSAGE_FORMAT, LOG_TIMESTAMP_FORMAT


class ErrorFileHandler(logging.Handler):
    """エラー発生時のみログファイルを作成するハンドラ."""

    def __init__(self):
        """ハンドラの初期化."""
        super().__init__()
        self.log_dir = Path(LOG_DIR)
        self.file_handler = None
        self.log_records = []  # エラー発生前のログを保持

    def emit(self, record):
        """ログレコードを処理する.

        Args:
            record: ログレコード
        """
        # エラーレベル未満のログは一時保存
        if record.levelno < logging.ERROR:
            self.log_records.append(record)
            return

        # エラーレベルのログが発生した場合
        if self.file_handler is None:
            # ログディレクトリを作成
            self.log_dir.mkdir(exist_ok=True)

            # ログファイル名（日時付き）
            timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
            log_file = self.log_dir / f"app_{timestamp}.log"

            # ファイルハンドラを作成
            self.file_handler = logging.FileHandler(log_file, encoding="utf-8")
            formatter = logging.Formatter(
                LOG_MESSAGE_FORMAT,
                datefmt=LOG_DATE_FORMAT,
            )
            self.file_handler.setFormatter(formatter)

            # 保存していたログをファイルに書き込む
            for log_record in self.log_records:
                self.file_handler.emit(log_record)
            self.log_records.clear()

        # 現在のエラーログをファイルに書き込む
        self.file_handler.emit(record)


def setup_logger(name: str = "image_to_pdf") -> logging.Logger:
    """ロガーをセットアップする.

    Args:
        name: ロガー名

    Returns:
        設定されたロガーオブジェクト
    """
    # ロガーを取得
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 既存のハンドラをクリア
    if logger.hasHandlers():
        logger.handlers.clear()

    # エラー時のみファイルに出力するハンドラを作成
    error_file_handler = ErrorFileHandler()
    error_file_handler.setLevel(logging.DEBUG)

    # コンソールハンドラを作成（エラーのみ表示）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        LOG_MESSAGE_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    console_handler.setFormatter(formatter)

    # ハンドラを追加
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    return logger
