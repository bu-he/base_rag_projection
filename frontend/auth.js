// ============================================================
// 登录 / 注册页逻辑
// ============================================================
// 接口约定：
//   POST /auth/register  {"username","password"(≥8位)} → {"message","user":{...}}
//   POST /auth/login     表单格式（OAuth2 标准）username/password → {"token": "eyJ..."}
// 流程：登录成功 → token 存 localStorage → 跳 index.html
//       注册成功 → 自动接着登录（不用再点一次）
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

// ---------- DOM ----------
const loginTabBtn = document.getElementById("loginTabBtn");
const registerTabBtn = document.getElementById("registerTabBtn");
const authForm = document.getElementById("authForm");
const usernameInput = document.getElementById("usernameInput");
const passwordInput = document.getElementById("passwordInput");
const authHint = document.getElementById("authHint");
const submitBtn = document.getElementById("submitBtn");

// 已经登录着的，直接进主页
if (localStorage.getItem("rag_token")) {
  location.replace("index.html");
}

// ---------- 模式切换 ----------
let mode = "login";   // login / register

function switchMode(m) {
  mode = m;
  const isLogin = (m === "login");
  loginTabBtn.classList.toggle("active", isLogin);
  registerTabBtn.classList.toggle("active", !isLogin);
  submitBtn.textContent = isLogin ? "登录" : "注册并登录";
  showHint(isLogin ? "" : "密码至少 8 位", false);
}

loginTabBtn.addEventListener("click", () => switchMode("login"));
registerTabBtn.addEventListener("click", () => switchMode("register"));

// ---------- 提交 ----------
async function submit() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (!username || !password) {
    showHint("请输入用户名和密码", true);
    return;
  }

  // 前端先拦一道，给中文提示，省得用户看后端的英文报错。
  // 密码上限 64 不是随便定的：bcrypt 算法只处理前 72 字节，
  // 中文一个字占 3 字节，超长密码后端必炸，这里直接挡在浏览器里
  if (username.length > 50) {
    showHint("用户名最多 50 个字符", true);
    return;
  }
  if (password.length > 64) {
    showHint("密码最多 64 位，想更安全请用字母+数字+符号组合", true);
    return;
  }
  if (mode === "register" && password.length < 8) {
    showHint("密码至少 8 位", true);
    return;
  }

  submitBtn.disabled = true;
  try {
    // 注册模式：先注册；失败（用户名已存在等）就停在当前页显示原因
    if (mode === "register") {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      });
      if (!res.ok) {
        showHint(await readDetail(res), true);
        return;
      }
      // 注册成功 → 不中断，直接走下面的登录
    }

    // 登录（注册模式下 = 注册完自动登录）
    // 注意：后端 login 收的是表单格式（OAuth2 标准），不是 JSON——
    // URLSearchParams 会自动带 application/x-www-form-urlencoded 的头，不要手动设
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: new URLSearchParams({ username: username, password: password }),
    });
    if (!res.ok) {
      showHint(await readDetail(res), true);
      return;
    }
    const data = await res.json();

    // 存登录态。注意：换账号登录时，本地旧 session_id 属于上一个用户，
    // 后端归属校验会拒掉它，所以这里必须清掉，让新用户从新会话开始
    // 字段是 access_token（OAuth2 标准格式，Swagger 的 Authorize 也靠它）
    localStorage.setItem("rag_token", data.access_token);
    localStorage.setItem("rag_username", username);
    localStorage.removeItem("rag_session_id");
    location.replace("index.html");
  } catch (err) {
    // 一般是后端没启动 / 跨域问题
    showHint("连不上后端：" + err.message, true);
  } finally {
    submitBtn.disabled = false;
  }
}

// 从错误响应里取后端 detail 文案，取不到就拼状态码
async function readDetail(res) {
  try {
    const data = await res.json();
    return data.detail || `请求失败（HTTP ${res.status}）`;
  } catch (_) {
    return `请求失败（HTTP ${res.status}）`;
  }
}

function showHint(text, isError) {
  authHint.textContent = text;
  authHint.classList.toggle("error", !!isError);
}

authForm.addEventListener("submit", (e) => {
  e.preventDefault();   // 阻止表单默认提交导致的整页刷新
  submit();
});
