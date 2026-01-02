# Image to PDF Converter

複数枚の画像をPDFファイルに変換するアプリケーション。

## 機能

- フォルダ内の画像を自動検索
- サブフォルダにも対応
- 画像の順序を上下ボタンで入れ替え可能
- フォルダごとにPDFファイルを生成
- 正規表現パターンによる画像のグループ化機能
- 複数のグループ化パターンを優先順位付きで管理
- PDF変換後の画像自動削除機能（ON/OFF可能）
- PDFページサイズの設定（画像サイズに合わせる/固定サイズ）
- サポートする画像拡張子のカスタマイズ
- モダンなGUI（Flet使用）
- プログレスバー表示
- エラーログ自動出力（logsフォルダ）

## 必要要件

- Python 3.10以上
- Poetry

## インストール

```bash
# 依存パッケージのインストール
poetry install
```

## 使い方

```bash
# アプリケーションの起動
poetry run python -m image_to_pdf 
```

## プロジェクト構成

```
image-to-pdf/
├── image_to_pdf/
│   ├── __init__.py
│   ├── __main__.py          # メインエントリポイント
│   ├── app.py               # アプリケーション起動
│   ├── gui.py               # GUIアプリケーション
│   ├── image_scanner.py     # 画像検索・解析
│   ├── pdf_converter.py     # PDF変換
│   ├── config_manager.py    # 設定管理
│   ├── settings.py          # デフォルト設定
│   ├── settings_dialog.py   # 設定ダイアログ
│   └── logger.py            # ログ出力
├── tests/                   # テストコード
├── logs/                    # ログファイル出力先
├── build_exe.py             # EXEビルドスクリプト
├── build_exe.spec           # PyInstallerビルド設定
├── pyproject.toml           # Poetryプロジェクト設定
└── README.md
```

## EXEファイルの作成

アプリケーションを実行可能なEXEファイルにビルドできます。

```bash
# EXEファイルをビルド
poetry run python build_exe.py

# または、PyInstallerを直接使用
poetry run pyinstaller build_exe.spec
```

ビルドが完了すると、`dist/ImageToPDF` (macOS/Linux) または `dist/ImageToPDF.exe` (Windows) が生成されます。

**注意:**

- ビルドには数分かかる場合があります
- 初回ビルド時は特に時間がかかります
- 生成された実行ファイルは単一ファイルで、他のPCでも実行可能です（Pythonのインストール不要）
- プラットフォーム固有: macでビルドした実行ファイルはmacでのみ、Windowsでビルドした実行ファイルはWindowsでのみ動作します

## テスト

プロジェクトには単体テストが含まれています。

```bash
# テストを実行
poetry run pytest

# カバレッジレポート付きでテストを実行
poetry run pytest --cov=image_to_pdf --cov-report=term-missing
```

## 開発ツール

プロジェクトでは、コード品質を維持するために以下のツールを使用しています。

```bash
# コードフォーマットとリント
poetry run ruff check image_to_pdf/
poetry run ruff format image_to_pdf/

# 型チェック
poetry run mypy image_to_pdf/

# pre-commitフックの設定（推奨）
poetry run pre-commit install
```

## 使用ライブラリ

- **Flet**: モダンなUIフレームワーク
- **PyInstaller**: 実行ファイル作成
- **Pillow**: 画像処理
- **ReportLab**: PDF生成
- **pytest**: テストフレームワーク（開発用）
- **pytest-cov**: カバレッジレポート（開発用）
- **ruff**: 高速なPythonリンター/フォーマッター（開発用）
- **mypy**: 静的型チェッカー（開発用）
- **pre-commit**: Gitフック管理（開発用）
