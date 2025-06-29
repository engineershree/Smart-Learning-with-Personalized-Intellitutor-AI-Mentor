#!/usr/bin/env python
from simple_app import app

if __name__ == '__main__':
    port = 3000
    print(f"Starting server at http://localhost:{port}")
    app.run(host='localhost', port=port, debug=True) 