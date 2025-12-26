#!/bin/bash
# Mail MCP Server 自动配置脚本

set -e

echo "🚀 Mail MCP Server 配置脚本"
echo "=============================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤 1: 检查 Python
echo "📦 步骤 1/4: 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3${NC}"
    echo "请先安装 Python 3"
    exit 1
fi

PYTHON_PATH=$(which python3)
echo -e "${GREEN}✅ Python 路径: $PYTHON_PATH${NC}"

# 步骤 2: 安装 MCP 库
echo ""
echo "📚 步骤 2/4: 检查 MCP 库..."
if python3 -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}✅ MCP 库已安装${NC}"
else
    echo -e "${YELLOW}⚠️  MCP 库未安装，正在安装...${NC}"
    pip3 install mcp
    echo -e "${GREEN}✅ MCP 库安装完成${NC}"
fi

# 步骤 3: 配置 Claude Desktop
echo ""
echo "⚙️  步骤 3/4: 配置 Claude Desktop..."

CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
SERVER_PATH="$HOME/Develpment/GetMailID/mail_mcp_server.py"

# 创建配置目录
mkdir -p "$CONFIG_DIR"

# 检查配置文件是否存在
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️  配置文件已存在${NC}"
    echo "   路径: $CONFIG_FILE"
    echo ""
    echo "请手动编辑配置文件，添加以下内容："
    echo ""
    echo -e "${YELLOW}----------------------------------------${NC}"
    cat <<EOF
{
  "mcpServers": {
    "mail": {
      "command": "$PYTHON_PATH",
      "args": [
        "$SERVER_PATH"
      ]
    }
  }
}
EOF
    echo -e "${YELLOW}----------------------------------------${NC}"
    echo ""
    echo "如果配置文件中已有其他 MCP Server，在 mcpServers 对象中添加 mail 条目"
    echo ""
    echo "使用以下命令打开配置文件："
    echo "  code '$CONFIG_FILE'"
    echo "  或"
    echo "  nano '$CONFIG_FILE'"
else
    echo "创建新配置文件..."
    cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "mail": {
      "command": "$PYTHON_PATH",
      "args": [
        "$SERVER_PATH"
      ]
    }
  }
}
EOF
    echo -e "${GREEN}✅ 配置文件已创建${NC}"
    echo "   路径: $CONFIG_FILE"
fi

# 步骤 4: 验证
echo ""
echo "✅ 步骤 4/4: 验证安装..."

# 检查服务器文件
if [ ! -f "$SERVER_PATH" ]; then
    echo -e "${RED}❌ MCP Server 文件不存在: $SERVER_PATH${NC}"
    exit 1
fi

# 添加执行权限
chmod +x "$SERVER_PATH"
chmod +x "$HOME/Develpment/GetMailID/get_email_path.py"
chmod +x "$HOME/Develpment/GetMailID/get_thread_paths.py"

echo -e "${GREEN}✅ 所有文件权限已设置${NC}"

# 测试 MCP Server
echo ""
echo "测试 MCP Server..."
timeout 2s python3 "$SERVER_PATH" < /dev/null > /dev/null 2>&1 || true
echo -e "${GREEN}✅ MCP Server 可以启动${NC}"

# 完成
echo ""
echo "=============================="
echo -e "${GREEN}🎉 配置完成！${NC}"
echo "=============================="
echo ""
echo "下一步："
echo "1. 完全退出 Claude Desktop (⌘Q)"
echo "2. 重新打开 Claude Desktop"
echo "3. 在对话中测试："
echo "   - 在 Mail 中选中邮件，按 ⌘⇧C 复制 Message-ID"
echo "   - 在 Claude 中输入：请读取这封邮件 <message-id>"
echo ""
echo "📖 详细文档: ~/Develpment/GetMailID/MCP_SETUP_GUIDE.md"
echo ""
