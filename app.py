"""
Flask Web API for Multi-Agent Data Query System
提供RESTful API接口供前端调用
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from typing import Dict, Any

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from agent import MultiAgentSystem

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # 允许跨域请求

# 全局系统实例（用于存储不同用户的会话）
user_systems: Dict[str, MultiAgentSystem] = {}


def get_or_create_system(user_id: str) -> MultiAgentSystem:
    """获取或创建用户的系统实例"""
    if user_id not in user_systems:
        system = MultiAgentSystem()
        system.login(user_id)
        user_systems[user_id] = system
    return user_systems[user_id]


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.json
        user_id = data.get('user_id', 'guest')
        
        # 创建或获取用户系统
        system = get_or_create_system(user_id)

        # 直接从长期记忆数据库加载用户信息（无需等待对话总结）
        ltm = system.master_agent.long_term_memory
        profile = ltm.get_user_profile(user_id)
        preferences = ltm.get_all_preferences(user_id)
        knowledge = ltm.get_all_knowledge(user_id, limit=50)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_id': system.session_id,
            'message': f'欢迎 {user_id}！',
            'user_info': {
                'logged_in': True,
                'user_id': user_id,
                'session_id': system.session_id,
                'profile': profile,
                'preferences': preferences,
                'knowledge': knowledge
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def query():
    """查询接口"""
    try:
        data = request.json
        user_id = data.get('user_id', 'guest')
        question = data.get('question', '')
        
        if not question.strip():
            return jsonify({
                'success': False,
                'error': '问题不能为空'
            }), 400
        
        # 获取用户系统
        system = get_or_create_system(user_id)
        
        # 执行查询
        answer = system.query(question)
        
        return jsonify({
            'success': True,
            'answer': answer,
            'user_id': user_id,
            'session_id': system.session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/new_session', methods=['POST'])
def new_session():
    """创建新会话"""
    try:
        data = request.json
        user_id = data.get('user_id', 'guest')
        
        system = get_or_create_system(user_id)
        system.new_session()
        
        return jsonify({
            'success': True,
            'session_id': system.session_id,
            'message': '已开始新会话'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/user_info', methods=['POST'])
def user_info():
    """获取用户信息"""
    try:
        data = request.json
        user_id = data.get('user_id', 'guest')
        
        system = get_or_create_system(user_id)
        # 直接读取长期记忆，包括知识列表
        ltm = system.master_agent.long_term_memory
        info = system.get_user_info()
        info['knowledge'] = ltm.get_all_knowledge(user_id, limit=50)

        return jsonify({
            'success': True,
            'user_info': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'active_users': len(user_systems)
    })


if __name__ == '__main__':
    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("错误：未设置 DASHSCOPE_API_KEY 环境变量")
        sys.exit(1)
    
    print("🚀 多智能体数据查询系统 Web API 启动中...")
    print("📡 访问地址: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

