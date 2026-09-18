// JavaScript文件 - 包含所有前端逻辑

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
});

function initPage() {
    // 获取当前Bond模式下的网卡信息
    fetch('?action=getBond')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                render(data);
            } else {
                showToast('网卡：获取失败');
            }
        })
        .catch(error => {
            showToast('网卡：请求失败');
        });
}

function render(data) {
    const slaves = data.slaves
    const activeSlave = data.active_slave
    document.getElementById('bond').textContent = data.master

    const settingsList = document.getElementById('settings-list');
    settingsList.innerHTML = '';

    slaves.forEach(slave => {
        const li = document.createElement('li');
        li.className = 'setting-item';

        const label = document.createElement('span');
        label.className = 'setting-label';
        label.textContent = slave;

        const switchLabel = document.createElement('label');
        switchLabel.className = 'switch';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'slave-' + slave;

        const slider = document.createElement('span');
        slider.className = 'slider';

        switchLabel.appendChild(checkbox);
        switchLabel.appendChild(slider);

        li.appendChild(label);
        li.appendChild(switchLabel);

        settingsList.appendChild(li);

        // 设置初始状态
        if (slave === activeSlave) {
            checkbox.checked = true;
            window.activeSlave = activeSlave
        }

        // 添加事件监听器
        checkbox.addEventListener('change', function() {
            toggleSlave(slave, this);
        });
    });
}

function toggleSlave(slaveName, checkbox) {
    if (!checkbox.checked) {
        showToast("手动开启网卡，其余网卡自动关闭！");
        checkbox.checked = true;
        return;
    }

    fetch(`?action=toggle&slave=${encodeURIComponent(slaveName)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            checkbox.checked = false;
            showToast(data.msg);
        } else {
            const activeElement = document.getElementById('slave-' + window.activeSlave);
            if (activeElement) {
                activeElement.checked = false;
            }
            window.activeSlave = slaveName;
            showToast(data.msg);
        }
    })
    .catch(error => {
        showToast('请求失败: ' + error);
        checkbox.checked = false;
    });
}

function showToast(msg, duration = 1000) {
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

// 为页面添加一个全局变量来存储活跃的网卡
window.activeSlave = null;