use std::io::{self, BufRead};
use rand::Rng;

type Result<T, E = Box<dyn std::error::Error>> = std::result::Result<T, E>;

fn main() -> Result<()> {
    let stdin = io::stdin();
    let mut lines = stdin.lines();

    // Read WIDTH and HEIGHT from first line
    let first_line = lines.next().ok_or("No input")??;
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let w: usize = parts[0].parse()?;
    let h: usize = parts[1].parse()?;

    // Read number of pieces
    let num_pieces_line = lines.next().ok_or("No number of pieces")??;
    let num_pieces: usize = num_pieces_line.trim().parse()?;

    // Discard num_pieces lines for shapes
    for _ in 0..num_pieces {
        lines.next().ok_or("Not enough shape lines")??;
    }

    let mut rng = rand::thread_rng();

    loop {
        let line = match lines.next() {
            Some(l) => l?,
            None => break,
        };
        // Parse the piece name (first word)
        let piece_name = line.split_whitespace().next().unwrap_or("");

        // Generate random x (0 to W-1) and rotation (0-3)
        let x = rng.gen_range(0..w);
        let rotation = rng.gen_range(0..4);

        println!("{} {}", x, rotation);
        io::stdout().flush()?;
    }

    Ok(())
}