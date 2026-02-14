from mangum import Mangum
from app.main import app

# Vercel serverless function handler
handler = Mangum(app)
