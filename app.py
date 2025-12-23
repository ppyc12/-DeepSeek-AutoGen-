import streamlit as st
import autogen
import json
import matplotlib.pyplot as plt
import numpy as np
import PyPDF2
import time
import re

# ==========================================
# 1. 页面与 CSS 配置
# ==========================================
st.set_page_config(page_title="AI 深度辩论引擎", layout="wide", page_icon="🧠")

st.markdown("""
<style>
    .stApp { font-family: "Microsoft YaHei", sans-serif; }
    .main-title {
        text-align: center; font-size: 3rem; font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4A90E2, #E94E77);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .seat-card {
        background-color: #f0f2f6; border-radius: 10px; padding: 20px;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px; color: #333333 !important;
        height: 100%; /* 统一高度 */
    }
    .seat-title { font-weight: bold; font-size: 1.2rem; }
    .seat-desc { color: #666666 !important; font-size: 0.9rem; }
    .tactical-console {
        background-color: #e8f4f8; padding: 15px; border-radius: 10px;
        border-left: 5px solid #4A90E2; margin-bottom: 20px;
        margin-top: 20px;
    }
    div[data-testid="stFragment"] > div { transition: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧠 AI 深度辩论引擎</div>', unsafe_allow_html=True)

# ==========================================
# 2. 核心功能区 (缓存 + 工具函数)
# ==========================================

@st.cache_data
def get_pdf_text(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        content = ""
        for page in reader.pages:
            content += page.extract_text()
        return content
    except:
        return ""

@st.cache_data
def summarize_doc(api_key, text):
    """AI 智能摘要"""
    if not text or not api_key: return ""
    input_text = text[:10000] 
    
    config_list = [{
        "model": "deepseek-chat", 
        "api_key": api_key, 
        "base_url": "https://api.deepseek.com",
        "api_type": "openai"
    }]
    
    client = autogen.OpenAIWrapper(config_list=config_list)
    prompt = f"请阅读以下文档，并提炼出 5-8 个核心论点、关键数据或争议焦点。文档内容：\n{input_text}"
    try:
        response = client.create(messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except:
        return text[:2000]

@st.cache_resource
def get_agents(api_key, context_text, pro_identity, con_identity):
    """
    初始化 Agents，支持动态身份设定。
    参数: pro_identity (正方人设), con_identity (反方人设)
    """
    base_config = [{
        "model": "deepseek-chat",
        "api_key": api_key,
        "base_url": "https://api.deepseek.com",
        "api_type": "openai",     
        "temperature": 0.7,       
        "max_tokens": 500, # 稍微放宽长度，让特定角色能发挥       
        "frequency_penalty": 0.6,
        "presence_penalty": 0.6
    }]
    
    analyst_config = [{
        "model": "deepseek-chat",
        "api_key": api_key,
        "base_url": "https://api.deepseek.com",
        "api_type": "openai",
        "temperature": 0.5,
        "max_tokens": 600
    }]
    
    stop_prompt = """
    【CRITICAL RULES】:
    1. DO NOT repeat the user's input or the opponent's argument.
    2. Start your argument DIRECTLY.
    3. ONLY generate ONE single turn.
    4. Speak in Chinese.
    """
    
    # 【核心修改】：将用户输入的身份注入到 System Prompt 中
    pro_prompt = f"【角色设定】：你是正方辩手，你的身份是【{pro_identity}】。\n【参考资料】：{context_text}\n请完全沉浸在你的角色中，使用该角色特有的视角、专业术语和语气进行辩论。{stop_prompt}"
    con_prompt = f"【角色设定】：你是反方辩手，你的身份是【{con_identity}】。\n【参考资料】：{context_text}\n请完全沉浸在你的角色中，使用该角色特有的视角、专业术语和语气进行辩论。{stop_prompt}"
    
    pro = autogen.AssistantAgent("Pro", system_message=pro_prompt, llm_config={"config_list": base_config})
    con = autogen.AssistantAgent("Con", system_message=con_prompt, llm_config={"config_list": base_config})
    
    analyst = autogen.AssistantAgent(
        "Analyst", 
        llm_config={"config_list": analyst_config}, 
        system_message="Strict judge. Output JSON ONLY."
    )
    
    return pro, con, analyst

# ==========================================
# 3. 状态管理
# ==========================================
if "chat_history" not in st.session_state: st.session_state.chat_history = [] 
if "round_index" not in st.session_state: st.session_state.round_index = 0 
if "debate_started" not in st.session_state: st.session_state.debate_started = False
if "doc_summary" not in st.session_state: st.session_state.doc_summary = ""
# 新增：存储用户设定的角色
if "pro_id" not in st.session_state: st.session_state.pro_id = "资深专家"
if "con_id" not in st.session_state: st.session_state.con_id = "犀利批评家"

# ==========================================
# 4. 侧边栏与启动逻辑
# ==========================================
with st.sidebar:
    st.header("⚙️ 会议控制台")
    api_key = st.text_input("DeepSeek API Key", value="sk-xxxxxxxxxxxxxxxx", type="password") 
    target_round = st.slider("计划发言总次数", 2, 10, 6) 
    
    st.markdown("---")
    st.header("📂 RAG 知识库")
    uploaded_file = st.file_uploader("上传参考文档 (PDF)", type=["pdf"])
    
    if uploaded_file is not None:
        raw_text = get_pdf_text(uploaded_file)
        if raw_text:
            if "sk-" in api_key and not st.session_state.doc_summary:
                with st.spinner("🧠 AI 正在阅读文档并生成摘要..."):
                    summary = summarize_doc(api_key, raw_text)
                    st.session_state.doc_summary = summary
                    st.success("✅ 摘要已生成")
            elif not st.session_state.doc_summary:
                 st.session_state.doc_summary = raw_text[:3000]

    st.markdown("---")
    if st.button("🔄 重置辩论", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.round_index = 0
        st.session_state.debate_started = False
        st.rerun()

# ==========================================
# 5. 主界面布局 (输入区)
# ==========================================

# 动态显示席位卡片 (如果辩论开始了，显示设定好的角色；没开始显示默认)
display_pro = st.session_state.pro_id if st.session_state.debate_started else "待定角色..."
display_con = st.session_state.con_id if st.session_state.debate_started else "待定角色..."

st.markdown("### 🏛️ 参会嘉宾介绍")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="seat-card" style="border-top:5px solid #4A90E2;"><div style="font-size:40px;">👨‍💼</div><div class="seat-title" style="color:#4A90E2;">正方代表</div><div class="seat-desc">{display_pro}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="seat-card" style="border-top:5px solid #FFD700;"><div style="font-size:40px;">⚖️</div><div class="seat-title" style="color:#D4AF37;">首席裁判</div><div class="seat-desc">铁面无私 | 数据量化</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="seat-card" style="border-top:5px solid #E94E77;"><div style="font-size:40px;">👩‍💻</div><div class="seat-title" style="color:#E94E77;">反方代表</div><div class="seat-desc">{display_con}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

if not st.session_state.debate_started:
    # 1. 议题输入
    default_topic = "基于文档进行辩论" if st.session_state.doc_summary else "2025年，全栈工程师会被 AI 取代吗？"
    topic = st.text_input("1️⃣ 会议议题：", value=default_topic)
    
    # 2. 角色自定义 (分两列)
    col_p, col_c = st.columns(2)
    with col_p:
        # 默认值可以设得比较通用
        user_pro_id = st.text_input("2️⃣ 正方角色身份 (Pro Identity)", value="资深技术架构师")
    with col_c:
        user_con_id = st.text_input("3️⃣ 反方角色身份 (Con Identity)", value="AI 安全伦理专家")
    
    # 3. 启动按钮
    if st.button("🔥 开启圆桌会议 (初始化)", use_container_width=True):
        if "sk-" not in api_key:
            st.error("请输入 API Key")
        else:
            st.session_state.debate_started = True
            st.session_state.topic = topic
            # 保存用户输入的身份
            st.session_state.pro_id = user_pro_id
            st.session_state.con_id = user_con_id
            
            init_msg = f"议题：‘{topic}’。请正方发言，反方反驳。"
            st.session_state.chat_history.append({
                "role": "user", "content": init_msg, "speaker": "System", "is_animated": True
            })
            st.rerun()

# ==========================================
# 6. 核心逻辑 (Fragment 局部刷新)
# ==========================================

@st.fragment 
def debate_ui_fragment():
    if not st.session_state.debate_started:
        return

    context_data = st.session_state.doc_summary if st.session_state.doc_summary else ""
    rag_context = f"【核心参考资料】：\n{context_data}" if context_data else ""
    
    # 【核心调用】：传入用户设定的身份
    pro_agent, con_agent, analyst_agent = get_agents(api_key, rag_context, st.session_state.pro_id, st.session_state.con_id)

    # --- A. 渲染历史 ---
    st.markdown("### 🎙️ 辩论实况")
    chat_container = st.container()
    
    with chat_container:
        for idx, msg in enumerate(st.session_state.chat_history):
            speaker = msg.get('speaker', 'Unknown')
            content = msg['content']
            round_num = msg.get('round', '-')
            already_animated = msg.get("is_animated", False)

            if speaker == "Instruction":
                st.warning(f"🕵️ {content}")
                st.session_state.chat_history[idx]["is_animated"] = True
            elif speaker == "System": continue
            elif speaker == "Pro":
                col_left, col_mid, col_right = st.columns([10, 1, 10])
                with col_left:
                    # 显示时带上角色名，增加沉浸感
                    full_text = f"**🟦 正方 ({st.session_state.pro_id}):**\n\n{content}"
                    if not already_animated:
                        message_box = st.empty()
                        current_text = ""
                        for char in full_text:
                            current_text += char
                            message_box.info(current_text) 
                            time.sleep(0.03) 
                        st.session_state.chat_history[idx]["is_animated"] = True
                    else:
                        st.info(full_text)
            elif speaker == "Con":
                col_left, col_mid, col_right = st.columns([10, 1, 10])
                with col_right:
                    full_text = f"**🟥 反方 ({st.session_state.con_id}):**\n\n{content}"
                    if not already_animated:
                        message_box = st.empty()
                        current_text = ""
                        for char in full_text:
                            current_text += char
                            message_box.error(current_text)
                            time.sleep(0.03)
                        st.session_state.chat_history[idx]["is_animated"] = True
                    else:
                        st.error(full_text)

    st.markdown("---")

    # --- B. 控制台 ---
    if st.session_state.round_index < target_round:
        
        next_is_pro = (st.session_state.round_index % 2 == 0)
        # 动态显示下一位发言者的身份
        next_role_name = st.session_state.pro_id if next_is_pro else st.session_state.con_id
        next_color = "#4A90E2" if next_is_pro else "#E94E77"
        current_speaker_tag = "Pro" if next_is_pro else "Con"
        
        st.markdown(f"""
        <div class="tactical-console">
            <h3 style="margin:0; color: #333;">🕹️ 战术指挥台</h3>
            <p>下一轮发言方：<strong style="color:{next_color}">{next_role_name}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        col_input, col_btn = st.columns([3, 1])
        
        with col_input:
            key_id = f"input_{st.session_state.round_index}"
            user_instruction = st.text_input("💡 递纸条 (输入指令干预下一轮发言)", 
                                           key=key_id,
                                           placeholder=f"给 {next_role_name} 的秘密指令...")
        
        with col_btn:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            btn_label = f"▶️ 执行第 {st.session_state.round_index + 1} 轮发言"
            
            if st.button(btn_label, use_container_width=True):
                
                # 插入锦囊
                if user_instruction:
                    instruction_msg = f"【给 {next_role_name} 的独家指令】：{user_instruction}"
                    st.session_state.chat_history.append({
                        "role": "user", "content": instruction_msg, "speaker": "Instruction", "is_animated": True
                    })
                    st.toast(f"锦囊已注入给 {next_role_name}！")
                
                # 生成回复
                speaker_agent = pro_agent if next_is_pro else con_agent
                
                with st.spinner(f"{next_role_name} 正在深度思考..."):
                    try:
                        clean_history = []
                        total_msgs = len(st.session_state.chat_history)
                        
                        for i, m in enumerate(st.session_state.chat_history):
                            m_speaker = m.get('speaker', 'Unknown')
                            
                            # 角色映射
                            if m_speaker == current_speaker_tag:
                                mapped_role = "assistant"
                            elif m_speaker == "Instruction":
                                mapped_role = "user"
                            else:
                                mapped_role = "user"

                            if m_speaker == "Instruction":
                                if i == total_msgs - 1: 
                                     hidden_prompt = f" {m['content']} \n(【强制】：只输出一轮发言，不要复述指令！)"
                                     clean_history.append({"role": "user", "content": hidden_prompt})
                            else:
                                clean_history.append({"role": mapped_role, "content": m["content"]})
                        
                        reply = speaker_agent.generate_reply(messages=clean_history)
                        if not reply: reply = "（沉默）"
                        
                        st.session_state.chat_history.append({
                            "role": "user", 
                            "content": reply,
                            "speaker": current_speaker_tag, 
                            "round": st.session_state.round_index + 1,
                            "is_animated": False 
                        })
                        
                        st.session_state.round_index += 1
                        st.rerun() 
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- C. 评分 ---
    else:
        st.success("✅ 辩论结束！")
        if st.button("⚖️ 请求裁判裁决", use_container_width=True):
             with st.spinner("裁判正在回顾全场..."):
                clean_content_only = [m['content'] for m in st.session_state.chat_history if m.get('speaker') != "Instruction"]
                history_text = str(clean_content_only)
                
                prompt = f"""
                Review debate history: {history_text}
                Evaluate based on the identity: Pro={st.session_state.pro_id}, Con={st.session_state.con_id}.
                Output JSON ONLY:
                {{
                    "Pro": {{"Logic": 85, "Evidence": 90, "Expression": 88}},
                    "Con": {{"Logic": 80, "Evidence": 85, "Expression": 92}},
                    "Winner": "Pro",
                    "Comment": "Analysis."
                }}
                """
                try:
                    res = analyst_agent.generate_reply(messages=[{"role": "user", "content": prompt}])
                    match = re.search(r'\{.*\}', res, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        
                        c_res1, c_res2 = st.columns([2, 3])
                        with c_res1:
                            winner_color = "#4A90E2" if data['Winner'] == "Pro" else "#E94E77"
                            winner_text = f"🟦 正方 ({st.session_state.pro_id})" if data['Winner'] == "Pro" else f"🟥 反方 ({st.session_state.con_id})"
                            st.markdown(f"""
                            <div style="background-color:{winner_color}; padding:20px; border-radius:10px; color:white; text-align:center;">
                                <h3>🏆 胜者</h3><h1>{winner_text}</h1>
                            </div>
                            <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-top:15px; color:#333; border-left: 5px solid {winner_color};">
                                <b>📝 点评：</b> {data['Comment']}
                            </div>
                            """, unsafe_allow_html=True)
                        with c_res2:
                            categories = ['Logic', 'Evidence', 'Expression']
                            pro_scores = [int(data['Pro'][c]) for c in categories]
                            con_scores = [int(data['Con'][c]) for c in categories]
                            pro_scores += pro_scores[:1]; con_scores += con_scores[:1]
                            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
                            angles += angles[:1]
                            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
                            ax.set_ylim(0, 100)
                            ax.plot(angles, pro_scores, 'o-', color='#4A90E2', label='Pro')
                            ax.fill(angles, pro_scores, alpha=0.2, color='#4A90E2')
                            ax.plot(angles, con_scores, 'o-', color='#E94E77', label='Con')
                            ax.fill(angles, con_scores, alpha=0.2, color='#E94E77')
                            ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
                            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
                            st.pyplot(fig)
                    else: st.error("评分解析失败")
                except Exception as e: st.error(f"评分失败: {e}")

if st.session_state.debate_started:
    debate_ui_fragment()