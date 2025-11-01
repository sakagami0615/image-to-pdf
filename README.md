# Image to PDF Converter

複数枚の画像をPDFファイルに変換するアプリケーション。

## 機能

- フォルダ内の画像を自動検索
- サブフォルダにも対応
- 画像の順序を上下ボタンで入れ替え可能
- フォルダごとにPDFファイルを生成
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
poetry run python run.py
```

または

```bash
# Poetry環境内で実行
poetry shell
python run.py
```

## プロジェクト構成

```
image-to-pdf/
├── image_to_pdf/
│   ├── __init__.py
│   ├── main.py              # メインエントリポイント
│   ├── gui.py               # GUIアプリケーション
│   ├── image_scanner.py     # 画像検索・解析
│   ├── pdf_converter.py     # PDF変換
│   └── logger.py            # ログ出力
├── logs/                    # ログファイル出力先
├── run.py                   # 実行用スクリプト
├── pyproject.toml          # Poetryプロジェクト設定
└── README.md
```

## EXEファイルの作成

アプリケーションを実行可能なEXEファイルにビルドできます。

```bash
# EXEファイルをビルド
poetry run python build_exe.py
```

ビルドが完了すると、`dist/ImageToPDF.exe` が生成されます。

**注意:**

- ビルドには数分かかる場合があります
- 初回ビルド時は特に時間がかかります
- 生成されたEXEファイルは単一ファイルで、他のPCでも実行可能です（Pythonのインストール不要）

## テスト

プロジェクトには単体テストが含まれています。

```bash
# テストを実行
poetry run pytest

# カバレッジレポート付きでテストを実行
poetry run pytest --cov=image_to_pdf --cov-report=term-missing
```

## 使用ライブラリ

- **Flet**: モダンなUIフレームワーク
- **PyInstaller**: EXEファイル作成
- **Pillow**: 画像処理
- **ReportLab**: PDF生成
- **pytest**: テストフレームワーク（開発用）
- **pytest-cov**: カバレッジレポート（開発用）
