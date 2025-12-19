const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

let firstLine = true;
let W, H;
let numPieces = null;
let skipCount = 0;

rl.on('line', (line) => {
  if (firstLine) {
    [W, H] = line.trim().split(/\s+/).map(Number);
    firstLine = false;
  } else if (numPieces === null) {
    numPieces = parseInt(line.trim());
    skipCount = numPieces;
  } else if (skipCount > 0) {
    skipCount--;
  } else {
    const piece_name = line.trim().split(/\s+/)[0];
    // Output random x (0 to W-1) and random rotation (0-3)
    const x = Math.floor(Math.random() * W);
    const rotation = Math.floor(Math.random() * 4);
    console.log(`${x} ${rotation}`);
  }
});

rl.on('close', () => {
  process.exit(0);
});