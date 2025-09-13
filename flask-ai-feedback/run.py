from app import create_app

# 通过应用工厂创建 app 实例
app = create_app()

if __name__ == '__main__':
    # 使用环境变量或 app.config 来获取配置
    # 这里的参数是为了保持和您原始代码一致
    app.run(debug=True, port=5001, host='0.0.0.0')