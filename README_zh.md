# Mail MCP Bridge

> 通过模型上下文协议(MCP)连接 macOS Mail 和 AI

**Mail MCP Bridge** 让 AI 助手（如 Claude、ChatGPT）能够直接访问和分析你的 macOS Mail 邮件。只需在 Mail 中复制 Message-ID 并粘贴给 AI——无需手动导出邮件。


**演示: 实际使用效果** (点击观看)

![演示视频](https://github.com/user-attachments/assets/b9229493-8bdf-4995-9ca8-d5de55ec7144)

*内容: 从 Mail 复制 Message-ID → AI 分析邮件内容*

[English](README.md)

## 🎯 项目简介

**问题**: 现实中的大量沟通通过邮件进行——项目协作、客户沟通、商务谈判、技术支持。手动导出邮件让 AI 分析非常繁琐低效。

**解决方案**: Mail MCP Bridge 通过简单的工作流让 AI 直接读取邮件:

- 在 Mail 中复制 Message-ID (一个键盘快捷键)
- 粘贴给 AI
- AI 瞬间分析邮件内容

**使用场景**:

- 📋 通过邮件线程跟踪项目进展
- 💼 从商务沟通中提取关键信息
- 🔍 总结长邮件对话
- 📊 提取结构化数据（需求、反馈、承诺）
- 🤝 回顾对话历史
- 📎 **分析邮件附件**（PDF、Word、Excel 等文档）

**专注**: 提取纯文本内容和附件元数据——完美适配 AI 分析。

## ✨ 特性

- 📧 **直接访问** - AI 通过 MCP 协议读取邮件
- 🧵 **线索支持** - 一个 Message-ID 获取完整对话
- 📎 **附件提取** - 提取邮件中的 PDF、文档等附件供 AI 分析
- 🎨 **Claude Code 插件** - 预置的命令和技能，实现智能邮件分析
- ⚡ **极速** - 毫秒级查询响应
- 🎯 **纯文本** - 干净的文本提取，为 AI 优化
- 🔒 **隐私优先** - 本地运行，邮件永不离开你的 Mac

## 🚀 快速开始

### 前置要求

- macOS 12.0+ (带 Mail 应用)
- Python 3.9+
- MCP 兼容的 AI 助手 (如 Claude Desktop)

### 安装

```bash
# 克隆仓库
git clone https://github.com/fatbobman/mail-mcp-bridge.git
cd mail-mcp-bridge

# 安装 MCP 依赖
pip3 install mcp
```

### 配置 Claude Desktop

1. **找到配置文件位置**:

   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **编辑配置** (如果不存在则创建):

   **基础配置**:

   ```json
   {
     "mcpServers": {
       "mail": {
         "command": "python3",
         "args": [
           "/path/to/mail-mcp-bridge/src/mail_mcp_server.py"
         ]
       }
     }
   }
   ```

   **高级配置（含环境变量）**:

   ```json
   {
     "mcpServers": {
       "mail": {
         "command": "python3",
         "args": [
           "/path/to/mail-mcp-bridge/src/mail_mcp_server.py"
         ],
         "env": {
           "MAIL_SINGLE_MAX_BODY_LENGTH": "10000",
           "MAIL_THREAD_MAX_BODY_LENGTH": "1200",
           "MAIL_KEEP_QUOTE_LINES": "10",
           "MAIL_ATTACHMENT_PATH": "/tmp"
         }
       }
     }
   }
   ```

   **环境变量说明**:
   - `MAIL_SINGLE_MAX_BODY_LENGTH`: 单封邮件最大正文长度（字符数），默认 10000，0 表示不限制
   - `MAIL_THREAD_MAX_BODY_LENGTH`: 线索邮件最大正文长度（字符数），默认 1200，0 表示不限制
   - `MAIL_KEEP_QUOTE_LINES`: 每个引用块保留的行数（保留上下文），默认 10
   - `MAIL_ATTACHMENT_PATH`: 附件提取目录，默认 `/tmp`

   **智能去引用**: `read_thread` 自动启用智能引用检测，保留新内容和引用头部，删除冗余的大段引用，可节省 80% 的 token

   **重要**: 将 `/path/to/mail-mcp-bridge` 替换为实际的项目路径。

3. **重启 Claude Desktop** (完全退出后重新打开)

### 安装 Claude Code 插件（可选但推荐）

Mail MCP 包含开箱即用的 **Claude Code 插件**，提供智能邮件分析能力：

**你将获得**：

- 🎯 **智能附件分析** - 自动识别重要附件（发票、合同、税务文件）
- 🧵 **线索追踪** - 跨邮件对话追踪文档演进
- 🚀 **三种分析模式** - 快速/交互/自动模式，优化 Token 使用
- 📋 **行动项提取** - 自动发现邮件中的截止日期和任务

**安装方法**：

```bash
# 1. 添加 Mail MCP 插件市场
/plugin marketplace add /path/to/mail-mcp-bridge/plugins

# 2. 安装附件分析插件
/plugin install mail-attachment-analyzer@mail-mcp

# 3. 重启 Claude Code
```

将 `/path/to/mail-mcp-bridge` 替换为你的实际安装路径。

**使用方式**：

安装后，插件会自动工作。有三种使用方式：

#### 方式 1：自然语言调用（推荐）

```bash
你: 分析这封邮件 <message-id@example.com>
AI: [自动检测并智能分析]
```

#### 方式 2：使用 Slash Commands

在 CLI 中使用 `/` 命令快速调用：

```bash
# 分析单封邮件（快速查看）
你: /analyze-email
AI: Please provide the email Message-ID
💡 Quick method (recommended):
In Mail.app: Select email → Press shortcut (⌘⇧C) → Message-ID copied
你: <message-id@example.com>
AI: [快速显示邮件内容摘要和附件列表]
```

**特点**：

- ✅ 每次都是全新开始，不会使用之前的 message-id
- ✅ 适合分析不同的邮件
- ⚠️ 需要每次提供 message-id

#### 方式 3：在 VSCode Extension 中点击 Skill

在 Claude Code Extension 中直接点击 Skills：

- `analyze-email`
- `analyze-thread`
- `analyze-attachments`

**特点**：

- ✅ AI 会记住对话历史中的 message-id
- ✅ 如果之前分析过，可能直接使用之前的 ID
- ✅ 适合对同一邮件进行深入分析
- ⚠️ 如果想分析新邮件，明确说明："分析新的邮件"

**使用建议**：

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 首次分析邮件 | Slash Commands | 确保提供正确的 message-id |
| 深入分析同一邮件 | Extension Skills | 利用对话上下文，减少重复输入 |
| 分析多个不同邮件 | Slash Commands | 每次都会询问，避免混淆 |
| 快速查看邮件内容 | 自然语言 | 最直接，无需切换模式 |

**命令对比**：

| 命令 | 用途 | MCP 调用 | 适用场景 |
|------|------|----------|----------|
| `/analyze-email` | 快速查看单封邮件 | read_email | 了解邮件内容 |
| `/analyze-thread` | 分析完整对话线索 | read_thread | 梳理多方沟通 |
| `/analyze-attachments` | 深度分析附件 | read_email + extract | 处理文档合同 |

> 💡 **提示**：
>
> - 自然语言方式更直接（推荐日常使用）
> - Slash Commands 更快速（适合频繁使用）
> - 选择命令 = 明确表达意图，减少交互步骤

📖 **[→ 插件文档](plugins/README.md)**

### 设置 Mail Quick Action

在 Mail 应用中添加"复制 Message-ID"按钮:

**详细步骤**:

1. 打开 **Automator** (`⌘ + 空格`，输入 "Automator")

2. 创建新的 **Quick Action**:
   - File → New (`⌘ + N`)
   - 选择 "Quick Action"
   - Workflow receives current: **no input**
   - in: **Mail.app**

3. 添加 **Run Shell Script** 动作:
   - 在左侧面板搜索 "Run Shell Script"
   - 拖拽到工作流区域
   - Shell: `/bin/bash**

4. 复制脚本内容:

   ```bash
   cat automator_script.sh
   ```

   将完整输出粘贴到 Automator 脚本区域

5. 保存为 **"Copy Message-ID"**

6. (可选) 分配键盘快捷键:
   - 系统设置 → 键盘 → 键盘快捷键
   - 服务 → Mail → "Copy Message-ID"
   - 添加快捷键 (如 `⌘ + ⇧ + C`)

**Automator 设置示例**:

![Automator 设置示例](images/automatic-setup.webp)

**测试**:

1. 打开 Mail 应用
2. 选择任意邮件
3. 按下快捷键 (如果已配置)
4. 应该听到提示音，确认 Message-ID 已复制

## 📖 使用方法

### 基本工作流

```bash
1. 在 Mail 中选择邮件
2. 按下快捷键 (如 ⌘⇧C)
3. 粘贴 Message-ID 给 AI
```

### 💡 选择线索中的特定邮件

当需要分析邮件线索中的某封特定邮件时：

**方法 1：展开对话视图**
1. 在 Mail 应用中选择邮件
2. 菜单栏：**显示** → **展开所有对话** (Show → Expand All Conversations)
3. 左侧会显示完整的对话树形结构
4. 点击选择你想要分析的那封邮件
5. 按下快捷键复制其 Message-ID
6. 使用 `/analyze-email` 分析这特定邮件

**方法 2：使用线索命令**
如果不确定要分析哪一封邮件，可以先：
1. 使用 `/analyze-thread` 分析整个线索
2. 查看对话时间线和摘要
3. 根据摘要，选择需要深入分析的特定邮件
4. 在 VSCode Extension 中点击 Skill（会使用之前的 message-id）

**使用场景示例**：

```bash
# 场景：只想看线索中某封重要邮件的详细内容
你: /analyze-thread
AI: [显示线索概览，发现第 5 封邮件有重要决策]

你: 我想深入看一下第 5 封邮件
AI: [从线索摘要中获取第 5 封的 message-id]
AI: [使用 /analyze-email 分析该邮件]
```

**小贴士**：
- `/analyze-thread` 给全局视图，了解整体脉络
- `/analyze-email` 深入分析单封邮件的详细内容
- 结合使用可以获得最佳效果

### 对话示例

#### 读取单封邮件

```bash
你: 请分析这封邮件: <message-id@example.com>

AI: 我来读取这封邮件...
[AI 读取并分析邮件内容]
```

#### 读取邮件线索

```bash
你: <message-id@example.com> 的完整对话是什么?

AI: 我来检索整个线索...
[AI 显示对话中的所有邮件]
```

#### 分析邮件线索（自动触发 Skill）

```bash
你: 帮我看看这个邮件线索: <example-thread@example.com>

AI: 我来分析这个邮件线索...

📧 邮件线索分析
- 邮件数量: 15封
- 时间跨度: 2025-01-10 至 2025-01-15
- 参与者: 项目组成员 (3人)

💬 主要议题
- 讨论项目需求和技术方案
- 确定开发时间表
- 分配任务责任

📋 附件清单
- requirements.pdf (需求文档)
- design_mockup.fig (设计稿)
- 多张技术方案截图

✅ 达成共识
- 采用 SwiftUI 重构 UI
- 使用 SwiftData 进行数据管理
- 预计 2 月中旬完成 MVP

⚠️ 待处理问题
- 性能优化方案需要进一步讨论
- 需要安排下周技术评审会议
```

#### 实际使用场景

```bash
你: 请总结我们与商业伙伴的所有沟通，
包括他们的需求、承诺的时间表和行动项。

AI: 我来阅读相关的邮件线索并提取关键信息...
[AI 分析邮件内容，整理项目进展、承诺和行动项]
```

#### 分析邮件附件

```bash
你: 这封邮件有附件吗？

AI: 这封邮件有 2 个附件：
1. contract_draft.pdf (2.3 MB)
2. appendix.xlsx (156 KB)

你: 帮我提取合同 PDF 并分析内容

AI: [提取附件到临时目录]
[AI 读取并分析 PDF 内容]
```

#### 使用 Attachment Analyzer Skill

```bash
你: /analyze-attachments

AI: Please provide the email Message-ID

你: <example-email@company.com>

AI: 正在分析邮件及附件...

📧 基本信息
- 发件人: 产品团队 <product@company.com>
- 主题: Q1 产品需求文档评审
- 日期: 2025年1月15日
- 线索: 是 (8封邮件)

📎 附件清单 (共5个文件)

🚨 高重要性:
- PRD_Q1_2025.pdf
  产品需求文档，需要评审确认

⚠️ 中重要性:
- roadmap.xlsx
  产品路线图规划
- design_system.fig
  设计规范文件

💡 低重要性:
- screenshot_01.png 等2张截图
  参考效果图

💡 关键发现
- Q1 重点功能: 用户系统重构 + 性能优化
- 预计 3 月底完成全部功能开发
- 需要在本周五前完成需求评审

⚠️ 需要行动
- [ ] 周五前完成 PRD 评审
- [ ] 确认技术可行性
- [ ] 安排开发排期会议

✅ 分析完成，临时文件已删除
```

#### 自然语言触发 Skill

以下表述都会自动触发邮件分析：

```bash
# 中文示例
"分析这封邮件 <message-id>"
"看看这个邮件有什么附件"
"帮我整理一下这个线索的内容"
"这封邮件重要吗"
"提取邮件中的附件"

# 英文示例
"Analyze this email <message-id>"
"What attachments are in this email"
"Help me understand this thread"
"Is this email important"
"Extract email attachments"
```

#### 批量处理多个邮件

```bash
你: 我有几封邮件需要分析：

1. <msg1@example.com> - 税务通知
2. <msg2@example.com> - 合同草案
3. <msg3@example.com> - 项目讨论

AI: 我来依次分析这些邮件...

[处理邮件 1/3]
📧 税务通知 - HMRC
🚨 高重要性: tax_notice_2025.pdf
⚠️ 行动: 1月31日前提交申报

[处理邮件 2/3]
📧 合同草案
⚠️ 中重要性: service_agreement.docx
💡 待审核条款和付款条件

[处理邮件 3/3]
📧 项目讨论线索
🧵 15封邮件，2个附件
💡 主要讨论: Q1 发布计划
```

## 🛠️ MCP 工具

| 工具 | 描述 |
|------|------|
| `get_email_path` | 获取单封邮件的文件路径 |
| `get_thread_paths` | 获取邮件线索中的所有路径 |
| `read_email` | 读取单封邮件内容（含附件列表） |
| `read_thread` | 读取整个邮件线索 |
| `extract_attachments` | 提取邮件附件到临时目录 |
| `cleanup_attachments` | 清理临时附件目录 |

📖 **[→ 详细 API 文档](TOOLS.md)**

## 🏗️ 工作原理

```
┌─────────────┐
│  Mail App   │ 选择邮件 → 复制 Message-ID (⌘⇧C)
└──────┬──────┘
       │
       ↓ Message-ID
┌─────────────┐
│MCP Server   │ 1. 查询 Mail SQLite 数据库
│             │ 2. 通过 ROWID 定位 .emlx 文件
│             │ 3. 解析邮件内容
│             │ 4. 提取纯文本
└──────┬──────┘
       │
       ↓ 结构化数据
┌─────────────┐
│ AI Assistant│ 分析邮件内容
└─────────────┘
```

🔧 **[→ 技术架构](ARCHITECTURE.md)**

## 🐛 故障排除

### MCP 服务器未找到

**解决方案**:

```bash
# 验证 claude_desktop_config.json 中的路径
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 重启 Claude Desktop (完全退出后重新打开)
```

### 找不到邮件

**可能原因**:

1. Message-ID 格式不正确 (必须包含 `< >`)
2. 邮件已从 Mail 中删除
3. 邮件在不同账户的数据库中

### 权限被拒绝

**解决方案**:

```bash
# 使脚本可执行
chmod +x *.py *.sh
```

## 🔒 隐私与安全

- ✅ **本地处理**: 所有操作在你的 Mac 上本地运行
- ✅ **无外部服务器**: 不向外部服务器发送数据
- ✅ **无遥测**: 无分析或跟踪
- ✅ **只读**: 只读取邮件数据，从不修改

## 📚 文档

- **[TOOLS.md](TOOLS.md)** - 完整的 MCP 工具 API 参考
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 技术架构和数据库结构
- **[README.md](README.md)** - English Documentation

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 🌟 致谢

- 为 MCP (模型上下文协议) 生态系统构建
- 灵感来源于连接邮件和 AI 的需求
- 在 macOS 26 (Tahoe) 的 Claude Desktop 上测试

## 📮 联系方式

- **问题反馈**: <https://github.com/fatbobman/mail-mcp-bridge/issues>
- **作者**: Fatbobman

## ☕ 请我喝杯咖啡

如果你觉得这个项目有帮助,欢迎请我喝杯咖啡!

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/fatbobman)

---

**用 ❤️ 为 AI 社区打造**
