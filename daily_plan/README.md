## LLM Study Agent（基于 Azure OpenAI GPT-4）

每天自动生成学习计划并解析输出（含时间/任务）

### ✅ 安装步骤

```bash
# 克隆项目或创建文件夹
cd daily_plan

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Windows 用 venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### ✅ 配置 Azure OpenAI
编辑 `app.py`：
- 替换 `api_base` 为你在 Azure Portal 中部署的 OpenAI 资源地址
- 替换 `api_key` 为你的密钥
- 替换 `engine` 为你部署的模型名称（如 `gpt-4-1106-preview`）

### ✅ 运行

```bash
python app.py
```

运行后你会看到 GPT 返回的学习计划，并打印出每个时间段的学习任务
