from fastapi import FastAPI
from pydantic import BaseModel
import torch
import os
import sys
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer, GenerationConfig
import uvicorn
from dotenv import load_dotenv

# PyInstallerでパッケージ化されているかどうかを確認する関数
def is_packaged():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# .envファイルから環境変数を読み込む
try:
    if is_packaged():
        # パッケージ化されている場合は、_MEIPASSディレクトリからの相対パスを使用
        base_dir = sys._MEIPASS
        dotenv_path = os.path.join(base_dir, '.env')
    else:
        # 通常実行の場合
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f".envファイルを読み込みました: {dotenv_path}")
    else:
        print(f".envファイルが見つかりません: {dotenv_path}")
except Exception as e:
    print(f".envファイルの読み込み中にエラーが発生しました: {e}")

# GPU使用の設定を環境変数から取得
use_gpu = os.environ.get('USE_GPU', 'False').lower() in ('true', '1', 'yes')

app = FastAPI()

class InferenceRequest(BaseModel):
    text: str

# モデルとトークナイザーのディレクトリパス
try:
    if is_packaged():
        # パッケージ化されている場合は、_MEIPASSディレクトリからの相対パスを使用
        base_dir = sys._MEIPASS
        model_dir = os.path.join(base_dir, "translator_main", "translator", "server_client", "model", "m2m100_418M")
    else:
        # 通常実行の場合
        model_dir = os.path.join(os.path.dirname(__file__), "model", "m2m100_418M")
    
    print(f"モデルディレクトリ: {model_dir}")
except Exception as e:
    print(f"モデルディレクトリパスの解決中にエラーが発生しました: {e}")
    model_dir = os.path.join(os.path.dirname(__file__), "model", "m2m100_418M")

# モデルとトークナイザーのロード
try:
    if not os.path.exists(model_dir):
        print(f"モデルディレクトリが存在しないため、新規作成します: {model_dir}")
        os.makedirs(model_dir, exist_ok=True)
        print("モデルをダウンロードしています...")
        print("これには数分かかる場合があります。しばらくお待ちください...")
        # 進捗表示を追加
        print("ダウンロード中: トークナイザー")
        tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
        print("ダウンロード中: 翻訳モデル")
        model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
        print("モデルを保存しています...")
        tokenizer.save_pretrained(model_dir)
        model.save_pretrained(model_dir)
        print("モデルのダウンロードと保存が完了しました")
    else:
        print(f"既存のモデルを読み込んでいます: {model_dir}")
        tokenizer = M2M100Tokenizer.from_pretrained(model_dir)
        model = M2M100ForConditionalGeneration.from_pretrained(model_dir)
except Exception as e:
    print(f"モデルのロード中にエラーが発生しました: {e}")
    # フォールバック: オンラインからモデルをロード
    try:
        print("オンラインからモデルをロードします...")
        tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
        model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
    except Exception as e2:
        print(f"オンラインからのモデルロードにも失敗しました: {e2}")
        raise

if use_gpu:
    # GPU が使える場合は GPU を、使えない場合は CPU を利用する
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")  # ログ出力
    model.to(device)
else:
    print("CPU mode is enabled")

@app.post("/translate")
async def translate(request_data: InferenceRequest):
    input_text = request_data.text
    # ソース言語を英語に設定（必要に応じて変更）
    tokenizer.src_lang = "en"
    inputs = tokenizer(input_text, return_tensors="pt")
    
    # GPUを使用する場合のみ、入力テンソルをデバイスに転送
    if use_gpu:
        inputs = {k: v.to(device) for k, v in inputs.items()}
    
    generation_config = GenerationConfig(
        max_length=200,
        early_stopping=True,
        num_beams=5
    )

    try:
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.get_lang_id("ja"),
            generation_config=generation_config
        )
        translated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        return {"result": translated_text}
    except Exception as e:
        return {"error": str(e)}

def start_server():
    """
    翻訳サーバーを起動する関数
    app.pyから呼び出されるエントリーポイント
    """
    print("翻訳サーバーを起動します...")
    uvicorn.run(app, host="127.0.0.1", port=11451)

if __name__ == "__main__":
    start_server()
