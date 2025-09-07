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
                emp_info = (
                    f"社員ID: {row['社員ID']}, "
                    f"氏名: {row['氏名（フルネーム）']}, "
                    f"役職: {row['役職']}, "
                    f"従業員区分: {row['従業員区分']}, "
                    f"スキルセット: {row['スキルセット']}, "
                    f"保有資格: {row['保有資格']}"
                )
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append(emp_info)

        documents = []
        for dept, employees in departments.items():
            # 部署ごとに従業員情報を1つのテキストにまとめる
            text = f"部署: {dept}\n従業員一覧:\n" + "\n".join(employees)
            documents.append(Document(page_content=text, metadata={"部署": dept}))

        return documents
