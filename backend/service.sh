#!/bin/bash
# 智教云后端服务管理脚本
# 用法: ./service.sh {start|stop|restart|status}

# 配置
APP_NAME="zhijiaoyun-backend"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$APP_DIR/.service.pid"
LOG_FILE="$APP_DIR/.service.log"
HOST="0.0.0.0"
PORT="8000"
WORKERS="1"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查虚拟环境
check_venv() {
    if [ -d "$APP_DIR/venv" ]; then
        source "$APP_DIR/venv/bin/activate"
    elif [ -d "$APP_DIR/.venv" ]; then
        source "$APP_DIR/.venv/bin/activate"
    fi
}

# 获取 PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查服务是否运行
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 启动服务
start() {
    if is_running; then
        echo -e "${YELLOW}⚠️  服务已经在运行中 (PID: $(get_pid))${NC}"
        return 1
    fi

    echo -e "${BLUE}🚀 正在启动智教云后端服务...${NC}"
    
    check_venv
    cd "$APP_DIR"
    
    # 使用 nohup 启动 uvicorn
    nohup python3 -m uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        >> "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✅ 服务启动成功！${NC}"
        echo -e "   PID: $pid"
        echo -e "   地址: http://$HOST:$PORT"
        echo -e "   日志: $LOG_FILE"
    else
        echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 通过端口查找进程
find_pid_by_port() {
    lsof -ti:$PORT 2>/dev/null || ss -tlnp | grep ":$PORT " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2
}

# 停止服务
stop() {
    local found_pid=""
    local stopped_count=0
    
    echo -e "${BLUE}🛑 正在停止服务...${NC}"
    
    # 1. 停止 PID 文件记录的进程
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "   停止 PID 文件记录进程: $pid"
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -KILL "$pid" 2>/dev/null
            fi
            stopped_count=$((stopped_count + 1))
        fi
    fi
    
    # 2. 查找并停止占用端口的所有进程
    local port_pids=$(find_pid_by_port)
    if [ -n "$port_pids" ]; then
        for p in $port_pids; do
            if [ -n "$p" ] && ps -p "$p" > /dev/null 2>&1; then
                echo -e "   停止端口占用进程: $p"
                kill -TERM "$p" 2>/dev/null
                sleep 1
                if ps -p "$p" > /dev/null 2>&1; then
                    kill -KILL "$p" 2>/dev/null
                fi
                stopped_count=$((stopped_count + 1))
            fi
        done
    fi
    
    # 3. 查找并停止所有 uvicorn/python 相关进程（项目目录下）
    local uvicorn_pids=$(ps aux | grep -E "(uvicorn|python.*app\.main)" | grep -v grep | grep "$APP_DIR" | awk '{print $2}')
    if [ -n "$uvicorn_pids" ]; then
        for p in $uvicorn_pids; do
            if [ -n "$p" ] && ps -p "$p" > /dev/null 2>&1; then
                echo -e "   停止 uvicorn 进程: $p"
                kill -TERM "$p" 2>/dev/null
                sleep 1
                if ps -p "$p" > /dev/null 2>&1; then
                    kill -KILL "$p" 2>/dev/null
                fi
                stopped_count=$((stopped_count + 1))
            fi
        done
    fi
    
    # 4. 等待所有进程结束
    local wait_count=0
    while [ $wait_count -lt 5 ]; do
        local remaining=$(find_pid_by_port)
        if [ -z "$remaining" ]; then
            break
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    # 5. 检查端口是否仍被占用
    local remaining=$(find_pid_by_port)
    if [ -n "$remaining" ]; then
        echo -e "${YELLOW}⚠️  警告: 端口 $PORT 仍被占用，尝试强制结束...${NC}"
        for p in $remaining; do
            kill -KILL "$p" 2>/dev/null
        done
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    
    # 6. 最终检查
    local final_check=$(find_pid_by_port)
    if [ -z "$final_check" ]; then
        echo -e "${GREEN}✅ 服务已停止 (共停止 $stopped_count 个进程)${NC}"
    else
        echo -e "${RED}❌ 端口 $PORT 仍被占用，进程: $final_check${NC}"
        echo -e "   请手动执行: kill -9 $final_check"
        return 1
    fi
}

# 强制清理所有相关进程
force_cleanup() {
    echo -e "${YELLOW}⚠️  执行强制清理...${NC}"
    
    # 通过端口查找并结束
    local port_pids=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$port_pids" ]; then
        echo -e "   结束端口 $PORT 占用进程"
        kill -9 $port_pids 2>/dev/null
    fi
    
    # 结束所有 uvicorn 进程
    ps aux | grep -E "uvicorn.*:$PORT" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
    
    # 结束所有 python app.main 进程
    ps aux | grep "python.*app\.main" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
    
    sleep 1
    rm -f "$PID_FILE"
}

# 重启服务
restart() {
    echo -e "${BLUE}🔄 正在重启服务...${NC}"
    
    # 先执行正常停止
    stop
    
    # 检查端口是否仍被占用
    local port_check=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$port_check" ]; then
        echo -e "${YELLOW}⚠️  端口 $PORT 仍被占用，执行强制清理...${NC}"
        force_cleanup
    fi
    
    # 等待端口释放
    local wait_count=0
    while [ $wait_count -lt 5 ]; do
        local port_check=$(lsof -ti:$PORT 2>/dev/null)
        if [ -z "$port_check" ]; then
            break
        fi
        echo -e "   等待端口释放... ($((wait_count+1))/5)"
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    # 最终检查
    local final_check=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$final_check" ]; then
        echo -e "${RED}❌ 端口 $PORT 仍被占用，进程: $final_check${NC}"
        echo -e "   请手动执行: kill -9 $final_check"
        return 1
    fi
    
    echo -e "${GREEN}✅ 端口已释放，准备启动...${NC}"
    sleep 1
    start
}

# 查看状态
status() {
    if is_running; then
        local pid=$(get_pid)
        echo -e "${GREEN}✅ 服务运行中${NC}"
        echo -e "   PID: $pid"
        echo -e "   地址: http://$HOST:$PORT"
        
        # 检查健康状态
        local health=$(curl -s http://localhost:$PORT/health 2>/dev/null)
        if [ -n "$health" ]; then
            echo -e "   健康检查: $health"
        fi
    else
        echo -e "${RED}❌ 服务未运行${NC}"
        rm -f "$PID_FILE"
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  日志文件不存在${NC}"
    fi
}

# 强制停止（用于紧急情况）
force_stop() {
    echo -e "${YELLOW}⚠️  执行强制停止...${NC}"
    force_cleanup
    
    local port_check=$(lsof -ti:$PORT 2>/dev/null)
    if [ -z "$port_check" ]; then
        echo -e "${GREEN}✅ 服务已强制停止${NC}"
    else
        echo -e "${RED}❌ 仍有进程占用端口: $port_check${NC}"
        return 1
    fi
}

# 使用说明
usage() {
    echo "智教云后端服务管理脚本"
    echo ""
    echo "用法: $0 {start|stop|force-stop|restart|status|logs}"
    echo ""
    echo "命令:"
    echo "  start       启动服务"
    echo "  stop        停止服务（优雅关闭）"
    echo "  force-stop  强制停止（结束所有相关进程）"
    echo "  restart     重启服务（自动处理端口占用）"
    echo "  status      查看服务状态"
    echo "  logs        查看实时日志"
}

# 主逻辑
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    force-stop)
        force_stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        usage
        exit 1
        ;;
esac
