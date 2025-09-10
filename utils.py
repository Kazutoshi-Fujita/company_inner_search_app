"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent, Tool
import constants as ct

############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()

############################################################
# --- SQL Toolのセットアップ ---
############################################################
DATABASE_FILE = "./data/db/employee_roster.db"

# データベースファイルが存在しない場合は、DB作成スクリプトの実行を促す
if not os.path.exists(DATABASE_FILE):
    st.error(f"エラー: SQLiteデータベース '{DATABASE_FILE}' が見つかりません。")
    st.error("`create_db.py` を実行してデータベースを作成してください。")
    st.stop()

db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_FILE}")

sql_execute_tool = QuerySQLDatabaseTool(
    db=db,
    name="sql_executor",
    description="従業員名簿データベースに対するSQLクエリを実行し、従業員情報を取得する際に使用します。"
)

############################################################
# 関数定義
############################################################

def get_source_icon(source):
    """
    メッセージと一緒に表示するアイコンの種類を取得

    Args:
        source: 参照元のありか

    Returns:
        メッセージと一緒に表示するアイコンの種類
    """
    # 参照元がWebページの場合とファイルの場合で、取得するアイコンの種類を変える
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON
    
    return icon


def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def get_llm_response(chat_message):
    """
    LLMからの回答取得

    Args:
        chat_message: ユーザー入力値

    Returns:
        LLMからの回答
    """
    # RAGのRetrieverをツールとしてラップ
    # RAG RetrieverもツールとしてAgentに渡す
    rag_tool = Tool(
        name="rag_document_searcher",
        func=lambda query: st.session_state.retriever.invoke(query),
        description="社内文書を検索し、関連情報を見つける際に使用します。文書検索が必要な場合に利用してください。"
    )

    # Agentに提供するツールリスト
    # ここでRAGの検索ツールとSQL実行ツールを両方渡す
    tools = [sql_execute_tool, rag_tool]

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのプロンプトテンプレートを作成
    # （これはRAGのためのものなので、Agentのプロンプトとは別で管理する）
    question_generator_template = ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_generator_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # Agentのためのプロンプトテンプレート (RAGとSQLのどちらを使うかLLMが判断する)
    agent_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
            あなたは社内情報特化型のアシスタントです。ユーザーの質問に答えるために、提供されたツールを適切に選択して使用してください。
            - 従業員に関する質問（例: 一覧化、特定の情報）には `sql_executor` ツールを使用してください。
            - その他の社内文書に関する質問には `rag_document_searcher` ツールを使用してください。
            - 憶測で回答せず、ツールの情報に基づいて回答してください。
            - 回答はできる限り詳細に、Markdown形式で整形して表示してください。
            """),
            MessagesPlaceholder("chat_history"), # 会話履歴をAgentにも渡す
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    
    # OpenAI Tools Agentの作成
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)
    agent = create_openai_tools_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # LLMへのリクエストとレスポンス取得
    # AgentExecutorに会話履歴を渡す
    response = agent_executor.invoke({
        "input": chat_message,
        "chat_history": [
            HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]["answer"])
            for msg in st.session_state.messages if "content" in msg and msg["content"] # chat_historyからAgentExecutorのchat_history形式に変換
        ]
    })
    
    # LLMレスポンスを会話履歴に追加
    # Agentの最終出力をLLMの回答として扱う
    st.session_state.chat_history.extend([HumanMessage(content=chat_message), AIMessage(content=response["output"])])

    # Agentの出力を既存のdisplay_contact_llm_responseに合わせるために調整
    # ここは表示層の調整なので、必要に応じて`components.py`の`display_contact_llm_response`も修正が必要になる場合があります。
    # 例えば、SQLの結果を直接表示するのではなく、LLMが整形したテキストを返すようにする、など。
    # ここでは、Agentのoutputをそのまま'answer'として返しています。
    llm_response = {
        "answer": response["output"],
        "context": [] # SQL Toolの場合は、RAGのようなcontextは直接返さないため空とするか、SQLクエリと結果をcontextとして含める
    }
    
    return llm_response

