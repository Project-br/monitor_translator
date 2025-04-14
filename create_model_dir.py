#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
モデルディレクトリ構造を作成するスクリプト
"""

import os

def create_model_dir():
    """モデルディレクトリ構造を作成する"""
    model_dir = os.path.join(
        "translator_main", 
        "translator", 
        "server_client", 
        "model",
        "m2m100_418M"
    )
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        print(f"モデルディレクトリを作成しました: {model_dir}")
    else:
        print(f"モデルディレクトリは既に存在します: {model_dir}")
    
    # 空のREADME.txtファイルを作成して、ディレクトリが含まれるようにする
    readme_path = os.path.join(model_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("このディレクトリには初回起動時に翻訳モデルがダウンロードされます。\n")
        f.write("This directory will be populated with translation model files on first launch.\n")
    
    print(f"README.txtファイルを作成しました: {readme_path}")

if __name__ == "__main__":
    create_model_dir()
