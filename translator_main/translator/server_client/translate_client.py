import requests
import json
import time
import sys
import os

# PyInstallerでパッケージ化されているかどうかを確認する関数
def is_packaged():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

class TranslateClient:
    def __init__(self, server_url: str = "http://127.0.0.1:11451/translate"):
        """
        TranslateClient クラスの初期化

        :param server_url: 翻訳サーバーのURL
        """
        self.server_url = server_url
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        self.internal_translator = None
        
        # パッケージ化されている場合は内部翻訳機能を初期化
        if is_packaged():
            try:
                from .model.translator_model import TranslatorModel
                self.internal_translator = TranslatorModel()
                print("内部翻訳モデルを初期化しました")
            except ImportError as e:
                print(f"内部翻訳モデルの初期化に失敗しました: {e}")
                print("サーバー接続モードで動作します")
                self.internal_translator = None
            except Exception as e:
                print(f"内部翻訳モデル初期化中にエラーが発生しました: {e}")
                print("サーバー接続モードで動作します")
                self.internal_translator = None

    def translate(self, text: str) -> str:
        """
        同期的に翻訳リクエストを送信し、結果を取得する

        :param text: 翻訳したいテキスト
        :return: 翻訳結果の文字列
        """
        if not text or text.strip() == "":
            return "翻訳するテキストが空です。"
        
        # 改行を特殊なマーカーに置き換え（翻訳サーバーが改行を維持しない場合の対策）
        NEWLINE_MARKER = "[NEWLINE_MARKER_XYZ]"
        text_with_markers = text.replace("\n", NEWLINE_MARKER)
        
        # パッケージ化されていて内部翻訳機能が利用可能な場合
        if is_packaged() and self.internal_translator:
            try:
                result = self.internal_translator.translate(text_with_markers)
                # 翻訳結果の特殊マーカーを改行に戻す
                return result.replace(NEWLINE_MARKER, "\n")
            except Exception as e:
                print(f"内部翻訳処理でエラーが発生しました: {e}")
                print("サーバー接続モードにフォールバックします")
        
        # リトライ処理を実装
        for attempt in range(self.max_retries):
            try:
                print(f"翻訳サーバーに接続を試みています... (試行 {attempt + 1}/{self.max_retries})")
                response = requests.post(
                    self.server_url, 
                    json={"text": text_with_markers}, 
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                translated_text = result.get("result", "翻訳結果が取得できませんでした。")
                # 翻訳結果の特殊マーカーを改行に戻す
                return translated_text.replace(NEWLINE_MARKER, "\n")
            except requests.Timeout:
                print(f"リクエストがタイムアウトしました。再試行します... ({attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except requests.ConnectionError as e:
                print(f"サーバー接続エラー: {e}")
                print(f"翻訳サーバーが起動していない可能性があります。再試行します... ({attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except requests.RequestException as e:
                print(f"リクエスト中にエラーが発生しました: {e}")
                if attempt < self.max_retries - 1:
                    print(f"再試行します... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
            
        # すべての試行が失敗した場合
        return "翻訳サーバーに接続できませんでした。サーバーが起動しているか確認してください。"

# TranslateClient クラスの使用例
def main():
    client = TranslateClient()
    text_to_translate = "Now I'll translate all the comments in the translator.py file from English to Japanese. I'll create a comprehensive edit that changes all the comments while preserving the code functionality."
    translated_text = client.translate(text_to_translate)
    print(f"翻訳結果: {translated_text}")

# エントリーポイント
if __name__ == "__main__":
    main()
