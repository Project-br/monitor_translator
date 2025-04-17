#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ENJAPP 翻訳ツール起動スクリプト

このスクリプトは翻訳サーバーを別プロセスで起動し、
その後にモニター翻訳ツールを起動します。

主な機能:
- 翻訳サーバーの起動と管理
- モニター翻訳ツールの起動
- コマンドライン引数による動作切り替え
- アプリケーション終了時のリソースクリーンアップ
"""

import os
import sys
import subprocess
import time
import signal
import atexit
import platform
import requests
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('enjapp')

# グローバル変数として翻訳サーバープロセスを保持
server_process = None

def get_project_root():
    """
    プロジェクトのルートディレクトリを取得します。
    """
    # このスクリプトの場所を基準にルートディレクトリを特定
    return os.path.dirname(os.path.abspath(__file__))

def get_python_executable():
    """
    適切なPython実行ファイルを取得します。
    仮想環境内で実行されている場合はその環境のPythonを使用します。
    """
    # 仮想環境内で実行されている場合
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        if platform.system() == 'Windows':
            return os.path.join(sys.prefix, 'Scripts', 'python.exe')
        else:
            return os.path.join(sys.prefix, 'bin', 'python')
    else:
        # 仮想環境外の場合は現在のPython実行ファイルを使用
        return sys.executable

def cleanup_server():
    """
    翻訳サーバープロセスをクリーンアップする関数
    
    アプリケーション終了時に、翻訳サーバープロセスを適切に終了させます。
    WindowsとUnix系 OSの両方に対応しています。
    
    Returns:
        None
    """
    global server_process
    if server_process:
        logger.info("翻訳サーバーを終了しています...")
        try:
            if platform.system() == 'Windows':
                # Windowsの場合はTASKKILLを使用してプロセスを強制終了
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(server_process.pid)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug(f"Windowsプロセス終了: PID {server_process.pid}")
            else:
                # Unix系の場合はシグナルを送信して正常終了を促す
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                server_process.wait(timeout=5)  # 最大5秒待機
                logger.debug(f"Unixプロセス終了: PID {server_process.pid}")
        except Exception as e:
            logger.error(f"サーバー終了中にエラーが発生しました: {e}")
        finally:
            server_process = None
            logger.info("翻訳サーバーを終了しました")

def start_translation_server():
    """
    翻訳サーバーを起動する関数
    
    戻り値:
        subprocess.Popen: 起動したサーバープロセス
    """
    global server_process
    
    # 既存のサーバープロセスをクリーンアップ
    cleanup_server()
    
    print("翻訳サーバーを起動しています...")
    
    # 現在の実行ファイルのディレクトリを取得
    current_dir = get_project_root()
    
    # PyInstallerでパッケージ化されているかどうかを確認
    is_packaged = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    
    # 翻訳サーバースクリプトのパスを構築
    if is_packaged:
        # パッケージ化されている場合は、_MEIPASSディレクトリからの相対パスを使用
        base_dir = sys._MEIPASS
        server_script = os.path.join(
            base_dir, 
            "translator_main", 
            "translator", 
            "server_client", 
            "translate_server_run.py"
        )
    else:
        # 通常実行の場合
        server_script = os.path.join(
            current_dir, 
            "translator_main", 
            "translator", 
            "server_client", 
            "translate_server_run.py"
        )
    
    # スクリプトが存在するか確認
    if not os.path.exists(server_script):
        print(f"エラー: 翻訳サーバースクリプトが見つかりません: {server_script}")
        return None
    
    # Pythonインタープリターのパスを取得
    python_exe = get_python_executable()
    
    # サーバーをバックグラウンドで起動
    try:
        # パッケージ化されている場合
        if is_packaged:
            # 現在の実行ファイル自体をサーバーモードで起動
            exe_path = sys.executable
            
            # 環境変数を設定してサーバーモードで起動
            env = os.environ.copy()
            env['ENJAPP_SERVER_MODE'] = '1'
            
            if platform.system() == 'Windows':
                server_process = subprocess.Popen(
                    [exe_path, "--server"],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Unix系OSの場合
                server_process = subprocess.Popen(
                    [exe_path, "--server"],
                    preexec_fn=os.setsid,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
        else:
            # 通常の実行（パッケージ化されていない場合）
            # 新しいプロセスグループで起動（Windows対応）
            if platform.system() == 'Windows':
                server_process = subprocess.Popen(
                    [python_exe, server_script],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Unix系OSの場合
                server_process = subprocess.Popen(
                    [python_exe, server_script],
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
        
        # サーバーの起動を確認するために待機
        print("サーバーの起動を確認しています...")
        max_retries = 60  # 無制限に近い値に設定（60回のリトライ）
        retry_interval = 2  # 秒
        server_ready = False
        
        for i in range(max_retries):
            # プロセスが終了していないか確認
            if server_process.poll() is not None:
                print("エラー: 翻訳サーバーの起動に失敗しました")
                return None
                
            # サーバーが応答するか確認
            try:
                response = requests.get("http://127.0.0.1:11451/docs", timeout=5)  # タイムアウトを5秒に増加
                if response.status_code == 200:
                    server_ready = True
                    break
            except requests.RequestException:
                pass
                
            print(f"サーバー起動待機中... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
            
        if not server_ready:
            print("警告: サーバーの応答を確認できませんでしたが、プロセスは実行中です")
        
        print(f"翻訳サーバープロセスが開始されました (PID: {server_process.pid})")
        
        # プログラム終了時にサーバーをクリーンアップするように登録
        atexit.register(cleanup_server)
        
        return server_process
        
    except Exception as e:
        print(f"サーバー起動中にエラーが発生しました: {e}")
        return None

def start_monitor_translator():
    """
    モニター翻訳ツールを起動する関数
    
    戻り値:
        int: 終了コード
    """
    print("モニター翻訳ツールを起動しています...")
    
    # PyInstallerでパッケージ化されているかどうかを確認
    is_packaged = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    
    # 現在の実行ファイルのディレクトリを取得
    current_dir = get_project_root()
    
    # 翻訳モニタースクリプトのパスを構築
    # PyQt5版のGUIを使用する場合
    use_pyqt = True  # PyQt5版を使用するフラグ
    
    if is_packaged:
        # パッケージ化されている場合は、直接モジュールをインポートして実行
        try:
            print("パッケージ化された環境でGUIを起動します...")
            from translator_main.translator.gui.qt_translator import main as qt_main
            # GUIをメインスレッドで実行
            return qt_main()
        except ImportError as e:
            print(f"GUIモジュールのインポートに失敗しました: {e}")
            # パスを調整して再試行
            base_dir = sys._MEIPASS
            sys.path.append(base_dir)
            try:
                from translator_main.translator.gui.qt_translator import main as qt_main
                return qt_main()
            except ImportError as e2:
                print(f"調整後もGUIモジュールのインポートに失敗しました: {e2}")
                return 1
        except Exception as e:
            print(f"GUI起動中に予期しないエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        # 通常実行の場合
        if use_pyqt:
            translator_script = os.path.join(
                current_dir, 
                "translator_main", 
                "translator", 
                "gui",
                "qt_translator.py"
            )
        else:
            # 従来のtkinter版
            translator_script = os.path.join(
                current_dir, 
                "translator_main", 
                "translator", 
                "translator.py"
            )
        
        # スクリプトが存在するか確認
        if not os.path.exists(translator_script):
            print(f"エラー: 翻訳モニタースクリプトが見つかりません: {translator_script}")
            return 1
        
        # 翻訳モニターを現在のプロセスで実行（制御を移す）
        translator_process = subprocess.run([sys.executable, translator_script])
        
        return translator_process.returncode

def main():
    """
    メイン実行関数
    
    コマンドライン引数を解析し、アプリケーションの動作モードを決定します。
    主に以下の2つのモードがあります：
    1. サーバーモード（--serverオプションまたはENJAPP_SERVER_MODE環境変数で指定）
    2. 通常モード（デフォルト）
    
    Returns:
        None
    """
    # コマンドライン引数を解析
    import argparse
    parser = argparse.ArgumentParser(description='ENJAPP 翻訳ツール')
    parser.add_argument('--server', action='store_true', help='サーバーモードで起動')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで起動（詳細なログ出力）')
    args = parser.parse_args()
    
    # デバッグモードの設定
    if args.debug:
        logging.getLogger('enjapp').setLevel(logging.DEBUG)
        logger.debug("デバッグモードが有効化されました")
    
    # サーバーモードで起動する場合
    if args.server or os.environ.get('ENJAPP_SERVER_MODE') == '1':
        logger.info("サーバーモードで起動します...")
        try:
            from translator_main.translator.server_client.translate_server_run import start_server
            logger.debug("翻訳サーバーモジュールのインポートに成功しました")
            start_server()
        except ImportError as e:
            logger.error(f"サーバーモジュールのインポートに失敗しました: {e}")
            # パッケージ化されている場合のパスを調整
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
                logger.debug(f"パッケージ化された環境を検出しました。パスを調整します: {base_dir}")
                sys.path.append(base_dir)
                try:
                    from translator_main.translator.server_client.translate_server_run import start_server
                    logger.debug("パス調整後に翻訳サーバーモジュールのインポートに成功しました")
                    start_server()
                except ImportError as e2:
                    logger.critical(f"調整後もサーバーモジュールのインポートに失敗しました: {e2}")
                    sys.exit(1)
            else:
                logger.critical("サーバーモジュールが見つかりません")
                sys.exit(1)
        except Exception as e:
            logger.critical(f"サーバー起動中に予期しないエラーが発生しました: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            sys.exit(1)
        return
    
    try:
        # 通常モードの起動処理
        logger.info("モニター翻訳ツールを起動します...")
        
        # モニター翻訳ツールを起動（サーバー起動情報を渡す）
        exit_code = start_monitor_translator()
        logger.debug(f"モニター翻訳ツールが終了しました。終了コード: {exit_code}")
        
        # 翻訳モニターの終了コードを返す
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("\nプログラムがユーザーによって中断されました")
    except Exception as e:
        logger.error(f"アプリケーション実行中にエラーが発生しました: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
    finally:
        # 明示的にサーバープロセスをクリーンアップ
        cleanup_server()

if __name__ == "__main__":
    main()