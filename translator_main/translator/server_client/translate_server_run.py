from fastapi import FastAPI
from pydantic import BaseModel
import torch
import os
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer, GenerationConfig
import uvicorn
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

# GPU使用の設定を環境変数から取得
use_gpu = os.environ.get('USE_GPU', 'False').lower() in ('true', '1', 'yes')

app = FastAPI()

class InferenceRequest(BaseModel):
    text: str

# モデルとトークナイザーのディレクトリパス
model_dir = os.path.join(os.path.dirname(__file__), "model", "m2m100_418M")

# モデルとトークナイザーのロード
if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
    tokenizer.save_pretrained(model_dir)
    model.save_pretrained(model_dir)
else:
    tokenizer = M2M100Tokenizer.from_pretrained(model_dir)
    model = M2M100ForConditionalGeneration.from_pretrained(model_dir)

if use_gpu:
    # GPU が使える場合は GPU を、使えない場合は CPU を利用する
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")  # ログ出力
    model.to(device)

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=11451)
