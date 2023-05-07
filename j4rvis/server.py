from langchain.agents import AgentExecutor
from auth import verify_password
from aiohttp import web
import aiohttp_cors
import jwt
import traceback
import secrets
import datetime

# Secret key to sign JWT tokens
SECRET_KEY = secrets.token_hex(32)

# JWT blacklist set
jwt_blacklist = set()


# JWT token validation decorator
def check_jwt(handler):
    async def middleware_handler(self, request):
        token = request.headers.get("Authorization", None)
        if not token:
            return web.json_response({"error": "Missing Authorization header"})
        try:
            _ = jwt.decode(token, SECRET_KEY, algorithms="HS256")
            if token in jwt_blacklist:
                return web.json_response({"error": "Invalid JWT token"})
        except jwt.InvalidTokenError:
            return web.json_response({"error": "Invalid JWT token"})
        return await handler(self, request)

    return middleware_handler


class WebServer:
    def __init__(self, agent: AgentExecutor, password_hash: bytes) -> None:
        self.agent = agent
        self.password_hash = password_hash

    async def create_token(self, request):
        data = await request.json()
        password = data.get("password", None)
        if verify_password(password, self.password_hash):
            payload = {
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=365),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return web.json_response({"token": token})
        else:
            return web.json_response({"error": "unable to verify password"})

    @check_jwt
    async def invalidate_token(self, request):
        token = request.headers.get("Authorization", None)
        jwt_blacklist.add(token)
        return web.json_response({"status": "Token invalidated"})

    @check_jwt
    async def ask(self, request):
        # Read the JSON body of the request
        data = await request.json()
        input_question = data.get("input", None)
        if not input_question:
            return web.json_response({"error": "invalid input or empty question"})

        try:
            # Run the agent using the input_question
            result = self.agent.run(input_question)

            # Prepare the JSON response
            response_data = {"content": result, "bot": True}

            # Return the JSON response
            return web.json_response(response_data)

        except AttributeError:
            traceback.print_exc()
            return web.json_response({"error": "an attribute error happened"})

    def build_app(self):
        app = web.Application()
        app.add_routes(
            [
                web.post("/create_token", self.create_token),
                web.post("/invalidate_token", self.invalidate_token),
                web.post("/ask", self.ask),
            ]
        )
        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            },
        )
        for route in list(app.router.routes()):
            cors.add(route)
        return app
