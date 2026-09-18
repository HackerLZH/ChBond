#!/bin/bash
exec 2>/tmp/chbond.log

bond=$(cat /var/apps/ChBond/BOND_NAME)
BASE=/var/apps/ChBond/target/www

# 输出JSON响应头
function json_header() {
    echo "Content-Type: application/json; charset=utf-8"
    echo ""
}

# 输出HTML响应头
function html_header() {
    echo "Content-Type: text/html; charset=utf-8"
    echo ""
}

# 根据扩展名返回Content-Type
function get_content_type() {
    local file="$1"
    case "${file##*.}" in
        js)   echo "application/javascript" ;;
        css)  echo "text/css" ;;
        html) echo "text/html" ;;
        png)  echo "image/png" ;;
        jpg|jpeg) echo "image/jpeg" ;;
        gif)  echo "image/gif" ;;
        svg)  echo "image/svg+xml" ;;
        *)    echo "text/plain" ;;
    esac
}

# 返回静态文件
function serve_static() {
    local path="$1"
    local fullpath="$BASE/$path"

    if [ -f "$fullpath" ]; then
        echo "Content-Type: $(get_content_type "$path")"
        echo ""
        cat "$fullpath"
    else
        echo "Content-Type: text/plain"
        echo ""
        echo "Not found: $path"
    fi
}

# 获取网卡信息（返回JSON格式）
function get_master_slaves() {
    json_header

    mapfile -t slaves < <(grep Interface /proc/net/bonding/"$bond" | awk '{print $3}')
    active_slave=$(cat /sys/class/net/"$bond"/bonding/active_slave)

    # 构建JSON数组
    echo -n '{"success": true, "slaves": ['
    local first=true
    for slave in "${slaves[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo -n ","
        fi
        speed=$(cat /sys/class/net/"$slave"/speed)
        echo -n "{\"name\": \"${slave}\", \"speed\": ${speed}}"
    done
    echo -n "], \"active_slave\": \"${active_slave}\", \"master\": \"${bond}\"}"
    echo ""
}

# 切换网卡
function toggle_slave() {
    json_header

    local slave="$1"

    if [ -z "$slave" ]; then
        echo '{"success": false, "msg": "缺少slave参数"}'
        exit 0
    fi

    # 执行切换命令
    if echo "failure" > /sys/class/net/"$bond"/bonding/primary_reselect && \
       echo "$slave" > /sys/class/net/"$bond"/bonding/active_slave; then
        echo "{\"success\": true, \"msg\": \"${slave}切换成功\"}"
    else
        echo '{"success": false, "msg": "没有root权限或命令执行失败"}'
    fi
}

# 检查聚合网卡是否存在
if [ ! -f /proc/net/bonding/"$bond" ]; then
    html_header
    echo "聚合网卡 $bond 不存在，请在应用设置中设置有效网卡名！"
    exit 0
fi

# 根据请求类型分发处理
if [ -n "$QUERY_STRING" ]; then
    action=$(echo "$QUERY_STRING" | tr '&' '\n' | grep '^action' | cut -d= -f2)
    slave=$(echo "$QUERY_STRING" | tr '&' '\n' | grep '^slave' | cut -d= -f2)
    file=$(echo "$QUERY_STRING" | tr '&' '\n' | grep '^file' | cut -d= -f2)
fi

case "$action" in
    getBond)
        get_master_slaves
        ;;
    toggle)
        toggle_slave "$slave"
        ;;
    js|css)
        serve_static "$file"
        ;;
    *)
        # 默认返回页面
        html_header
        cat "$BASE"/html/index.html
        ;;
esac