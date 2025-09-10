import csv
from langchain.schema import Document

class EmployeeRosterLoader:
    def __init__(self, path: str, encoding="utf-8"):
        self.path = path
        self.encoding = encoding

    def load(self):
        """
        CSVを行単位ではなく、部署ごとにまとめて1つのドキュメント化する。
        これにより「人事部の従業員一覧」などの問い合わせに対して、
        k=5でも9人以上の情報を返せるようになる。
        """
        departments = {}

        with open(self.path, encoding=self.encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                dept = row["部署"]
                # 従業員情報をより詳細かつ検索しやすい形式で結合
                emp_info = (
                    f"社員ID: {row['社員ID']}, "
                    f"氏名: {row['氏名（フルネーム）']}, "
                    f"性別: {row['性別']}, "
                    f"生年月日: {row['生年月日']}, "
                    f"年齢: {row['年齢']}, "
                    f"メールアドレス: {row['メールアドレス']}, "
                    f"従業員区分: {row['従業員区分']}, "
                    f"入社日: {row['入社日']}, "
                    f"部署: {row['部署']}, "
                    f"役職: {row['役職']}, "
                    f"スキルセット: {row['スキルセット']}, "
                    f"保有資格: {row['保有資格']}, "
                    f"大学名: {row['大学名']}, "
                    f"学部・学科: {row['学部・学科']}, "
                    f"卒業年月日: {row['卒業年月日']}"
                )
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append(emp_info)

        documents = []
        for dept, employees in departments.items():
            # 部署ごとに従業員情報を1つのテキストにまとめる
            # 部署名もテキスト内に含めることで、検索時の関連性を高める
            text = f"部署: {dept}の従業員情報:\n" + "\n".join(employees)
            documents.append(Document(page_content=text, metadata={"部署": dept, "source": self.path}))

        return documents