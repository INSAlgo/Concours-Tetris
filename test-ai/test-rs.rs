use std::io::{self, BufRead};
use rand::Rng;
use std::collections::HashMap;

type Result<T, E = Box<dyn std::error::Error>> = std::result::Result<T, E>;

static mut W: i32 = 0;
static mut H: i32 = 0;
static mut PIECES: HashMap<String, Vec<(i32, i32)>> = HashMap::new();

fn load_inputs() -> Result<()> {
    let stdin = io::stdin();
    let mut lines = stdin.lines();

    // Read WIDTH and HEIGHT from first line
    let first_line = lines.next().ok_or("No input")??;
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let w: i32 = parts[0].parse()?;
    let h: i32 = parts[1].parse()?;

    // Read number of pieces
    let num_pieces_line = lines.next().ok_or("No number of pieces")??;
    let num_pieces: usize = num_pieces_line.trim().parse()?;

    let mut pieces = HashMap::new();
    for _ in 0..num_pieces {
        let line = lines.next().ok_or("Not enough shape lines")??;
        let mut parts: Vec<&str> = line.split_whitespace().collect();
        let name = parts[0].to_string();
        parts.remove(0);
        let mut coords = Vec::new();
        for coord in parts {
            let xy: Vec<&str> = coord.split(',').collect();
            let x: i32 = xy[0].parse()?;
            let y: i32 = xy[1].parse()?;
            coords.push((x, y));
        }
        pieces.insert(name, coords);
    }

    unsafe {
        W = w;
        H = h;
        PIECES = pieces;
    }

    Ok(())
}

fn main() -> Result<()> {
    load_inputs()?;

    let stdin = io::stdin();
    let mut lines = stdin.lines();

    let mut rng = rand::thread_rng();

    loop {
        let line = match lines.next() {
            Some(l) => l?,
            None => break,
        };
        // Parse the piece name (first word)
        let piece_name = line.split_whitespace().next().unwrap_or("");

        // Generate random x (0 to W-1) and rotation (0-3)
        let x = rng.gen_range(0..unsafe { W });
        let rotation = rng.gen_range(0..4);

        println!("{} {}", x, rotation);
        io::stdout().flush()?;
    }

    Ok(())
}