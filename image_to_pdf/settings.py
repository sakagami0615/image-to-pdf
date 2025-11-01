"""アプリケーション設定."""

from reportlab.lib.pagesizes import A4

# サポートする画像拡張子
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}

# PDFページサイズ（デフォルト: A4）
PDF_PAGE_SIZE = A4

# PDFページサイズを画像サイズに合わせるかどうか
# True: 画像サイズに合わせたページサイズ（余白なし）
# False: 固定サイズ（PDF_PAGE_SIZE）に合わせる（余白あり）
PDF_FIT_PAGE_TO_IMAGE = True

# PDF名に選択したルートフォルダ名を含めるかどうか
# True: 全パスを含む（例: prj-data-images.pdf）
# False: 画像フォルダ名のみ（例: images.pdf）
PDF_INCLUDE_ROOT_FOLDER_NAME = False

# GUIウィンドウサイズ
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 750

# 画像プレビューサイズ
PREVIEW_WIDTH = 700
PREVIEW_HEIGHT = 500

# 検索結果コンテナの高さ
RESULTS_CONTAINER_HEIGHT = 350

# ログ設定
LOG_DIR = "logs"
LOG_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
LOG_MESSAGE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
