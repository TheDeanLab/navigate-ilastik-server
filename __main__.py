from aslm_server import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000)