import sqlite3
import csv
import os
import unicodedata

# このモジュール内の相対パス解決のためのベースディレクトリ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "data", "db")
DATABASE_FILE = unicodedata.normalize('NFC', os.path.join(DATABASE_DIR, "employee_roster.db"))
CSV_FILE_PATH = unicodedata.normalize('NFC', os.path.join(BASE_DIR, "data", "社員について", "社員名簿.csv"))

def create_and_populate_db():
    """
    指定されたCSVファイルから従業員データを読み込み、SQLiteデータベースを作成・投入します。
    エラー処理も含まれます。
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS employees")
        cursor.execute("""
            CREATE TABLE employees (
                社員ID TEXT PRIMARY KEY,
                氏名 TEXT,
                性別 TEXT,
                生年月日 TEXT,
                年齢 INTEGER,
                メールアドレス TEXT,
                従業員区分 TEXT,
                入社日 TEXT,
                部署 TEXT,
                役職 TEXT,
                スキルセット TEXT,
                保有資格 TEXT,
                大学名 TEXT,
                学部_学科 TEXT,
                卒業年月日 TEXT
            )
        """)
        conn.commit()

        if not os.path.exists(CSV_FILE_PATH):
            raise FileNotFoundError(f"CSVファイル '{CSV_FILE_PATH}' が見つかりません。")

        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)

            column_mapping = {
                '社員ID': '社員ID',
                '氏名（フルネーム）': '氏名',
                '性別': '性別',
                '生年月日': '生年月日',
                '年齢': '年齢',
                'メールアドレス': 'メールアドレス',
                '従業員区分': '従業員区分',
                '入社日': '入社日',
                '部署': '部署',
                '役職': '役職',
                'スキルセット': 'スキルセット',
                '保有資格': '保有資格',
                '大学名': '大学名',
                '学部・学科': '学部_学科',
                '卒業年月日': '卒業年月日'
            }
            
            db_columns = [
                '社員ID', '氏名', '性別', '生年月日', '年齢', 'メールアドレス',
                '従業員区分', '入社日', '部署', '役職', 'スキルセット', '保有資格',
                '大学名', '学部_学科', '卒業年月日'
            ]

            for i, row_data in enumerate(reader):
                if len(row_data) != len(header):
                    print(f"警告: {CSV_FILE_PATH} の行 {i+2} のカラム数がヘッダーと一致しません。スキップします。")
                    continue

                row_dict = dict(zip(header, row_data))
                
                values = []
                for csv_col_name in column_mapping.keys():
                    values.append(row_dict.get(csv_col_name, "")) # CSVに存在しない場合は空文字列

                placeholders = ', '.join(['?' for _ in db_columns])
                insert_sql = f"INSERT INTO employees ({', '.join(db_columns)}) VALUES ({placeholders})"
                cursor.execute(insert_sql, values)
                
        conn.commit()
        print(f"データベース '{DATABASE_FILE}' が作成され、データが投入されました。")
        return True # 成功した場合はTrueを返す
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        return False
    except sqlite3.Error as e:
        print(f"データベース操作中にエラーが発生しました: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # このファイルが直接実行された場合のテスト用
    print("db_manager.py が直接実行されました。データベースの作成とデータ投入を開始します。")
    if create_and_populate_db():
        print("処理が成功しました。")
    else:
        print("処理中にエラーが発生しました。")