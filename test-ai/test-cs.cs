using System;
using System.Collections.Generic;

class Program
{
    static int W, H;
    static Dictionary<string, List<(int, int)>> Pieces = new();

    static void LoadInputs()
    {
        // Read WIDTH and HEIGHT from first line
        string input = Console.ReadLine();
        string[] parts = input.Split(' ');
        W = int.Parse(parts[0]);
        H = int.Parse(parts[1]);

        // Read number of pieces
        int numPieces = int.Parse(Console.ReadLine());

        // Read piece definitions
        for (int i = 0; i < numPieces; i++)
        {
            string line = Console.ReadLine();
            string[] pieceParts = line.Split(' ');
            string name = pieceParts[0];
            List<(int, int)> positions = new();
            for (int j = 1; j < pieceParts.Length; j++)
            {
                string[] coords = pieceParts[j].Split(',');
                int x = int.Parse(coords[0]);
                int y = int.Parse(coords[1]);
                positions.Add((x, y));
            }
            Pieces[name] = positions;
        }
    }

    static void Main()
    {
        LoadInputs();

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