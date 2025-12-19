using System;

class Program
{
    static void Main()
    {
        // Read WIDTH and HEIGHT from first line
        string input = Console.ReadLine();
        string[] parts = input.Split(' ');
        int W = int.Parse(parts[0]);
        int H = int.Parse(parts[1]);

        // Read number of pieces
        int numPieces = int.Parse(Console.ReadLine());

        // Discard the shape lines
        for (int i = 0; i < numPieces; i++)
        {
            Console.ReadLine();
        }

        Random rand = new Random();

        string line;
        while ((line = Console.ReadLine()) != null)
        {
            // Parse the piece name from the line
            string[] pieceParts = line.Split(' ');
            string pieceName = pieceParts[0];

            // Generate random x (0 to W-1) and rotation (0-3)
            int x = rand.Next(0, W);
            int rotation = rand.Next(0, 4);

            // Output the result
            Console.WriteLine($"{x} {rotation}");
        }
    }
}