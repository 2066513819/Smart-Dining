$(document).ready(function() {
    // 初始化侧边栏
    initSidebar();
    
    // 初始化工具提示
    $('[data-toggle="tooltip"]').tooltip();
    
    // 初始化模态框
    initModal();
    
    // 初始化导航菜单
    initNavMenu();
    
    // 初始化主题切换
    initThemeSwitch();
});

/**
 * 初始化侧边栏
 */
function initSidebar() {
    // 侧边栏折叠/展开
    $('.navbar-minimalize').click(function() {
        $(".navbar-static-side").toggleClass("navbar-static-side-open");
        $(".navbar-static-side").toggleClass("navbar-static-side-close");
        
        // 调整内容区域宽度
        if ($(".navbar-static-side").hasClass("navbar-static-side-open")) {
            $("#page-wrapper").css("margin-left", "220px");
        } else {
            $("#page-wrapper").css("margin-left", "0");
        }
    });
    
    // 移动端关闭侧边栏
    $('.nav-close').click(function() {
        $(".navbar-static-side").removeClass("navbar-static-side-open");
        $(".navbar-static-side").addClass("navbar-static-side-close");
        $("#page-wrapper").css("margin-left", "0");
    });
    
    // 响应式处理
    $(window).resize(function() {
        if ($(window).width() < 768) {
            $(".navbar-static-side").removeClass("navbar-static-side-open");
            $(".navbar-static-side").addClass("navbar-static-side-close");
            $("#page-wrapper").css("margin-left", "0");
        } else {
            $(".navbar-static-side").removeClass("navbar-static-side-close");
            $(".navbar-static-side").addClass("navbar-static-side-open");
            $("#page-wrapper").css("margin-left", "220px");
        }
    });
}

/**
 * 初始化导航菜单
 */
function initNavMenu() {
    // 二级菜单展开/折叠
    $('.nav > li > a').click(function() {
        var $this = $(this);
        var $parent = $this.parent('li');
        var $submenu = $parent.find('.nav-second-level');
        
        // 如果当前菜单项有子菜单
        if ($submenu.length > 0) {
            $submenu.slideToggle(300);
            $parent.toggleClass('active');
            
            // 切换箭头方向
            $this.find('.fa.arrow').toggleClass('fa-angle-down fa-angle-right');
        }
    });
    
    // 根据当前URL高亮菜单项
    var currentUrl = window.location.pathname;
    $('.nav a').each(function() {
        var href = $(this).attr('href');
        if (href && href !== '#' && currentUrl.indexOf(href) !== -1) {
            $(this).parent('li').addClass('active');
            $(this).parents('ul').slideDown(300);
            $(this).parents('li').addClass('active');
            $(this).parents('li').find('.fa.arrow').addClass('fa-angle-down').removeClass('fa-angle-right');
        }
    });
}

/**
 * 初始化模态框
 */
function initModal() {
    // 自定义模态框关闭事件
    $('.modal').on('hidden.bs.modal', function () {
        // 清除模态框内容
        $(this).find('.modal-body').html('');
    });
    
    // 模态框居中显示
    function centerModals() {
        $('.modal').each(function(i) {
            var $clone = $(this).clone().css('display', 'block').appendTo('body');
            var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
            top = top > 0 ? top : 0;
            $clone.remove();
            $(this).find('.modal-content').css("margin-top", top);
        });
    }
    
    $('.modal').on('show.bs.modal', centerModals);
    $(window).on('resize', centerModals);
}

/**
 * 初始化主题切换
 */
function initThemeSwitch() {
    // 切换主题
    $('#switchTheme').click(function() {
        $('body').toggleClass('dark-theme');
        
        // 保存主题设置到本地存储
        if ($('body').hasClass('dark-theme')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
    
    // 从本地存储恢复主题
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        $('body').addClass('dark-theme');
    }
}

/**
 * 显示加载提示
 * @param {string} message - 提示消息
 */
function showLoading(message) {
    message = message || '加载中，请稍候...';
    $('<div class="loading-overlay"><div class="loading-spinner"></div><div class="loading-message">' + message + '</div></div>').appendTo('body');
    
    // 添加CSS样式
    if (!$('style#loading-style').length) {
        var style = $('<style id="loading-style">' +
            '.loading-overlay {position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.5); z-index: 9999; display: flex; flex-direction: column; justify-content: center; align-items: center;}' +
            '.loading-spinner {border: 4px solid #f3f3f3; border-top: 4px solid #1890ff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite;}' +
            '.loading-message {color: #fff; margin-top: 10px; font-size: 14px;}' +
            '@keyframes spin {0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); }}' +
            '</style>');
        $('head').append(style);
    }
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
    $('.loading-overlay').remove();
}

/**
 * 显示提示消息
 * @param {string} message - 提示消息
 * @param {string} type - 消息类型：success, info, warning, danger
 * @param {number} duration - 显示时长（毫秒）
 */
function showMessage(message, type, duration) {
    type = type || 'success';
    duration = duration || 3000;
    
    // 创建提示元素
    var alertClass = 'alert-' + type;
    var messageHtml = '<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">&times;</span>' +
        '</button>' +
        '</div>';
    
    // 添加到页面
    var $message = $(messageHtml);
    $message.appendTo('body');
    
    // 定位到页面顶部
    $message.css({
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'z-index': '10000',
        'min-width': '250px'
    });
    
    // 自动关闭
    setTimeout(function() {
        $message.alert('close');
    }, duration);
}

/**
 * 表单验证
 * @param {string} formSelector - 表单选择器
 * @returns {boolean} - 是否通过验证
 */
function validateForm(formSelector) {
    var $form = $(formSelector);
    var isValid = true;
    
    // 清除之前的错误提示
    $form.find('.error-message').remove();
    
    // 验证必填字段
    $form.find('[required]').each(function() {
        var $field = $(this);
        var value = $field.val().trim();
        
        if (!value) {
            isValid = false;
            var errorMessage = $field.attr('data-error-message') || '此字段为必填项';
            $field.after('<div class="error-message text-danger">' + errorMessage + '</div>');
            $field.addClass('is-invalid');
        } else {
            $field.removeClass('is-invalid');
        }
    });
    
    // 验证邮箱格式
    $form.find('[type="email"]').each(function() {
        var $field = $(this);
        var value = $field.val().trim();
        
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            isValid = false;
            var errorMessage = $field.attr('data-error-message') || '请输入有效的邮箱地址';
            $field.after('<div class="error-message text-danger">' + errorMessage + '</div>');
            $field.addClass('is-invalid');
        }
    });
    
    // 验证密码强度
    $form.find('[data-validate="password"]').each(function() {
        var $field = $(this);
        var value = $field.val().trim();
        
        if (value && value.length < 6) {
            isValid = false;
            var errorMessage = $field.attr('data-error-message') || '密码长度不能少于6个字符';
            $field.after('<div class="error-message text-danger">' + errorMessage + '</div>');
            $field.addClass('is-invalid');
        }
    });
    
    // 验证两次密码是否一致
    var $password = $form.find('[name="password"]');
    var $confirmPassword = $form.find('[name="confirmPassword"]');
    if ($password.length && $confirmPassword.length) {
        var passwordValue = $password.val().trim();
        var confirmPasswordValue = $confirmPassword.val().trim();
        
        if (passwordValue && confirmPasswordValue && passwordValue !== confirmPasswordValue) {
            isValid = false;
            var errorMessage = $confirmPassword.attr('data-error-message') || '两次输入的密码不一致';
            $confirmPassword.after('<div class="error-message text-danger">' + errorMessage + '</div>');
            $confirmPassword.addClass('is-invalid');
        }
    }
    
    return isValid;
}

/**
 * AJAX请求封装
 * @param {string} url - 请求URL
 * @param {string} method - 请求方法
 * @param {object} data - 请求数据
 * @param {function} successCallback - 成功回调
 * @param {function} errorCallback - 错误回调
 */
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    showLoading();
    
    $.ajax({
        url: url,
        type: method,
        data: data,
        dataType: 'json',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            hideLoading();
            
            if (response.code === 200 || response.success) {
                if (successCallback) {
                    successCallback(response);
                } else {
                    showMessage(response.message || '操作成功');
                }
            } else {
                if (errorCallback) {
                    errorCallback(response);
                } else {
                    showMessage(response.message || '操作失败', 'danger');
                }
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            
            var errorMessage = '请求失败，请稍后重试';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            } else if (xhr.status === 401) {
                errorMessage = '未授权，请重新登录';
                setTimeout(function() {
                    window.location.href = '/auth/login';
                }, 1500);
            } else if (xhr.status === 403) {
                errorMessage = '没有权限执行此操作';
            } else if (xhr.status === 404) {
                errorMessage = '请求的资源不存在';
            } else if (xhr.status === 500) {
                errorMessage = '服务器内部错误';
            }
            
            if (errorCallback) {
                errorCallback({ message: errorMessage });
            } else {
                showMessage(errorMessage, 'danger');
            }
        }
    });
}

/**
 * 获取URL参数
 * @param {string} name - 参数名
 * @returns {string} - 参数值
 */
function getUrlParam(name) {
    var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)');
    var r = window.location.search.substr(1).match(reg);
    if (r != null) {
        return decodeURIComponent(r[2]);
    }
    return null;
}

/**
 * 设置URL参数
 * @param {string} url - 原始URL
 * @param {string} paramName - 参数名
 * @param {string} paramValue - 参数值
 * @returns {string} - 新URL
 */
function setUrlParam(url, paramName, paramValue) {
    var pattern = new RegExp('(\?|\&)(' + paramName + '=).*?(\&|$)');
    var newUrl = url;
    
    if (pattern.test(newUrl)) {
        newUrl = newUrl.replace(pattern, '$1$2' + paramValue + '$3');
    } else {
        newUrl = newUrl + (newUrl.indexOf('?') > 0 ? '&' : '?') + paramName + '=' + paramValue;
    }
    
    return newUrl;
}

/**
 * 格式化日期时间
 * @param {Date} date - 日期对象
 * @param {string} format - 格式化字符串
 * @returns {string} - 格式化后的日期时间
 */
function formatDate(date, format) {
    if (!date) {
        return '';
    }
    
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    var o = {
        'M+': date.getMonth() + 1, // 月份
        'd+': date.getDate(),      // 日
        'h+': date.getHours(),     // 小时
        'm+': date.getMinutes(),   // 分
        's+': date.getSeconds(),   // 秒
        'q+': Math.floor((date.getMonth() + 3) / 3), // 季度
        'S': date.getMilliseconds() // 毫秒
    };
    
    if (/(y+)/.test(format)) {
        format = format.replace(RegExp.$1, (date.getFullYear() + '').substr(4 - RegExp.$1.length));
    }
    
    for (var k in o) {
        if (new RegExp('(' + k + ')').test(format)) {
            format = format.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (('00' + o[k]).substr(('' + o[k]).length)));
        }
    }
    
    return format;
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} - 是否复制成功
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).then(function() {
            showMessage('复制成功');
            return true;
        }).catch(function(err) {
            showMessage('复制失败，请手动复制', 'danger');
            return false;
        });
    } else {
        // 兼容旧浏览器
        var textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            var successful = document.execCommand('copy');
            if (successful) {
                showMessage('复制成功');
            } else {
                showMessage('复制失败，请手动复制', 'danger');
            }
            return successful;
        } catch (err) {
            showMessage('复制失败，请手动复制', 'danger');
            return false;
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

/**
 * 数字格式化
 * @param {number} num - 要格式化的数字
 * @param {number} decimal - 小数位数
 * @returns {string} - 格式化后的数字
 */
function formatNumber(num, decimal) {
    decimal = decimal || 2;
    return num.toFixed(decimal).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * 字符串截断
 * @param {string} str - 要截断的字符串
 * @param {number} length - 截断长度
 * @param {string} suffix - 后缀
 * @returns {string} - 截断后的字符串
 */
function truncateString(str, length, suffix) {
    suffix = suffix || '...';
    if (str.length <= length) {
        return str;
    }
    return str.substring(0, length) + suffix;
}

/**
 * 防抖函数
 * @param {function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {function} - 防抖后的函数
 */
function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        var later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {function} func - 要执行的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {function} - 节流后的函数
 */
function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}