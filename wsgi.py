from app import create_app

# Always use production config for Docker deployment
app = create_app('production')

if __name__ == "__main__":
    app.run()