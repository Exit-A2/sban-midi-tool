from setuptools import setup, find_packages

setup(
    name="sbanmiditool",  # パッケージ名（pip listで表示される）
    version="1.0.0",  # バージョン
    description="すべあなのモールスや点字をMIDIに変換できるモジュール",  # 説明
    author="A2",  # 作者名
    packages=find_packages(),  # 使うモジュール一覧を指定する
    license="MIT",  # ライセンス
    install_requires=open("requirements.txt").readlines(),
)
