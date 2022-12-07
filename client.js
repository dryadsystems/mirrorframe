let ws = new WebSocket(
  (window.location.protocol === "https:" ? "wss://" : "ws://") +
    window.location.host +
    "/ws"
);

let last_prompt = null;
let last_seed = null;

async function getPrompt() {
  var prompt = document.getElementById("prompt");
  var seed = document.getElementById("seed");
  while (true) {
    if (prompt && prompt.value) {
      if (prompt.value != last_prompt || seed.value != last_seed) {
        last_prompt = prompt.value;
        last_seed = seed;
        console.time("generation")
        return JSON.stringify({ prompt: prompt.value, seed: seed.value });
      }
    }
    await new Promise((r) => setTimeout(r, 100));
  }
}

ws.addEventListener("message", ({ data }) => {
  console.timeEnd("generation")
  var top = document.getElementById("imoge");
  var bottom = document.getElementById("imoge2");
  if (top.style.opacity == 1) {
    bottom.src = data;
    bottom.style.opacity = 1;
    top.style.opacity = 0;
  } else {
    top.src = data;
    top.style.opacity = 1;
    bottom.style.opacity = 0;
  }
  getPrompt().then((t) => ws.send(t));
});

new Promise((r) => setTimeout(r, 100)).then(() =>
  getPrompt().then((t) => ws.send(t))
);
