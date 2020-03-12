from server import main_server

def run_server():
    
    main_server.run("server.main_app:app", host='localhost', port=8000, reload=False)

run_server()