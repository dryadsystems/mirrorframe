# Copyright (c) 2022 Dryad Systems
import logging
import os
import base64
import json
import time
from io import BytesIO
import torch
from aiohttp import web
from pipeline_stable_diffusion_ait import StableDiffusionAITPipeline

logging.getLogger().setLevel("DEBUG")
script = open("client.js").read()

html = (
    f"<!DOCTYPE HTML><head><script>{script}</script>"
    """
    <style>img { transition:opacity 1s linear; position: absolute; top:5%; left: 25%; width:512px;height: 512px}</style>
    </head>
    <div style = "margin: 5%">
        <img id="imoge" alt="imoge" src="" style="opacity:0;"><br/>
        <img id="imoge2" alt="imoge" src="" style="opacity:1;"><br/>
        <textarea id="prompt" name="prompt" value=""></textarea><br/>
        <input id="seed" name="seed" value="42" type="hidden">
        <span id="latency"></span><br/>
    </div>
    """
)


class Live:
    def __init__(self) -> None:
        token = os.getenv("HF_TOKEN")
        args: dict = {"use_auth_token": token} if token else {"local_files_only": True}
        self.txt_pipe = StableDiffusionAITPipeline.from_pretrained(
            "stabilityai/stable-diffusion-2-base",
            revision="fp16",
            torch_dtype=torch.float16,
            safety_checker=None,
            **args,
        ).to("cuda")

    def generate(self, params: dict) -> str:
        shared_params = {
            "prompt": params["prompt"],
            # maybe use num_images_per_prompt? think about batch v serial
            "height": params.get("height", 512),
            "width": params.get("width", 512),
            "num_inference_steps": params.get("ddim_steps", 35),
            "guidance_scale": params.get("scale", 7.5),
        }
        logging.info(params["prompt"])
        rng = torch.Generator(device="cuda").manual_seed(int(params.get("seed", 42)))
        start = time.time()
        output = self.txt_pipe(generator=rng, **shared_params)
        logging.info("took %s", round(time.time() - start, 3))
        buf = BytesIO()
        output.images[0].save(buf, format="webp")
        buf.seek(0)
        resp = {
            "gen_time": time.time() - start,
            "image": f"data:image/webp;base64,{base64.b64encode(buf.read()).decode()}",
        }
        return json.dumps(resp)

    async def index(self, req: web.Request) -> web.Response:
        return web.Response(body=html, content_type="text/html")

    async def handle_ws(self, request: web.Request) -> web.Response:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logging.info("ws connected")
        async for msg in ws:
            # async with generate_lock:
            image = self.generate(json.loads(msg.data))
            await ws.send_str(image)
        return ws

    async def handle_endpoint(self, request: web.Request) -> web.Response:
        params = await request.json()
        prompt = params["text_prompts"][0]["text"]
        start = time.time()
        shared_params = {
            "prompt": prompt,
            # maybe use num_images_per_prompt? think about batch v serial
            "height": params.get("height", 512),
            "width": params.get("width", 512),
            "num_inference_steps": params.get("steps", 35),
            "guidance_scale": params.get("cfg_scale", 7.5),
        }
        rng = torch.Generator(device="cuda").manual_seed(int(params.get("seed", 42)))
        start = time.time()
        output = self.txt_pipe(generator=rng, **shared_params)
        logging.info("took %s", round(time.time() - start, 3))
        buf = BytesIO()
        output.images[0].save(buf, format="png")
        print(f"took {time.time() - start}")
        buf.seek(0)
        resp = web.Response(body=buf.read(), content_type="image/png")
        # resp.enable_compression(force=True)
        return resp


app = web.Application()
live = Live()
app.add_routes(
    [
        web.route("*", "/", live.index),
        web.get("/ws", live.handle_ws),
        web.post(
            "/v1alpha/generation/stable-diffusion-512-v2-0/text-to-image",
            live.handle_endpoint,
        ),
    ]
)

if __name__ == "__main__":
    web.run_app(app, port=8080, host="0.0.0.0")
