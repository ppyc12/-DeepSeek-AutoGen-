import autogen
from duckduckgo_search import DDGS

# ==========================================
# 1. 定义工具函数
# ==========================================
def search_web(query: str) -> str:
    print(f"\n[系统提示] 正在调用搜索工具，查询：{query} ...\n")
    try:
        # 使用 DuckDuckGo 搜索
        results = DDGS().text(query, max_results=3)
        if not results:
            return "未找到相关结果。"
        summary = ""
        for res in results:
            summary += f"标题: {res['title']}\n链接: {res['href']}\n摘要: {res['body']}\n\n"
        return summary
    except Exception as e:
        return f"搜索出错: {str(e)}"

# ==========================================
# 2. 配置两份 Config (修复报错的关键)
# ==========================================
config_list = [
    {
        "model": "deepseek-chat",
        "api_key": "",  # 【请在此处填入你的 Key】
        "base_url": "https://api.deepseek.com"
    }
]

# 配置 A：给【管理员】用的 (干净，没有工具)
llm_config_manager = {
    "config_list": config_list,
    "temperature": 0.7,
}

# 配置 B：给【辩手】用的 (带工具)
llm_config_agents = {
    "config_list": config_list,
    "temperature": 0.5,
    "timeout": 120,
    "functions": [
        {
            "name": "search_web",
            "description": "当需要查询实时数据、最新排名或具体事实时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    }
                },
                "required": ["query"],
            },
        }
    ],
}

# ==========================================
# 3. 定义角色
# ==========================================

# 正方：Java (使用带工具的配置)
pro_agent = autogen.AssistantAgent(
    name="Pro_Java",
    system_message="""
    你是正方辩手 (Java)。
    【极重要规则】：
    1. 你没有任何内部知识。所有数据必须通过 `search_web` 工具获取。
    2. 每一轮发言前，**必须先调用工具**，拿到结果后再发言。
    3. 不要输出 "(调用搜索工具...)" 这种文字，要真正的发送工具调用请求。
    """,
    llm_config=llm_config_agents,
)

# 反方：Python (使用带工具的配置)
con_agent = autogen.AssistantAgent(
    name="Pro_Python",
    system_message="""
    你是反方辩手 (Python)。
    【极重要规则】：
    1. 每一轮发言前，**必须先调用 search_web 工具** 查找反驳证据。
    2. 不要口头描述你在搜索，直接发起调用。
    """,
    llm_config=llm_config_agents,
)

# 裁判/执行者 (UserProxy)
# 只有裁判有能力真正执行代码，所以要把 function_map 给他
judge = autogen.UserProxyAgent(
    name="Judge",
    human_input_mode="NEVER",
    code_execution_config=False,
    function_map={"search_web": search_web}
)

# ==========================================
# 4. 创建群聊
# ==========================================
groupchat = autogen.GroupChat(
    agents=[judge, pro_agent, con_agent], 
    messages=[], 
    max_round=6
)

# 【核心修复】：Manager 使用不带工具的配置
manager = autogen.GroupChatManager(
    groupchat=groupchat, 
    llm_config=llm_config_manager # <--- 注意这里用 manager 配置
)

# ==========================================
# 5. 开始运行
# ==========================================
print("======== 增强版辩论赛（带联网功能）开始 ========")
judge.initiate_chat(
    manager,
    message="今天的辩题是：‘2024-2025年，Java 和 Python 谁的市场需求更大？’ 请双方利用搜索工具查找最新数据进行辩论。"
)