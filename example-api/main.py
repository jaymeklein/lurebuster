import uvicorn
from fastapi import FastAPI, Request, Response
from time import sleep
import random
import json

from model import Model


app = FastAPI()
@app.post("/example-endpoint", status_code=200)
async def example_endpoint(request: Request, data: Model):
    headers = dict(request.headers)
    if headers:
        print(f"headers: {json.dumps(headers, indent=4)}")

    if data:
        print(f"parameters: {json.dumps(data.model_dump(), indent=4)}")

    sleep(random.randint(0, 3))
    if random.random() > 0.7: # 30% Internal Error chance
        raise ValueError('Error!')

    return {"message": "Person information saved!"}

@app.get("/", status_code=200)
async def hello_lurebuster():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LureBuster Example Endpoint</title>
    </head>
    <body>
        <h1>Hello, LureBuster!</h1>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
