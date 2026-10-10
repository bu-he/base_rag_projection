// ============================================================
// RAG 问答前端 · 接口调用逻辑（带登录态）
// ============================================================
// 接口约定（后端在 api/router/ 下，除登录注册外都要带 Authorization 头）：
//   POST /auth/register       {"username","password"(≥8位)} → {"message","user":{...}}
//   POST /auth/login          {"username","password"}       → {"token": "eyJ..."}
//   POST /agent/stream        JSON: {"query","session_id"}  → SSE：首条 {"session_id":N}，
//                                                        之后逐条 {"content"}，出错 {"error"}，结尾 [DONE]
//                                                        （智能体自动决策：闲聊直答，产品问题先检索知识库）
//   GET  /session/{id}/messages  拉取该会话历史              → [{"role","content"}, ...]
//   DELETE /session/{id}      删除会话（真清空）              → {"message"}
//   POST /document/upload     multipart，字段名 file          → {"message","filename"}
//   POST /document/ingest     无参数                          → {"message"}
// 运行方式：在 fronted 目录下执行  python -m http.server 8080
// 然后浏览器访问 http://localhost:8080（必须是 localhost，不能是 127.0.0.1）
// 未登录 / 登录过期会自动跳转 login.html
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

// ---------- 登录态 & 会话 ID 管理（localStorage 持久化） ----------
function getToken() {
  return localStorage.getItem("rag_token");
}
function getSessionId() {
  const v = localStorage.getItem("rag_session_id");
  return v ? Number(v) : null;
}
function saveSessionId(id) {
  localStorage.setItem("rag_session_id", String(id));
}
function clearSessionId() {
  localStorage.removeItem("rag_session_id");
}

// 统一请求封装：自动带 Authorization 头；401（未登录/token 过期）统一清场并踢回登录页
// 所有需要登录的接口都必须走这个函数，别再裸用 fetch
async function authFetch(url, options = {}) {
  if (!getToken()) {
    location.replace("login.html");
    throw new Error("未登录");
  }
  const headers = Object.assign({}, options.headers || {});
  headers["Authorization"] = "Bearer " + getToken();
  const res = await fetch(url, Object.assign({}, options, { headers }));
  if (res.status === 401) {
    // token 过期或无效：清登录态回登录页（session_id 先留着，同账号重登还能续上）
    localStorage.removeItem("rag_token");
    localStorage.removeItem("rag_username");
    location.replace("login.html");
    throw new Error("登录已过期，请重新登录");
  }
  return res;
}

// ---------- DOM ----------
const chatArea = document.getElementById("chatArea");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const ingestBtn = document.getElementById("ingestBtn");
const clearBtn = document.getElementById("clearBtn");
const currentUser = document.getElementById("currentUser");
const logoutBtn = document.getElementById("logoutBtn");
const newSessionBtn = document.getElementById("newSessionBtn");
const sessionList = document.getElementById("sessionList");
const modelStatus = document.getElementById("modelStatus");

// 模型是否就绪（由 /health 轮询驱动）：就绪前禁用发送按钮
let modelReady = false;

// ---------- 工具函数 ----------

// 往聊天区追加一条消息，返回该 DOM 元素
// role: user / assistant / system / error
// msgId: 数据库消息 id（历史消息有；流式生成的新消息没有，刷新后才有）
function appendMessage(role, text, msgId = null) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  if (msgId !== null) {
    const del = document.createElement("button");
    del.className = "msg-del";
    del.textContent = "×";
    del.title = "删除这条消息";
    del.addEventListener("click", () => deleteMessage(msgId, div));
    div.appendChild(del);
  }
  chatArea.appendChild(div);
  scrollToBottom();
  return div;
}

// 删除单条消息：调后端 DELETE /message/{id}，成功后从页面移除
async function deleteMessage(id, el) {
  if (!confirm("确定删除这条消息吗？")) return;
  try {
    const res = await authFetch(`${API_BASE}/message/${id}`, { method: "DELETE" });
    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }
    el.remove();
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  }
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

// 把输入框和发送按钮禁用/启用（防止重复提交）
// 注意：模型未就绪（modelReady=false）时发送按钮永远禁用，与 loading 叠加
function setLoading(loading) {
  sendBtn.disabled = loading || !modelReady;
  queryInput.disabled = loading;
  if (!loading) queryInput.focus();
}

// ---------- 模型就绪状态（配合后端 /ready 就绪探针） ----------

// 轮询 /ready：loading → 提示 + 禁用发送；ok → 显示就绪并停止轮询
// /ready = 模型就绪探针（200 就绪 / 503 还在加载）；/health 只查进程存活，永远 ok，不能用来判断模型
// 注意：ready 是公开接口，不走 authFetch（避免 401 踢回登录页）
function pollModelStatus() {
  const tick = async () => {
    let status;
    try {
      const res = await fetch(`${API_BASE}/ready`);
      status = res.ok ? "ok" : "loading";   // 503 = 模型还在加载
    } catch (_) {
      status = "down";                       // 连接失败 = 后端进程未就绪
    }

    if (status === "ok") {
      modelReady = true;
      modelStatus.textContent = "✅ 模型已就绪";
      modelStatus.className = "model-status ready";
      setLoading(false);                     // 恢复发送按钮
      setTimeout(() => { modelStatus.style.opacity = "0"; }, 2500);  // 淡出
      return;                                // 就绪后停止轮询
    }

    if (status === "loading") {
      modelStatus.textContent = "⚙️ 模型加载中，请稍候...";
    } else {
      modelStatus.textContent = "⏳ 正在连接后端...";
    }
    modelStatus.className = "model-status loading";
    setTimeout(tick, 2000);                  // 未就绪，2 秒后再查
  };
  tick();
}

// 统一处理接口报错：优先取后端 detail 字段，拿不到就拼 HTTP 状态码
async function showError(err, res) {
  let detail = err.message;
  if (res) {
    try {
      const data = await res.json();
      if (data.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch (_) { /* 响应体不是 JSON，忽略 */ }
    detail = `请求失败（HTTP ${res.status}）：${detail}`;
  }
  appendMessage("error", detail);
}

// ---------- 核心功能 ----------

// 1. 问答（流式）：POST /agent/stream（智能体版：自动决策要不要检索），SSE 格式逐段返回
async function sendMessage(queryText) {
  // queryText 仅供 404 自动重发时传入原问题；正常触发时从输入框取
  const query = (queryText || queryInput.value).trim();
  if (!query) return;

  appendMessage("user", query);
  queryInput.value = "";
  setLoading(true);

  // 阶段一：智能体在决策+生成（打招呼直答秒回；产品问题会先检索，约 2~4 秒），先显示"正在思考"
  const statusMsg = appendMessage("assistant loading", "🤔 正在思考");
  const dots = document.createElement("span");
  dots.className = "dots";
  statusMsg.appendChild(dots);

  let answerMsg = null;   // 第一个正文块到达时才创建真正的回答气泡
  let gotError = false;   // 流里收到过 error 事件（用于跳过"没有返回内容"的兜底提示）

  try {
    const res = await authFetch(`${API_BASE}/agent/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // session_id 为 null 时后端会新建会话，并通过 SSE 首条消息把新 id 发回来
      body: JSON.stringify({ query: query, session_id: getSessionId() }),
    });

    if (!res.ok) {
      // 404 = 本地存的 session_id 在后端已不存在（清过库/换了账号/别人的会话）：
      // 清掉失效 id，带着原问题自动用新会话重发一次
      if (res.status === 404 && getSessionId()) {
        clearSessionId();
        statusMsg.remove();
        await sendMessage(query);
        return;
      }
      statusMsg.remove();
      await showError(new Error(), res);
      return;
    }

    // 流式读取：SSE 消息以空行（\n\n）分隔，每条形如  data: {"content":"..."}
    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";       // 一段网络数据可能只含半条消息，攒够再解析

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop();   // 最后一段可能不完整，留到下一轮继续攒

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();

        if (payload === "[DONE]") continue;   // 结束标记，循环会因流关闭自然退出

        let data;
        try { data = JSON.parse(payload); } catch (_) { continue; }  // 半条消息防御

        if (data.session_id) {
          saveSessionId(data.session_id);   // 后端发来会话 ID（新会话/确认已有会话），存住
          loadSessions();                   // 新会话要及时出现在左侧列表里
          continue;
        }

        if (data.error) {                   // 后端在流里报错（检索/生成异常）：撤掉状态条，原样显示
          statusMsg.remove();
          appendMessage("error", `后端错误：${data.error}`);
          gotError = true;
          continue;
        }

        if (data.content) {
          if (!answerMsg) {
            // 第一个字到了：撤掉"正在检索"，换成正式回答气泡
            statusMsg.remove();
            answerMsg = appendMessage("assistant", "");
          }
          answerMsg.textContent += data.content;   // 逐段追加，打字机效果
          scrollToBottom();
        }
      }
    }

    // 流结束但一个字都没收到 → 模型没返回内容（已显示过错误事件的不重复提示）
    if (!answerMsg && !gotError) {
      statusMsg.remove();
      appendMessage("assistant", "（模型没有返回内容）");
    }
  } catch (err) {
    // authFetch 的 401 已经跳转登录页了；走到这里一般是后端没启动 / 网络不通
    statusMsg.remove();
    if (answerMsg) answerMsg.remove();
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") {
      await showError(err);
    }
  } finally {
    setLoading(false);
  }
}

// 2. 上传文件：POST /document/upload（multipart，字段名 file）
async function uploadFile() {
  const file = fileInput.files[0];
  if (!file) return;

  appendMessage("system", `正在上传：${file.name}（${(file.size / 1024).toFixed(1)} KB）...`);
  uploadBtn.disabled = true;

  try {
    // FormData 会自动带上 multipart/form-data 的 Content-Type 和文件名
    const formData = new FormData();
    formData.append("file", file);

    // 注意：multipart 不要手动设 Content-Type，浏览器会自动加 boundary；
    // authFetch 会补上 Authorization 头，两者不冲突
    const res = await authFetch(`${API_BASE}/document/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }

    const data = await res.json();
    appendMessage("system", `✅ ${data.message}：${data.filename}，已入库，可以直接提问了`);
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  } finally {
    uploadBtn.disabled = false;
    fileInput.value = "";   // 允许连续上传同一个文件
  }
}

// 3. 扫描知识库：POST /document/ingest（把 data 目录下没入库的文件批量入库）
async function ingest() {
  ingestBtn.disabled = true;
  appendMessage("system", "正在扫描 data 目录并入库...");

  try {
    const res = await authFetch(`${API_BASE}/document/ingest`, { method: "POST" });
    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }
    const data = await res.json();
    appendMessage("system", `✅ ${data.message}`);
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  } finally {
    ingestBtn.disabled = false;
  }
}

// ---------- 拉取历史会话 ----------
// retry：自动重试计数（后端启动时正在加载模型权重，请求可能失败）
// 返回值约定：true = 历史已渲染或正在等待重试（流程已接管 UI，调用方无需补提示）；
//             false = 确实没有可显示的会话内容
async function loadHistory(retry = 0) {
  const sessionId = getSessionId();
  if (!sessionId) return false;
  try {
    // 消息接口已挪到 message.py：GET /message/{session_id}
    const res = await authFetch(`${API_BASE}/message/${sessionId}`);
    if (!res.ok) {
      // 只有 404（会话不存在/不属于当前用户）才重置指向；
      // 500 等其他错误不清，防止误伤（重试/刷新还能恢复）
      if (res.status === 404) { clearSessionId(); return false; }
      return false;
    }
    const messages = await res.json();
    if (!Array.isArray(messages) || messages.length === 0) return false;
    for (const m of messages) {
      if (m.role === "user" || m.role === "assistant") {
        appendMessage(m.role, m.content, m.id);   // 带上消息 id，渲染删除按钮
      }
    }
    return true;
  } catch (_) {
    // 后端没启动完：提示并 1 秒后自动重试（提示只保留最新一条，重试前撤掉）
    if (retry < 20) {
      const tip = appendMessage("system", "⏳ 后端启动中（正在加载模型），历史消息稍后自动加载...");
      setTimeout(() => { tip.remove(); loadHistory(retry + 1); }, 1000);
      return true;   // 等待中：告诉调用方"流程已接管"，别再补「没有消息/欢迎语」
    }
    return false;
  }
}

// ---------- 会话列表（左侧栏） ----------
// retry：自动重试计数。后端启动时要在 lifespan 里加载模型权重（几十秒），
// 期间请求会挂起或连接失败，这里给出提示并隔几秒重试，直到后端就绪
async function loadSessions(retry = 0) {
  try {
    const res = await authFetch(`${API_BASE}/session/list`);
    if (!res.ok) return;
    const data = await res.json();
    // 后端返回 {"sessions": [...]} 包装格式
    const sessions = (data && Array.isArray(data.sessions)) ? data.sessions : [];
    renderSessionList(sessions);
  } catch (_) {
    // 网络异常（后端没启动完/连接失败）：显示提示，1 秒后自动重试（最多 20 次）
    sessionList.innerHTML = '<div class="session-empty">⏳ 后端启动中（正在加载模型）...<br>就绪后自动显示</div>';
    if (retry < 20) setTimeout(() => loadSessions(retry + 1), 1000);
  }
}

function renderSessionList(sessions) {
  const currentId = getSessionId();
  sessionList.innerHTML = "";
  if (sessions.length === 0) {
    sessionList.innerHTML = '<div class="session-empty">还没有会话<br>提问会自动创建</div>';
    return;
  }
  // 最近更新的排前面
  sessions.sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
  sessions.forEach((s, index) => {
    const item = document.createElement("div");
    item.className = "session-item" + (s.id === currentId ? " active" : "");
    // 没有自定义标题（空 / 后端默认值「默认会话」）→ 按列表位置编号，每个用户各自从 1 开始
    const isDefault = !s.title || !s.title.trim() || s.title.trim() === "默认会话";
    const displayTitle = isDefault ? `默认会话 ${index + 1}` : s.title.trim();
    const title = document.createElement("div");
    title.className = "session-title";
    title.textContent = displayTitle;
    title.title = "双击修改标题";
    // 双击改名：弹输入框 → PATCH 后端 → 刷新列表（默认会话从空白开始输入）
    title.addEventListener("dblclick", (e) => {
      e.stopPropagation();   // 拦住冒泡，别触发外层的切换会话
      renameSession(s.id, isDefault ? "" : s.title.trim());
    });
    const time = document.createElement("div");
    time.className = "session-time";
    time.textContent = (s.updated_at || s.created_at || "").slice(5, 16).replace("T", " ");
    // 删除按钮：平时隐藏，鼠标悬停会话项时出现
    const del = document.createElement("button");
    del.className = "session-del";
    del.textContent = "×";
    del.title = "删除会话";
    del.addEventListener("click", (e) => {
      e.stopPropagation();   // 关键：拦住冒泡，点了删除就不要再触发外层的「切换会话」
      deleteSession(s.id, displayTitle);
    });
    item.appendChild(title);
    item.appendChild(time);
    item.appendChild(del);
    item.addEventListener("click", () => switchSession(s.id));
    sessionList.appendChild(item);
  });
}

// 修改会话标题：双击触发 → PATCH /session/{id}，成功后刷新列表
async function renameSession(id, oldTitle) {
  const title = prompt("修改会话标题：", oldTitle);
  // 点了取消 / 清空 / 没变化，都不发请求
  if (title === null || !title.trim() || title.trim() === oldTitle.trim()) return;
  try {
    const res = await authFetch(`${API_BASE}/session/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title.trim() }),
    });
    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }
    loadSessions();   // 重新拉列表显示新标题
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  }
}

// 删除会话：调后端 DELETE；删的是当前会话时，本地指向也要清掉
async function deleteSession(id, name) {
  if (!confirm(`确定删除「${name || "该会话"}」吗？聊天记录将一并删除`)) return;
  try {
    const res = await authFetch(`${API_BASE}/session/${id}`, { method: "DELETE" });
    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }
    if (id === getSessionId()) {
      // 删的是正在用的会话 → 清本地指向和聊天区，回到起点
      clearSessionId();
      chatArea.innerHTML = "";
      appendMessage("assistant", "（会话已删除，点「新建会话」或直接提问开始新的对话）");
    }
    loadSessions();   // 刷新列表
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  }
}

// 切换会话：存下 id → 清屏 → 拉这个会话的消息
async function switchSession(id) {
  if (id === getSessionId()) return;
  saveSessionId(id);
  chatArea.innerHTML = "";
  const ok = await loadHistory();
  if (!ok) appendMessage("assistant", "（这个会话还没有消息）");
  loadSessions();   // 刷新列表高亮
}

// ---------- 事件绑定 ----------
// 注意用箭头函数包一层：直接传 sendMessage 会把事件对象当成 queryText 串进去
sendBtn.addEventListener("click", () => sendMessage());
queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
uploadBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", uploadFile);
ingestBtn.addEventListener("click", ingest);
clearBtn.addEventListener("click", async () => {
  const sessionId = getSessionId();
  chatArea.innerHTML = "";
  if (sessionId) {
    // 真清空：删后端会话记录 + 重置本地 session_id（下次提问自动建新会话）
    try {
      await authFetch(`${API_BASE}/session/${sessionId}`, { method: "DELETE" });
    } catch (_) { /* 后端没启动也照常重置本地 */ }
    clearSessionId();
  }
  appendMessage("assistant", "（已清空，可以开始新的提问）");
  loadSessions();   // 列表里移除被删的会话
});

// 新建会话：立刻在后端建一个，列表马上出现并高亮；下一问直接落进这个会话
newSessionBtn.addEventListener("click", async () => {
  newSessionBtn.disabled = true;
  try {
    const res = await authFetch(`${API_BASE}/session/create`, { method: "POST" });
    if (!res.ok) {
      await showError(new Error(), res);
      return;
    }
    const session = await res.json();
    saveSessionId(session.id);          // 新会话 id 存住，下一问走复用分支
    chatArea.innerHTML = "";
    appendMessage("assistant", "（新会话已创建，直接提问即可）");
    loadSessions();                     // 列表立刻多一项并高亮
  } catch (err) {
    if (err.message !== "未登录" && err.message !== "登录已过期，请重新登录") await showError(err);
  } finally {
    newSessionBtn.disabled = false;
  }
});

// 登出：清登录态 + 本地会话，回登录页
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("rag_token");
  localStorage.removeItem("rag_username");
  clearSessionId();
  location.replace("login.html");
});

// ---------- 启动：登录检查 → 有历史渲染历史，没有显示欢迎语 ----------
(async function init() {
  if (!getToken()) {
    location.replace("login.html");
    return;
  }
  const username = localStorage.getItem("rag_username") || "已登录";
  currentUser.textContent = `👤 ${username}`;

  loadSessions();              // 左侧会话列表
  pollModelStatus();           // 模型就绪状态条（轮询 /health，就绪前禁用发送）
  // 刷新 = 空壳 HTML + JS 二次拉数据：先显示加载提示，数据回来再渲染
  const loadingMsg = appendMessage("assistant loading", "⏳ 正在加载历史消息");
  const hasHistory = await loadHistory();
  loadingMsg.remove();
  if (!hasHistory) {
    appendMessage("assistant", `你好，${username}！我是扫地机器人智能助手：产品问题会自动检索知识库回答，日常闲聊也可以直接聊。\n可以先点右上角「上传文件」把 .txt / .md / .pdf 加进知识库，然后直接向我提问。`);
  }
})();
