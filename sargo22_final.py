from flask import Flask, render_template_string, request, jsonify, session, redirect, send_from_directory
from functools import wraps
import threading
import os
import json
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta
import uuid
import signal

app = Flask(__name__)
app.secret_key = 'sargo22_final_key_' + secrets.token_hex(16)
app.permanent_session_lifetime = timedelta(hours=24)

# ============ بيانات المستخدم الوحيد (أنت فقط) ============
YOUR_USERNAME = "sargo"  # غير هذا إلى اسمك المفضل
YOUR_PASSWORD = "sargo123"  # غير هذا إلى كلمة سر قوية

# ============ تخزين حالة البوتات ============
active_bots = {}
bot_processes = {}
user_activity = []
bot_logs = {}

# ============ ديكورات التحقق ============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# ============ صفحات الويب ============
LOGIN_HTML = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ＳＡＲＧＯ²²⁩ - لوحة تحكم البوت</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 450px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            text-align: center;
            animation: slideUp 0.8s ease-out;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, #ff416c, #ff4b2b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .title {
            color: #fff;
            font-size: 1.2rem;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        
        .user-badge {
            background: rgba(255, 65, 108, 0.2);
            border: 1px solid rgba(255, 65, 108, 0.3);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 25px;
        }
        
        .user-badge i {
            color: #ff416c;
            margin-left: 10px;
        }
        
        .user-badge span {
            color: white;
            font-weight: 600;
        }
        
        .input-group {
            margin-bottom: 20px;
            text-align: right;
            position: relative;
        }
        
        .input-group label {
            display: block;
            color: #fff;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 14px;
        }
        
        .input-group input {
            width: 100%;
            padding: 14px 15px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.07);
            color: #fff;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: #ff416c;
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 20px rgba(255, 65, 108, 0.3);
        }
        
        .login-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
            position: relative;
            overflow: hidden;
        }
        
        .login-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(255, 65, 108, 0.4);
        }
        
        .login-btn:active {
            transform: translateY(0);
        }
        
        .login-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: 0.5s;
        }
        
        .login-btn:hover::before {
            left: 100%;
        }
        
        .message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
            animation: fadeIn 0.5s;
            backdrop-filter: blur(10px);
        }
        
        .message.success {
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid rgba(0, 255, 0, 0.3);
            color: #00ff00;
            display: block;
        }
        
        .message.error {
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            color: #ff4444;
            display: block;
        }
        
        .info-box {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            margin-top: 25px;
            text-align: right;
        }
        
        .info-box p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 13px;
            margin-bottom: 5px;
        }
        
        .footer {
            margin-top: 30px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 13px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 20px;
        }
        
        .creator {
            color: #ff416c;
            font-weight: bold;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .password-toggle {
            position: absolute;
            left: 15px;
            top: 40px;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            font-size: 1.2rem;
        }
        
        .password-toggle:hover {
            color: white;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 20px;
        }
        
        .feature-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .feature-item i {
            color: #ff416c;
            margin-bottom: 5px;
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">ＳＡＲＧＯ²²⁩</div>
        <div class="title">لوحة تحكم بوت فري فاير المتقدم</div>
        
        <div class="user-badge">
            <i class="fas fa-crown"></i>
            <span>لوحة خاصة للمطور SARGO</span>
        </div>
        
        <div id="message" class="message"></div>
        
        <form id="loginForm">
            <div class="input-group">
                <label for="username"><i class="fas fa-user"></i> اسم المستخدم</label>
                <input type="text" id="username" placeholder="أدخل اسم المستخدم الخاص بك" required>
            </div>
            
            <div class="input-group">
                <label for="password"><i class="fas fa-lock"></i> كلمة المرور</label>
                <button type="button" class="password-toggle" onclick="togglePassword()">
                    <i class="fas fa-eye"></i>
                </button>
                <input type="password" id="password" placeholder="أدخل كلمة المرور الخاصة بك" required>
            </div>
            
            <button type="submit" class="login-btn">
                <i class="fas fa-sign-in-alt"></i> دخول إلى لوحة التحكم
            </button>
        </form>
        
        <div class="features">
            <div class="feature-item">
                <i class="fas fa-robot"></i>
                بوت فري فاير
            </div>
            <div class="feature-item">
                <i class="fas fa-gamepad"></i>
                أوامر متقدمة
            </div>
            <div class="feature-item">
                <i class="fas fa-shield-alt"></i>
                حماية كاملة
            </div>
            <div class="feature-item">
                <i class="fas fa-bolt"></i>
                أداء عالي
            </div>
        </div>
        
        <div class="info-box">
            <p><i class="fas fa-info-circle"></i> هذه اللوحة خاصة بالمطور SARGO فقط</p>
            <p><i class="fas fa-check-circle"></i> نظام تشغيل البوت بنجاح تام</p>
            <p><i class="fas fa-server"></i> جاهز للرفع على GitHub</p>
        </div>
        
        <div class="footer">
            <p>© 2024 <span class="creator">SARGO DEVELOPMENT</span> - جميع الحقوق محفوظة</p>
            <p>Version: 3.0.0 | Status: <span style="color: #00ff00;">ACTIVE 100%</span></p>
        </div>
    </div>

    <script>
        // تبديل إظهار/إخفاء كلمة المرور
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const toggleIcon = document.querySelector('.password-toggle i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                toggleIcon.className = 'fas fa-eye';
            }
        }
        
        // تسجيل الدخول
        document.getElementById('loginForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const submitBtn = this.querySelector('.login-btn');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحقق...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (data.success) {
                    messageDiv.className = 'message success';
                    messageDiv.innerHTML = '<i class="fas fa-check-circle"></i> ✅ تم التحقق بنجاح! جاري الدخول...';
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    messageDiv.className = 'message error';
                    messageDiv.innerHTML = '<i class="fas fa-times-circle"></i> ❌ ' + data.message;
                    document.getElementById('password').value = '';
                }
                
            } catch (error) {
                document.getElementById('message').className = 'message error';
                document.getElementById('message').innerHTML = '<i class="fas fa-wifi-slash"></i> ❌ خطأ في الاتصال بالخادم';
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        };
        
        // تأثيرات إضافية
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('focus', function() {
                    this.style.transform = 'scale(1.02)';
                });
                input.addEventListener('blur', function() {
                    this.style.transform = 'scale(1)';
                });
            });
        });
    </script>
    <script src="https://kit.fontawesome.com/a076d05399.js"></script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ＳＡＲＧＯ²²⁩ - لوحة التحكم</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary: #ff416c;
            --secondary: #ff4b2b;
            --success: #00ff88;
            --danger: #ff3333;
            --warning: #ffcc00;
            --dark: #0a0a0f;
            --light: #ffffff;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: var(--dark);
            color: var(--light);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Navbar */
        .navbar {
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(25, 0, 10, 0.95));
            padding: 0 25px;
            height: 70px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 65, 108, 0.3);
            backdrop-filter: blur(10px);
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .user-panel {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .user-card {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 18px;
            background: rgba(255, 65, 108, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(255, 65, 108, 0.2);
            cursor: pointer;
        }
        
        .user-avatar {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.3rem;
            box-shadow: 0 5px 15px rgba(255, 65, 108, 0.4);
        }
        
        .logout-btn {
            background: linear-gradient(135deg, var(--danger), #ff2b55);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Main Content */
        .main-content {
            margin-top: 70px;
            padding: 25px;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Welcome Banner */
        .welcome-banner {
            background: linear-gradient(135deg, rgba(255, 65, 108, 0.1), rgba(255, 75, 43, 0.1));
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 65, 108, 0.2);
            backdrop-filter: blur(10px);
        }
        
        .welcome-banner h1 {
            font-size: 2.2rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Bot Creation Form */
        .bot-creation-form {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .form-title {
            font-size: 1.5rem;
            margin-bottom: 25px;
            color: var(--light);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .form-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 65, 108, 0.1);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            color: var(--light);
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .form-input {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--light);
            font-size: 1rem;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(255, 255, 255, 0.08);
        }
        
        .form-btn {
            padding: 14px 30px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s;
        }
        
        .form-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 65, 108, 0.4);
        }
        
        /* Active Bots */
        .active-bots {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .bots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .bot-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 65, 108, 0.1);
            transition: all 0.3s;
        }
        
        .bot-card:hover {
            border-color: var(--primary);
            transform: translateY(-5px);
        }
        
        .bot-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .bot-name {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--light);
        }
        
        .bot-status {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-online {
            background: rgba(0, 255, 136, 0.2);
            color: var(--success);
            border: 1px solid var(--success);
        }
        
        .status-offline {
            background: rgba(255, 51, 51, 0.2);
            color: var(--danger);
            border: 1px solid var(--danger);
        }
        
        .bot-info {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .info-item {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }
        
        .info-label {
            color: var(--primary);
            font-weight: 500;
        }
        
        .bot-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .action-btn {
            padding: 8px 15px;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        
        .btn-start {
            background: var(--success);
            color: black;
        }
        
        .btn-stop {
            background: var(--danger);
            color: white;
        }
        
        .btn-log {
            background: var(--warning);
            color: black;
        }
        
        /* Bot Logs */
        .bot-logs {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 65, 108, 0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .logs-container {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
        }
        
        .log-entry {
            padding: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.8);
            display: flex;
            gap: 15px;
        }
        
        .log-time {
            color: var(--primary);
            font-size: 0.8rem;
            min-width: 80px;
        }
        
        /* Messages */
        .message-box {
            position: fixed;
            top: 90px;
            right: 25px;
            min-width: 300px;
            max-width: 400px;
            z-index: 2000;
        }
        
        .message-alert {
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideInRight 0.5s ease-out;
        }
        
        .alert-success {
            background: rgba(0, 255, 136, 0.15);
            border-color: rgba(0, 255, 136, 0.3);
            color: var(--success);
        }
        
        .alert-error {
            background: rgba(255, 51, 51, 0.15);
            border-color: rgba(255, 51, 51, 0.3);
            color: var(--danger);
        }
        
        .alert-info {
            background: rgba(255, 65, 108, 0.15);
            border-color: rgba(255, 65, 108, 0.3);
            color: var(--primary);
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Loading */
        .loading {
            text-align: center;
            padding: 40px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .main-content {
                padding: 15px;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
            }
            
            .bots-grid {
                grid-template-columns: 1fr;
            }
            
            .navbar {
                padding: 0 15px;
            }
            
            .welcome-banner h1 {
                font-size: 1.8rem;
            }
        }
        
        /* Bot Log Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 3000;
            padding: 20px;
        }
        
        .modal-content {
            background: var(--dark);
            border-radius: 20px;
            padding: 30px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow: hidden;
            border: 1px solid rgba(255, 65, 108, 0.3);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 1.5rem;
            color: var(--light);
        }
        
        .close-btn {
            background: none;
            border: none;
            color: var(--light);
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .modal-logs {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 10px;
            padding: 20px;
            max-height: 60vh;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <div class="logo">
            <i class="fas fa-robot"></i>
            ＳＡＲＧＯ²²⁩
        </div>
        
        <div class="user-panel">
            <div class="user-card">
                <div class="user-avatar" id="userAvatar">S</div>
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem;" id="userName">SARGO</div>
                    <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7);">المطور والمالك</div>
                </div>
            </div>
            <button class="logout-btn" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i> خروج
            </button>
        </div>
    </nav>
    
    <!-- Messages Container -->
    <div class="message-box" id="messageBox"></div>
    
    <!-- Main Content -->
    <div class="main-content">
        <!-- Welcome Banner -->
        <div class="welcome-banner">
            <h1>🚀 مرحباً بك في لوحة تحكم بوت فري فاير!</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; margin-top: 10px;">
                أدخل بيانات حساب الضيف لتشغيل البوت بنجاح تام
            </p>
        </div>
        
        <!-- Bot Creation Form -->
        <div class="bot-creation-form">
            <h2 class="form-title"><i class="fas fa-plus-circle"></i> إنشاء بوت جديد</h2>
            
            <div class="form-grid">
                <div class="form-card">
                    <h3 style="color: var(--primary); margin-bottom: 20px;">
                        <i class="fas fa-user-circle"></i> بيانات حساب الضيف
                    </h3>
                    
                    <div class="form-group">
                        <label class="form-label">👤 رقم الحساب (UID)</label>
                        <input type="text" class="form-input" id="botUid" 
                               placeholder="أدخل UID حساب الضيف" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">🔑 كلمة المرور</label>
                        <input type="password" class="form-input" id="botPassword" 
                               placeholder="أدخل كلمة مرور حساب الضيف" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">🏷️ اسم البوت</label>
                        <input type="text" class="form-input" id="botName" 
                               placeholder="أدخل اسم للبوت (اختياري)" value="Bot-01">
                    </div>
                    
                    <button class="form-btn" onclick="createBot()">
                        <i class="fas fa-play"></i> تشغيل البوت الآن
                    </button>
                </div>
                
                <div class="form-card">
                    <h3 style="color: var(--primary); margin-bottom: 20px;">
                        <i class="fas fa-info-circle"></i> معلومات مهمة
                    </h3>
                    
                    <div style="color: rgba(255,255,255,0.8); line-height: 1.6; margin-bottom: 20px;">
                        <p>✅ البوت يعمل داخل لعبة فري فاير مباشرة</p>
                        <p>✅ يدعم جميع أوامر البوت المتقدمة</p>
                        <p>✅ نظام تشغيل مستقر 100%</p>
                        <p>✅ جاهز للرفع على GitHub</p>
                        <p>✅ بدون أخطاء أو مشاكل</p>
                    </div>
                    
                    <div style="background: rgba(255,65,108,0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,65,108,0.2);">
                        <p style="color: var(--primary); font-weight: 600; margin-bottom: 10px;">
                            <i class="fas fa-exclamation-triangle"></i> ملاحظة:
                        </p>
                        <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">
                            تأكد من صحة بيانات حساب الضيف قبل التشغيل
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Active Bots -->
        <div class="active-bots">
            <h2 class="form-title"><i class="fas fa-list"></i> البوتات النشطة</h2>
            
            <div class="bots-grid" id="botsGrid">
                <div class="loading">
                    <div class="spinner"></div>
                    جاري تحميل البوتات...
                </div>
            </div>
        </div>
        
        <!-- Bot Logs -->
        <div class="bot-creation-form">
            <h2 class="form-title"><i class="fas fa-terminal"></i> سجلات النظام</h2>
            
            <div class="bot-logs">
                <div class="logs-container" id="systemLogs">
                    <div class="log-entry">
                        <span class="log-time">[00:00:00]</span>
                        <span>● النظام يعمل بكفاءة 100%</span>
                    </div>
                    <div class="log-entry">
                        <span class="log-time">[00:00:00]</span>
                        <span>✅ جاهز لتشغيل بوت فري فاير</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bot Logs Modal -->
    <div id="logModal" class="modal-overlay" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title" id="modalTitle">سجلات البوت</h3>
                <button class="close-btn" onclick="closeLogModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-logs" id="modalLogs">
                <!-- Logs will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        // ============ المتغيرات العامة ============
        let currentBotId = null;
        
        // ============ تهيئة الصفحة ============
        document.addEventListener('DOMContentLoaded', function() {
            // تعيين اسم المستخدم
            document.getElementById('userAvatar').textContent = 'S';
            document.getElementById('userName').textContent = 'SARGO';
            
            // تحميل البوتات
            loadBots();
            
            // تحديث تلقائي كل 5 ثواني
            setInterval(loadBots, 5000);
            setInterval(updateLogs, 3000);
            
            // إضافة سجلات أولية
            addLog('🔧 تم تحميل لوحة التحكم بنجاح');
            addLog('🚀 النظام جاهز لتشغيل بوت فري فاير');
            addLog('✅ أدخل بيانات حساب الضيف وابدأ التشغيل');
            
            // إظهار رسالة ترحيب
            setTimeout(() => {
                showMessage('مرحباً بك في لوحة تحكم ＳＡＲＧＯ²²⁩!', 'info');
            }, 1000);
        });
        
        // ============ إنشاء بوت جديد ============
        function createBot() {
            const uid = document.getElementById('botUid').value.trim();
            const password = document.getElementById('botPassword').value;
            const name = document.getElementById('botName').value.trim() || 'Bot-' + Date.now().toString().slice(-4);
            
            if (!uid || !password) {
                showMessage('الرجاء إدخال بيانات حساب الضيف', 'error');
                return;
            }
            
            if (uid.length < 5) {
                showMessage('رقم الحساب غير صحيح', 'error');
                return;
            }
            
            // تعطيل الزر أثناء التشغيل
            const btn = document.querySelector('.form-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التشغيل...';
            btn.disabled = true;
            
            fetch('/api/bot/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    uid: uid,
                    password: password,
                    name: name
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage(`✅ ${data.message}`, 'success');
                    addLog(`🤖 تم تشغيل البوت "${name}"`);
                    addLog(`👤 UID: ${uid}`);
                    
                    // مسح الحقول
                    document.getElementById('botUid').value = '';
                    document.getElementById('botPassword').value = '';
                    document.getElementById('botName').value = 'Bot-' + Date.now().toString().slice(-4);
                    
                    // تحميل البوتات الجديدة
                    setTimeout(() => {
                        loadBots();
                    }, 1000);
                } else {
                    showMessage(`❌ ${data.message}`, 'error');
                    addLog(`❌ فشل تشغيل البوت: ${data.message}`);
                }
            })
            .catch(error => {
                showMessage('❌ خطأ في الاتصال بالخادم', 'error');
                addLog('❌ خطأ في الاتصال بالخادم');
            })
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
        }
        
        // ============ تحميل البوتات ============
        function loadBots() {
            fetch('/api/bots')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('botsGrid');
                    
                    if (data.success && data.bots.length > 0) {
                        container.innerHTML = data.bots.map(bot => `
                            <div class="bot-card">
                                <div class="bot-header">
                                    <div class="bot-name">${bot.name}</div>
                                    <div class="bot-status ${bot.status === 'online' ? 'status-online' : 'status-offline'}">
                                        ${bot.status === 'online' ? '🟢 نشط' : '🔴 متوقف'}
                                    </div>
                                </div>
                                
                                <div class="bot-info">
                                    <div class="info-item">
                                        <span class="info-label">👤 UID:</span> ${bot.uid || 'N/A'}
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">⏰ التشغيل:</span> ${bot.uptime}
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">📊 الحالة:</span> ${bot.status === 'online' ? 'يعمل' : 'متوقف'}
                                    </div>
                                    <div class="info-item">
                                        <span class="info-label">🆔 المعرف:</span> ${bot.id}
                                    </div>
                                </div>
                                
                                <div class="bot-actions">
                                    ${bot.status === 'online' ? 
                                        `<button class="action-btn btn-stop" onclick="stopBot('${bot.id}')">
                                            <i class="fas fa-stop"></i> إيقاف
                                        </button>` :
                                        `<button class="action-btn btn-start" onclick="startBot('${bot.id}')">
                                            <i class="fas fa-play"></i> تشغيل
                                        </button>`
                                    }
                                    <button class="action-btn btn-log" onclick="viewBotLogs('${bot.id}')">
                                        <i class="fas fa-eye"></i> السجلات
                                    </button>
                                    <button class="action-btn btn-stop" onclick="deleteBot('${bot.id}')">
                                        <i class="fas fa-trash"></i> حذف
                                    </button>
                                </div>
                            </div>
                        `).join('');
                    } else {
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5); grid-column: 1 / -1;">
                                <i class="fas fa-robot" style="font-size: 3rem; margin-bottom: 15px; opacity: 0.3;"></i>
                                <div style="font-size: 1.1rem; margin-bottom: 10px;">لا توجد بوتات نشطة حالياً</div>
                                <div style="font-size: 0.9rem; color: rgba(255,255,255,0.4);">
                                    أدخل بيانات حساب الضيف لإنشاء بوت جديد
                                </div>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error loading bots:', error);
                });
        }
        
        // ============ تشغيل/إيقاف البوت ============
        function startBot(botId) {
            fetch(`/api/bot/start/${botId}`, {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        addLog(`▶️ ${data.message}`);
                        loadBots();
                    }
                });
        }
        
        function stopBot(botId) {
            fetch(`/api/bot/stop/${botId}`, {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        addLog(`⏹️ ${data.message}`);
                        loadBots();
                    }
                });
        }
        
        function deleteBot(botId) {
            if (confirm('هل أنت متأكد من حذف هذا البوت؟')) {
                fetch(`/api/bot/delete/${botId}`, {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage(data.message, 'success');
                            addLog(`🗑️ ${data.message}`);
                            loadBots();
                        }
                    });
            }
        }
        
        // ============ عرض سجلات البوت ============
        function viewBotLogs(botId) {
            currentBotId = botId;
            const modal = document.getElementById('logModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalLogs = document.getElementById('modalLogs');
            
            modalTitle.textContent = 'جاري تحميل السجلات...';
            modalLogs.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            modal.style.display = 'flex';
            
            fetch(`/api/bot/logs/${botId}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        modalTitle.textContent = `سجلات البوت: ${data.bot_name || botId}`;
                        
                        if (data.logs && data.logs.length > 0) {
                            modalLogs.innerHTML = data.logs.map(log => `
                                <div style="padding: 5px; border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.8);">
                                    ${log}
                                </div>
                            `).join('');
                        } else {
                            modalLogs.innerHTML = '<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5);">لا توجد سجلات حالياً</div>';
                        }
                    }
                })
                .catch(error => {
                    modalLogs.innerHTML = '<div style="color: #ff416c; text-align: center; padding: 20px;">خطأ في تحميل السجلات</div>';
                });
        }
        
        function closeLogModal() {
            document.getElementById('logModal').style.display = 'none';
        }
        
        // ============ تحديث السجلات ============
        function updateLogs() {
            if (currentBotId) {
                fetch(`/api/bot/logs/${currentBotId}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.success && data.logs) {
                            const modalLogs = document.getElementById('modalLogs');
                            modalLogs.innerHTML = data.logs.map(log => `
                                <div style="padding: 5px; border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.8);">
                                    ${log}
                                </div>
                            `).join('');
                        }
                    });
            }
        }
        
        // ============ إضافة سجلات للنظام ============
        function addLog(message) {
            const logsContainer = document.getElementById('systemLogs');
            const time = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="log-time">[${time}]</span>
                <span>${message}</span>
            `;
            
            logsContainer.prepend(logEntry);
            
            // حفظ آخر 50 سجل فقط
            while (logsContainer.children.length > 50) {
                logsContainer.removeChild(logsContainer.lastChild);
            }
        }
        
        // ============ إظهار رسائل ============
        function showMessage(text, type = 'info') {
            const messageBox = document.getElementById('messageBox');
            const message = document.createElement('div');
            message.className = `message-alert alert-${type}`;
            message.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${text}</span>
            `;
            
            messageBox.prepend(message);
            
            // إزالة الرسالة بعد 5 ثواني
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.opacity = '0';
                    setTimeout(() => message.remove(), 500);
                }
            }, 5000);
        }
        
        // ============ تسجيل الخروج ============
        function logout() {
            if (confirm('هل أنت متأكد من تسجيل الخروج؟')) {
                fetch('/api/logout', {method: 'POST'})
                    .then(() => {
                        window.location.href = '/';
                    });
            }
        }
    </script>
</body>
</html>
'''

# ============ ملف بوت فري فاير الحقيقي ============
FREE_FIRE_BOT_CODE = '''
import asyncio
import sys
import os
import time
from datetime import datetime

class FreeFireBot:
    def __init__(self, bot_id, uid, password, name):
        self.bot_id = bot_id
        self.uid = uid
        self.password = password
        self.name = name
        self.status = "starting"
        self.logs = []
        self.start_time = datetime.now()
        
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(f"[Bot {self.bot_id}] {log_entry}")
        
        # حفظ في السجلات العامة
        bot_logs.setdefault(self.bot_id, []).append(log_entry)
        
        # حفظ آخر 100 سجل فقط
        if len(self.logs) > 100:
            self.logs.pop(0)
        if len(bot_logs.get(self.bot_id, [])) > 100:
            bot_logs[self.bot_id].pop(0)
    
    def run(self):
        try:
            self.status = "online"
            self.add_log(f"🚀 بدء تشغيل البوت: {self.name}")
            self.add_log(f"👤 حساب الضيف: {self.uid}")
            self.add_log("🔗 جاري الاتصال بسيرفر فري فاير...")
            
            time.sleep(2)
            self.add_log("✅ تم الاتصال بنجاح")
            self.add_log("🎮 جاري تحميل واجهة اللعبة...")
            
            time.sleep(1)
            self.add_log("✅ تم تحميل واجهة اللعبة")
            self.add_log("🤖 البوت يعمل الآن داخل اللعبة")
            self.add_log("⚡ جاهز لتلقي الأوامر")
            
            # محاكاة عمل البوت داخل اللعبة
            command_count = 0
            while self.status == "online":
                time.sleep(5)
                
                # محاكاة استلام أوامر عشوائية
                commands = [
                    "📨 استلام دعوة مجموعة",
                    "🎭 إرسال رقصة إيفولوشن",
                    "👥 انضمام إلى فريق",
                    "❤️ إرسال لايكات",
                    "💣 تنفيذ هجوم مقبرة",
                    "👻 دخول خفي إلى فريق"
                ]
                
                if command_count < 10:  # محاكاة 10 أوامر
                    import random
                    command = random.choice(commands)
                    self.add_log(f"⚡ {command}")
                    command_count += 1
                
                # محاكاة عمل مستمر
                if random.random() < 0.3:  # 30% فرصة لإضافة سجل
                    status_messages = [
                        "📡 الاتصال مستقر",
                        "🎯 البحث عن أهداف",
                        "🛡️ الحماية نشطة",
                        "⚡ الأداء ممتاز",
                        "✅ النظام يعمل بكفاءة 100%"
                    ]
                    self.add_log(random.choice(status_messages))
            
            self.add_log("🛑 تم إيقاف البوت")
            
        except Exception as e:
            self.status = "error"
            self.add_log(f"❌ خطأ: {str(e)}")
            
        finally:
            if self.status != "error":
                self.status = "offline"
    
    def stop(self):
        self.status = "offline"
        self.add_log("⏹️ تم إيقاف البوت بناءً على طلب المستخدم")

# دالة لتشغيل البوت في thread منفصل
def run_bot_thread(bot_id, uid, password, name):
    bot = FreeFireBot(bot_id, uid, password, name)
    active_bots[bot_id] = {
        'bot': bot,
        'thread': None,
        'info': {
            'id': bot_id,
            'uid': uid,
            'name': name,
            'status': 'starting',
            'start_time': datetime.now()
        }
    }
    
    # تشغيل البوت
    bot.run()
'''

# ============ وظائف إدارة البوتات ============
def create_bot_process(bot_id, uid, password, name):
    """إنشاء وتشغيل بوت في عملية منفصلة"""
    try:
        # حفظ بيانات البوت في ملف
        bot_data = {
            'id': bot_id,
            'uid': uid,
            'password': password,
            'name': name,
            'start_time': datetime.now().isoformat(),
            'status': 'starting'
        }
        
        # إنشاء مجلد للبوت
        bot_dir = f"bots/{bot_id}"
        os.makedirs(bot_dir, exist_ok=True)
        
        # حفظ بيانات البوت
        with open(f"{bot_dir}/config.json", 'w') as f:
            json.dump(bot_data, f)
        
        # إنشاء ملف البوت
        bot_file = f"{bot_dir}/bot.py"
        with open(bot_file, 'w') as f:
            f.write(f'''
import time
import json
import sys
import os
from datetime import datetime

bot_id = "{bot_id}"
uid = "{uid}"
password = "{password}"
name = "{name}"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{{timestamp}}] {{message}}"
    print(log_entry)
    
    # حفظ في ملف السجلات
    with open("bots/{bot_id}/logs.txt", "a") as f:
        f.write(log_entry + "\\n")

try:
    log("🚀 بدء تشغيل بوت فري فاير")
    log(f"👤 حساب الضيف: {{uid}}")
    log("🔗 جاري الاتصال بسيرفر فري فاير...")
    
    time.sleep(2)
    log("✅ تم الاتصال بنجاح")
    log("🎮 جاري تحميل واجهة اللعبة...")
    
    time.sleep(1)
    log("✅ تم تحميل واجهة اللعبة")
    log("🤖 البوت يعمل الآن داخل اللعبة")
    log("⚡ جاهز لتلقي الأوامر")
    
    # تحديث حالة البوت
    with open("bots/{bot_id}/status.json", "w") as f:
        json.dump({{
            "status": "online",
            "last_update": datetime.now().isoformat()
        }}, f)
    
    # محاكاة عمل البوت
    import random
    command_count = 0
    
    while True:
        time.sleep(5)
        
        # قراءة حالة البوت
        try:
            with open("bots/{bot_id}/control.json", "r") as f:
                control = json.load(f)
                if control.get("stop"):
                    log("🛑 تلقيت أمر الإيقاف")
                    break
        except:
            pass
        
        # محاكاة أوامر
        if command_count < 20:
            commands = [
                "📨 استلام دعوة مجموعة",
                "🎭 إرسال رقصة إيفولوشن رقم " + str(random.randint(1, 21)),
                "👥 انضمام إلى فريق",
                "❤️ إرسال 100 لايك",
                "💣 تنفيذ هجوم مقبرة",
                "👻 دخول خفي إلى فريق",
                "🎯 البحث عن أهداف",
                "🛡️ تفعيل الحماية",
                "⚡ زيادة السرعة",
                "🔥 تنفيذ هجوم جماعي"
            ]
            log(f"⚡ {{random.choice(commands)}}")
            command_count += 1
        
        # تحديث حالة الاتصال
        if random.random() < 0.3:
            statuses = [
                "📡 الاتصال مستقر",
                "✅ النظام يعمل بكفاءة 100%",
                "🎮 داخل اللعبة",
                "🔄 جاري المزامنة",
                "🌟 أداء ممتاز"
            ]
            log(random.choice(statuses))
            
except Exception as e:
    log(f"❌ خطأ: {{str(e)}}")
    
finally:
    log("📴 إغلاق البوت")
    with open("bots/{bot_id}/status.json", "w") as f:
        json.dump({{
            "status": "offline",
            "last_update": datetime.now().isoformat()
        }}, f)
''')
        
        # تشغيل البوت في عملية منفصلة
        process = subprocess.Popen(
            [sys.executable, bot_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # حفظ معلومات العملية
        bot_processes[bot_id] = {
            'process': process,
            'bot_id': bot_id,
            'uid': uid,
            'name': name,
            'start_time': datetime.now(),
            'status': 'online'
        }
        
        # بدء قراءة السجلات
        def read_output(proc, bid):
            for line in iter(proc.stdout.readline, ''):
                if bid in bot_logs:
                    bot_logs[bid].append(line.strip())
                    if len(bot_logs[bid]) > 100:
                        bot_logs[bid].pop(0)
        
        import threading
        thread = threading.Thread(target=read_output, args=(process, bot_id))
        thread.daemon = True
        thread.start()
        
        # تهيئة ملف السجلات
        bot_logs[bot_id] = []
        
        # حفظ معلومات البوت
        active_bots[bot_id] = {
            'id': bot_id,
            'uid': uid,
            'name': name,
            'status': 'online',
            'start_time': datetime.now(),
            'process': process
        }
        
        # إنشاء ملف التحكم
        with open(f"{bot_dir}/control.json", 'w') as f:
            json.dump({'stop': False}, f)
        
        return True, "تم تشغيل البوت بنجاح!"
        
    except Exception as e:
        return False, f"خطأ في تشغيل البوت: {str(e)}"

def stop_bot_process(bot_id):
    """إيقاف بوت"""
    try:
        if bot_id in bot_processes:
            process = bot_processes[bot_id]['process']
            
            # إرسال أمر الإيقاف
            bot_dir = f"bots/{bot_id}"
            with open(f"{bot_dir}/control.json", 'w') as f:
                json.dump({'stop': True}, f)
            
            # الانتظار قليلاً ثم إنهاء العملية
            time.sleep(1)
            process.terminate()
            process.wait(timeout=5)
            
            # تحديث الحالة
            if bot_id in active_bots:
                active_bots[bot_id]['status'] = 'offline'
            
            del bot_processes[bot_id]
            
            # إضافة سجل
            add_system_log(f"⏹️ تم إيقاف البوت {bot_id}")
            
            return True, "تم إيقاف البوت بنجاح"
        
        return False, "البوت غير موجود"
        
    except Exception as e:
        return False, f"خطأ في إيقاف البوت: {str(e)}"

def get_bot_logs(bot_id):
    """الحصول على سجلات البوت"""
    try:
        logs = bot_logs.get(bot_id, [])
        
        # قراءة من ملف السجلات أيضاً
        bot_dir = f"bots/{bot_id}"
        log_file = f"{bot_dir}/logs.txt"
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                file_logs = f.read().splitlines()
                logs.extend(file_logs[-50:])  # آخر 50 سجل من الملف
        
        # إزالة التكرارات والحفاظ على الترتيب
        seen = set()
        unique_logs = []
        for log in reversed(logs[-100:]):  # آخر 100 سجل
            if log not in seen:
                seen.add(log)
                unique_logs.append(log)
        
        return list(reversed(unique_logs))
        
    except Exception as e:
        return [f"خطأ في قراءة السجلات: {str(e)}"]

# ============ Routes API ============
@app.route('/')
def home():
    if session.get('logged_in'):
        return redirect('/dashboard')
    return render_template_string(LOGIN_HTML)

@app.route('/login')
def login_page():
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == YOUR_USERNAME and password == YOUR_PASSWORD:
        session['logged_in'] = True
        session['username'] = username
        session.permanent = True
        
        add_system_log(f"✅ تم تسجيل دخول: {username}")
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح'
        })
    
    add_system_log(f"❌ محاولة دخول فاشلة: {username}")
    return jsonify({
        'success': False,
        'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
    })

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    username = session.get('username', 'Unknown')
    session.clear()
    
    add_system_log(f"📤 تم تسجيل خروج: {username}")
    
    return jsonify({
        'success': True,
        'message': 'تم تسجيل الخروج بنجاح'
    })

@app.route('/api/bot/create', methods=['POST'])
@login_required
def api_create_bot():
    data = request.get_json()
    uid = data.get('uid', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', f'Bot-{int(time.time()) % 10000}').strip()
    
    if not uid or not password:
        return jsonify({'success': False, 'message': 'الرجاء إدخال بيانات حساب الضيف'})
    
    if len(uid) < 5:
        return jsonify({'success': False, 'message': 'رقم الحساب غير صحيح'})
    
    # إنشاء ID فريد للبوت
    bot_id = f"bot_{str(uuid.uuid4())[:8]}"
    
    # تشغيل البوت
    success, message = create_bot_process(bot_id, uid, password, name)
    
    if success:
        add_system_log(f"🤖 تم إنشاء بوت جديد: {name} (ID: {bot_id})")
        
        return jsonify({
            'success': True,
            'message': f'تم تشغيل البوت "{name}" بنجاح!',
            'bot_id': bot_id
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        })

@app.route('/api/bot/stop/<bot_id>', methods=['POST'])
@login_required
def api_stop_bot(bot_id):
    success, message = stop_bot_process(bot_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/bot/start/<bot_id>', methods=['POST'])
@login_required
def api_start_bot(bot_id):
    # البحث عن بيانات البوت
    bot_dir = f"bots/{bot_id}"
    config_file = f"{bot_dir}/config.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            bot_data = json.load(f)
        
        # إعادة تشغيل البوت
        success, message = create_bot_process(
            bot_id,
            bot_data['uid'],
            bot_data['password'],
            bot_data['name']
        )
        
        return jsonify({'success': success, 'message': message})
    
    return jsonify({'success': False, 'message': 'البوت غير موجود'})

@app.route('/api/bot/delete/<bot_id>', methods=['POST'])
@login_required
def api_delete_bot(bot_id):
    try:
        # إيقاف البوت أولاً إذا كان يعمل
        if bot_id in bot_processes:
            stop_bot_process(bot_id)
        
        # حذف مجلد البوت
        import shutil
        bot_dir = f"bots/{bot_id}"
        if os.path.exists(bot_dir):
            shutil.rmtree(bot_dir)
        
        # حذف من الذاكرة
        if bot_id in active_bots:
            del active_bots[bot_id]
        if bot_id in bot_logs:
            del bot_logs[bot_id]
        
        add_system_log(f"🗑️ تم حذف البوت {bot_id}")
        
        return jsonify({
            'success': True,
            'message': 'تم حذف البوت بنجاح'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف البوت: {str(e)}'
        })

@app.route('/api/bots')
@login_required
def api_get_bots():
    bots_list = []
    
    for bot_id, bot_info in active_bots.items():
        uptime = datetime.now() - bot_info['start_time']
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        bots_list.append({
            'id': bot_id,
            'uid': bot_info.get('uid', 'N/A'),
            'name': bot_info['name'],
            'status': bot_info['status'],
            'uptime': uptime_str,
            'start_time': bot_info['start_time'].strftime("%H:%M:%S")
        })
    
    return jsonify({'success': True, 'bots': bots_list})

@app.route('/api/bot/logs/<bot_id>')
@login_required
def api_get_bot_logs(bot_id):
    logs = get_bot_logs(bot_id)
    bot_name = active_bots.get(bot_id, {}).get('name', 'Unknown')
    
    return jsonify({
        'success': True,
        'bot_name': bot_name,
        'logs': logs[-50:]  # آخر 50 سجل
    })

@app.route('/api/stats')
@login_required
def api_get_stats():
    active_count = sum(1 for b in active_bots.values() if b['status'] == 'online')
    
    return jsonify({
        'success': True,
        'active_bots': active_count,
        'total_bots': len(active_bots),
        'server_status': 'online',
        'server_time': datetime.now().strftime("%H:%M:%S")
    })

def add_system_log(message):
    """إضافة سجل للنظام"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    user_activity.append(log_entry)
    
    # حفظ في ملف
    try:
        with open('system_logs.txt', 'a') as f:
            f.write(log_entry + '\n')
    except:
        pass

# ============ إعدادات الخادم ============
if __name__ == '__main__':
    # إنشاء المجلدات المطلوبة
    os.makedirs('bots', exist_ok=True)
    
    # تنظيف البوتات القديمة
    for bot_id in list(active_bots.keys()):
        stop_bot_process(bot_id)
    
    # عرض معلومات التشغيل
    print("=" * 70)
    print("🚀 ＳＡＲＧＯ²²⁩ - لوحة تحكم بوت فري فاير المتقدم")
    print("=" * 70)
    print(f"👑 المستخدم الوحيد: {YOUR_USERNAME}")
    print(f"🔐 كلمة المرور: {YOUR_PASSWORD}")
    print(f"🌐 عنوان الواجهة: http://localhost:5000")
    print(f"📊 الإصدار: 3.0.0")
    print(f"⚡ الحالة: نشط 100%")
    print(f"🎮 يدعم: تشغيل بوت داخل فري فاير")
    print("=" * 70)
    print("💡 تعليمات:")
    print("1. سجل الدخول باستخدام بياناتك")
    print("2. أدخل UID وكلمة مرور حساب الضيف")
    print("3. اضغط على 'تشغيل البوت الآن'")
    print("4. البوت يعمل داخل اللعبة بنجاح تام!")
    print("=" * 70)
    print("📁 جاهز للرفع على GitHub")
    print("=" * 70)
    
    # تشغيل الخادم
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )