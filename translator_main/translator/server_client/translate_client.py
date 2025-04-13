import requests
import json

class TranslateClient:
    def __init__(self, server_url: str = "http://127.0.0.1:11451/translate"):
        """
        TranslateClient クラスの初期化

        :param server_url: 翻訳サーバーのURL
        """
        self.server_url = server_url

    def translate(self, text: str) -> str:
        """
        同期的に翻訳リクエストを送信し、結果を取得する

        :param text: 翻訳したいテキスト
        :return: 翻訳結果の文字列
        """
        try:
            response = requests.post(
                self.server_url, 
                json={"text": text}, 
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get("result", "翻訳結果が取得できませんでした。")
        except requests.Timeout:
            return "リクエストがタイムアウトしました。"
        except requests.RequestException as e:
            return f"リクエスト中にエラーが発生しました: {e}"

# TranslateClient クラスの使用例
def main():
    client = TranslateClient()
    text_to_translate = "Now I'll translate all the comments in the translator.py file from English to Japanese. I'll create a comprehensive edit that changes all the comments while preserving the code functionality."
    translated_text = client.translate(text_to_translate)
    print(f"翻訳結果: {translated_text}")

# エントリーポイント
if __name__ == "__main__":
    main()
