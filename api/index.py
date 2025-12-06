from python.App_Flask import app

# Vercel serverless function handler
def handler(request):
    return app(request)
