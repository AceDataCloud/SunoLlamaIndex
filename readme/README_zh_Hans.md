# Suno by Ace Data Cloud：LlamaIndex 原生音乐工具

[English](../README.md) · [当前模型和价格](https://platform.acedata.cloud/models?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_pricing_zh)

这是 Ace Data Cloud 维护的 Suno 单服务集成，不是 Suno 或 LlamaIndex 官方产品。
安装后 `SunoToolSpec().to_tool_list()` 直接返回两个 LlamaIndex 原生工具：
`suno_generate_music`（提交一次）、`suno_get_task`（查询同一任务）。无需配置 MCP 服务地址。
同步与异步均支持；模型必须由用户明确选择，没有替代模型和自动重试。

## 1. 安装正确的包

标准发行名：`llama-index-tools-suno-acedatacloud`，Python 3.10+。
**当前为源码 PR，尚未发布 PyPI，也没有官方目录收录证明。** 审查期从分支安装：

```bash
python -m pip install "llama-index-tools-suno-acedatacloud @ git+https://github.com/AceDataCloud/SunoLlamaIndex.git@codex/native-suno-tools"
```

不是旧的检索教程；这是可导入的原生 `BaseToolSpec` 包。

## 2. 注册、登录并取得正确 API Token

1. [注册/登录 Ace Data Cloud](https://platform.acedata.cloud?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_register_zh)，打开[应用控制台](https://platform.acedata.cloud/console/applications?utm_source=llamaindex&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_llamaindex_api_key_zh)。
2. 找到 **General application**；没有时点击 **Initialize General Application**。
   通用应用 Key 受当前服务权限约束，专用应用仅限指定服务。检查 Suno 模型可用性、权限、余额和价格。
3. 复制已有 API Key，或 **Manage Keys → Create** 创建 `LlamaIndex Suno` 专用 Key。

![真实控制台截图：复制 API Key 或打开 Manage Keys，凭据已遮挡](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/get-api-key-en.png)

4. 创建时按需配置有效期、用量限制和 **Allowed APIs**；开启接口限制时，同时允许
   `/suno/audios` 和 `/suno/tasks`。创建后回 Key 列表复制。

![真实控制台截图：创建独立 Key 和权限限制](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/create-api-key-en.png)

图片复用 SunoDify 固定提交的真实控制台截图，2026-10-18 获取；展示账户设置，不是本集成跑通记录。
创建 Key 原图保留旧示例名 `Dify tutorial`，本集成请填 `LlamaIndex Suno`；不是平台配置字段。
密钥已遮挡，布局可能变化。只复制 Token 本体，不加 `Bearer `、引号或截图中的遮挡字符。
`platform-...` 管理令牌不能代替服务调用 Key，不能把密钥放进 prompt、日志或提交代码。

## 3. 在 LlamaIndex 中配置

将 Token 放入环境变量 `ACEDATACLOUD_API_TOKEN`，工具构造器自动读取；
也可从安全凭据库读取后传 `api_token=...`。不会把 Token 暴露为 Agent 工具参数。

```python
from llama_index.tools.suno_acedatacloud import SunoToolSpec

spec = SunoToolSpec()
tools = spec.to_tool_list()
print([tool.metadata.name for tool in tools])
# 接到已有 FunctionAgent(llm=llm, tools=tools)
```

构造和查看工具 schema 不发生成请求。LlamaIndex 是代码框架，未承诺新的聊天 GUI 或 Provider 下拉框。
[官方历史调试图来源与边界](../docs/visual-sources.md)。

## 4. 首次生成与同 ID 查询

英文 README 提供完整异步代码。生成调用会消耗额度：先核当日价格和权限，获得所需费用授权；
明确填 `model="YOUR_AVAILABLE_SUNO_MODEL"` 后再执行，不能照抄模型占位符当真实模型。

```python
submission = (
    await tools[0].acall(
        prompt="A gentle instrumental piano melody for a sunrise.",
        model="YOUR_AVAILABLE_SUNO_MODEL",
        instrumental=True,
    )
).raw_output
# 至少等待 15 秒；保存 task_id，以后只查询该 ID
result = (await tools[1].acall(task_id=submission["task_id"])).raw_output
```

用完执行 `await spec.aclose()`。`pending` 时只等候并查询，不能重新运行生成；
可用 `python examples/query_existing.py 原task_ID` 单独查询已有任务。
`status=succeeded`、`success=true` 且 `media_urls` 非空才是最终音频。
生成中的预览 URL 不会写入最终列表；任务失败保留为 failed。401/403/429/500 保留 SDK 的含义。
超时或丢失任务 ID 时先查账户记录，不自动补交生成。

## 5. 免费离线验证

```bash
python -m pip install -e ".[dev]"
python examples/offline.py
pytest
ruff check .
ruff format --check .
python -m build
```

离线消费示例使用模拟 HTTP、假 Token 和 `example.invalid` URL，但实际通过 SDK 和 LlamaIndex 工具调用。
CI 在新环境安装 wheel 再执行；不发真实 API，不产生真实音乐、账单或营收证据。

## 常见问题

- PyPI 找不到：当前未正式发布，使用源码 PR；源码合并、发包和官方收录分别验收。
- 401：重查完整 Token、有效期、应用与 Suno 权限。
- 403/余额不足：读 SDK 错误与当前账户限制，不能反复生成碰碰运气。
- 429/网络超时：禁重试；先查是否已提交，再决定下一步。
- 一直 pending：等 15 秒查同一 ID，预览不是终态。
- 查任务无权限：同一应用 Key 必须有 `/suno/tasks` 权限；知道别人的 task ID 不等于有权限。

发行工作流已准备 PyPI Trusted Publishing，需要真实项目/发布者配置与人工审查后才能发版。
[官方政策](https://github.com/run-llama/llama_index/blob/main/CONTRIBUTING.md)支持新集成独立维护、发布 PyPI，
主仓不接受新增 package；不能把本地安装当成官方可搜安装。
