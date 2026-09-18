// JavaScript文件 - 包含所有前端逻辑
// 兼容 Android 7 (Chromium 56-58 / ES5)

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initPage();
});

function initPage() {
    // 使用相对路径，兼容不同部署方式
    var url = '?action=getBond';

    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        render(data);
                    } else {
                        showToast('网卡：获取失败');
                    }
                } catch (e) {
                    showToast('网卡：数据格式错误');
                }
            } else {
                showToast('网卡：请求失败');
            }
        }
    };
    xhr.send();
}

function render(data) {
    var slaves = data.slaves;
    var activeSlave = data.active_slave;
    document.getElementById('bond').textContent = data.master;

    var settingsList = document.getElementById('settings-list');
    settingsList.innerHTML = '';

    for (var i = 0; i < slaves.length; i++) {
        var pair = slaves[i];
        var slave = pair.name;
        var speed = pair.speed;

        var li = document.createElement('li');
        li.className = 'setting-item';

        var label = document.createElement('span');
        label.className = 'setting-label';
        label.textContent = slave;

        var speed_label = document.createElement('span');
        speed_label.className = 'setting-speed';
        speed_label.textContent = '(' + speed + 'Mbps)';

        var switchLabel = document.createElement('label');
        switchLabel.className = 'switch';

        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'slave-' + slave;

        var slider = document.createElement('span');
        slider.className = 'slider';

        switchLabel.appendChild(checkbox);
        switchLabel.appendChild(slider);

        li.appendChild(label);
        li.appendChild(speed_label);
        li.appendChild(switchLabel);

        settingsList.appendChild(li);

        if (slave === activeSlave) {
            checkbox.checked = true;
            window.activeSlave = activeSlave;
        }

        (function(slaveName, cb) {
            cb.addEventListener('change', function() {
                toggleSlave(slaveName, cb);
            });
        })(slave, checkbox);
    }
}

function toggleSlave(slaveName, checkbox) {
    if (!checkbox.checked) {
        showToast('手动开启网卡，其余网卡自动关闭！');
        checkbox.checked = true;
        return;
    }

    var url = '?action=toggle&slave=' + encodeURIComponent(slaveName);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (!data.success) {
                        checkbox.checked = false;
                        showToast(data.msg);
                    } else {
                        var activeElement = document.getElementById('slave-' + window.activeSlave);
                        if (activeElement) {
                            activeElement.checked = false;
                        }
                        window.activeSlave = slaveName;
                        showToast(data.msg);
                    }
                } catch (e) {
                    showToast('解析响应失败');
                }
            } else {
                showToast('请求失败');
                checkbox.checked = false;
            }
        }
    };
    xhr.send();
}

function showToast(msg, duration) {
    if (duration === undefined) {
        duration = 1000;
    }
    var box = document.getElementById('__toast__');
    if (!box) {
        box = document.createElement('div');
        box.id = '__toast__';
        box.style.cssText =
            'position: fixed;' +
            'left: 50%;' +
            'bottom: 40px;' +
            'transform: translateX(-50%);' +
            'background: rgba(0,0,0,0.75);' +
            'color: #fff;' +
            'padding: 8px 16px;' +
            'border-radius: 6px;' +
            'font-size: 14px;' +
            'z-index: 99999;' +
            'pointer-events: none;' +
            'opacity: 0;' +
            'transition: opacity .3s;';
        document.body.appendChild(box);
    }
    box.textContent = msg;
    box.style.opacity = '1';

    if (box._timer) {
        clearTimeout(box._timer);
    }
    box._timer = setTimeout(function() {
        box.style.opacity = '0';
    }, duration);
}

// 全局变量：存储活跃的网卡
window.activeSlave = null;
