let ws = new WebSocket(
  (window.location.protocol === "https:" ? "wss://" : "ws://") +
    window.location.host +
    "/ws"
);

let last_prompt = null;
let last_seed = null;
let last_sent = null;

// async function testStability {
//     var
//     fetch("")
//     //https://api.stability.ai/v1alpha/generation/stable-diffusion-512-v2-0/text-to-image"  -H 'Content-Type: application/json'  -H 'Accept: image/png' -H "Authorization: sk-2ZP1rHM6OsQzzedLAkeHzPiZeAd5PYAWek35JqKpPsWsgitW"  --data-raw '{"cfg_scale": 7,"clip_guidance_preset": "NONE","height": 512,"width": 512,"samples": 1,"seed": 0,"steps": 50,"text_prompts": [{"text": "A lighthouse on a cliff","weight": 1}]}'
// }

async function getPrompt() {
  var prompt = document.getElementById("prompt");
  var seed = document.getElementById("seed");
  while (true) {
    if (prompt && prompt.value) {
      if (prompt.value != last_prompt || seed.value != last_seed) {
        last_prompt = prompt.value;
        last_seed = seed;
        last_sent = Date.now();
        console.time("generation");
        return JSON.stringify({ prompt: prompt.value, seed: seed.value });
      }
    }
    await new Promise((r) => setTimeout(r, 100));
  }
}

ws.addEventListener("message", ({ data }) => {
  var parsed = JSON.parse(data);
  var latency = Math.round(Date.now() - last_sent - parsed.gen_time * 1000);
  var latencyField = document.getElementById("latency");
  latencyField.textContent = `latency: ${latency}ms`;
  document.getElementById("gen_time").textContent = `generation: ${parsed.gen_time}ms`;
  var top = document.getElementById("imoge");
  var bottom = document.getElementById("imoge2");
  if (top.style.opacity == 1) {
    bottom.src = parsed.image;
    bottom.style.opacity = 1;
    top.style.opacity = 0;
  } else {
    top.src = parsed.image;
    top.style.opacity = 1;
    bottom.style.opacity = 0;
  }
  getPrompt().then((t) => ws.send(t));
});

new Promise((r) => setTimeout(r, 100)).then(() =>
  getPrompt().then((t) => ws.send(t))
);
