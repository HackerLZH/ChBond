#!/bin/bash
exec 2>/dev/null

bond=bond0

# ============== 1.解析js请求 ===========================
if [ -n "$QUERY_STRING" ]; then
    slave=$(echo "$QUERY_STRING" | awk -F'=' '{print $2}')
fi

if [ -n "$slave" ]; then
    echo "Content-Type: application/json; charset=utf-8"
    echo ""

    if echo "failure" > /sys/class/net/"$bond"/bonding/primary_reselect; then
        echo "$slave" > /sys/class/net/"$bond"/bonding/active_slave
        echo '{"success": true}'
        exit 0
    fi

    echo '{"success": false, "msg": "没有root权限"}'
    
    exit 0
fi


# ============= 2. 渲染界面   ==============================

# 设置Content-Type头部（CSS生效）
echo "Content-Type: text/html; charset=utf-8"
echo ""

# 获取Bond网卡信息
mapfile -t slaves < <(grep Interface /proc/net/bonding/"$bond" | awk '{print $3}')
active_slave=$(cat /sys/class/net/"$bond"/bonding/active_slave)

# 开始HTML输出
cat << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChBond</title>
    <style>
        .setting-list {
            list-style: none;
            padding: 0;
            margin: 0;
            max-width: 400px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }

        .setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
            background: #fff;
        }

        .setting-item:last-child {
            border-bottom: none;
        }

        .setting-item:hover {
            background: #f9fafb;
        }

        .setting-label {
            font-size: 14px;
            color: #111827;
        }

        /* 开关组件（用 checkbox 伪装） */
        .switch {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            flex-shrink: 0;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #ccc;
            transition: .3s;
            border-radius: 24px;
        }

        .slider::before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }

        .switch input:checked + .slider {
            background-color: #2563eb;
        }

        .switch input:checked + .slider::before {
            transform: translateX(20px);
        }
    </style>
</head>
<body>
    <h1>当前Bond模式下网卡使用情况</h1>
    <ul class="setting-list">
EOF

# 动态生成列表项
for slave in "${slaves[@]}"; do
    if [ "$slave" = "$active_slave" ]; then
cat << EOF
        <li class="setting-item">
            <span class="setting-label">${slave}</span>
            <label class="switch">
                <input type="checkbox" id="slave-${slave}" checked onchange="toggleSlave('${slave}', this)">
                <span class="slider"></span>
            </label>
        </li>
EOF
    else
cat << EOF
        <li class="setting-item">
            <span class="setting-label">${slave}</span>
            <label class="switch">
                <input type="checkbox" id="slave-${slave}" onchange="toggleSlave('${slave}', this)">
                <span class="slider"></span>
            </label>
        </li>
EOF
    fi
done


# 结束HTML
# 注意 <<'EOF' 的单引号，它告诉 bash：这段内容原样输出，不做变量替换、不做命令替换、不做反引号解析
cat << EOF
    </ul>
    <script>
        var active = "${active_slave}"
EOF
cat << 'EOF'
        function showToast(msg, duration = 2000) {
            let box = document.getElementById('__toast__');
            if (!box) {
                box = document.createElement('div');
                box.id = '__toast__';
                box.style.cssText = `
                    position: fixed;
                    left: 50%;
                    bottom: 40px;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.75);
                    color: #fff;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    z-index: 99999;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity .3s;
                `;
                document.body.appendChild(box);
            }
            box.textContent = msg;
            box.style.opacity = '1';

            clearTimeout(box._timer);
            box._timer = setTimeout(() => {
                box.style.opacity = '0';
            }, duration);
        }

        function toggleSlave(slaveName, e) {
            if (!e.checked) {
                showToast("手动开启网卡，其余网卡自动关闭！")
                e.checked = true
                return
            }
            const url = `?slave=${slaveName}`;
            fetch(url, { method: 'GET' })
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        showToast('操作失败: ' + (data.msg || 'unknown'));
                        e.checked = false
                    } else {
                        const last = document.getElementById('slave-' + active)
                        last.checked = false
                        active = slaveName
                        // 让浏览器先完成一次重绘，再弹窗
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => {
                                showToast('切换成功！');
                            });
                        });
                    }
                })
                .catch(err => {
                    showToast('请求失败: ' + err);
                    e.checked = false;
                });
        }
    </script>
</body>
</html>
EOF