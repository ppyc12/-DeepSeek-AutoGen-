import autogen

# 1. 配置 LLM (使用 DeepSeek)
# AutoGen 兼容 OpenAI 格式，所以我们把 base_url 改成 DeepSeek 的地址即可
config_list = [
    {
        "model": "deepseek-chat",  # 模型名称
        "api_key": "",  # 【重要】在这里填入你的 Key
        "base_url": "https://api.deepseek.com"       # DeepSeek 的 API 地址
    }
]

# 通用的配置参数
llm_config = {
    "config_list": config_list,
    "temperature": 0.7,  # 0.7 比较有创造力，适合辩论
    "timeout": 120,
}

# 2. 定义【正方】智能体
# system_message 定义了它的“人设”
pro_agent = autogen.AssistantAgent(
    name="Pro_Java",
    system_message="""
    你是正方辩手。你坚定地认为【Java 是最适合大型企业级开发的语言】。
    你的辩论风格：逻辑严密，喜欢引用设计模式、强类型安全、JVM生态作为论据。
    每次发言控制在 100 字以内，言辞犀利。
    """,
    llm_config=llm_config,
)

# 3. 定义【反方】智能体
con_agent = autogen.AssistantAgent(
    name="Pro_Python",
    system_message="""
    你是反方辩手。你坚定地认为【Python 才是现代开发的王者，Java 已经过时了】。
    你的辩论风格：激进，喜欢强调开发效率、AI/数据科学生态、语法简洁。
    你可以嘲笑 Java 代码臃肿。
    每次发言控制在 100 字以内。
    """,
    llm_config=llm_config,
)

# 4. 定义【裁判/管理员】智能体
# UserProxyAgent 通常作为人类代理，但这里我们把它设为自动模式，让它负责发起话题
judge = autogen.UserProxyAgent(
    name="Judge_Moderator",
    human_input_mode="NEVER",  # 设置为 NEVER 表示不需要你手动打字，全自动运行
    max_consecutive_auto_reply=6,  # 让它们最多对战 6 回合，省钱
    is_termination_msg=lambda x: "辩论结束" in x.get("content", ""),
    code_execution_config=False,  # 关闭代码执行功能（我们只需要说话，不需要运行代码）
    system_message="""
    你是辩论赛主席。
    你的任务是：
    1. 观察双方辩论。
    2. 每一轮都要确保话题不跑偏。
    3. 当辩论进行几轮后，你可以说“辩论结束”来停止对话。
    """,
)

# 5. 开始辩论！
# 由裁判发起，让正方先说话
print("======== 辩论开始：Java vs Python ========")
judge.initiate_chat(
    pro_agent,  # 裁判先对正方说话
    message="今天的辩题是：‘在2025年，大学生应该首选 Java 还是 Python 作为第一语言？’ 请正方先阐述观点。",
)