const fs = require('fs');

let W, H;
let pieces = {};

function loadInputs() {
  const allInput = fs.readFileSync(0, 'utf-8').trim();
  const lines = allInput.split('\n');
  let idx = 0;

  const [w, h] = lines[idx++].trim().split(/\s+/).map(Number);
  W = w;
  H = h;

  const N = parseInt(lines[idx++].trim());
  pieces = {};
  for (let i = 0; i < N; i++) {
    const parts = lines[idx++].trim().split(/\s+/);
    const name = parts[0];
    const coords = parts.slice(1).map(coord => {
      const [x, y] = coord.split(',').map(Number);
      return [x, y];
    });
    pieces[name] = coords;
  }

  // Process the remaining lines as game inputs
  for (let j = idx; j < lines.length; j++) {
    const line = lines[j].trim();
    if (line === '') continue;
    // Assuming each line is a game state, output random move
    const x = Math.floor(Math.random() * W);
    const rotation = Math.floor(Math.random() * 4);
    console.log(`${x} ${rotation}`);
  }
}

loadInputs();