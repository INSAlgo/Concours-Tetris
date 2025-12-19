import java.util.Scanner;
import java.util.Random;

class TestJava {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int W = scanner.nextInt();
        int H = scanner.nextInt();
        scanner.nextLine(); // consume the rest of the line

        int numPieces = scanner.nextInt();
        scanner.nextLine(); // consume the rest of the line

        // Discard the shape lines
        for (int i = 0; i < numPieces; i++) {
            scanner.nextLine();
        }

        Random rand = new Random();

        while (scanner.hasNextLine()) {
            String line = scanner.nextLine();
            if (line.trim().isEmpty()) continue;
            String pieceName = line.split("\\s+")[0];
            // parse the name, but for random AI, not used
            int x = rand.nextInt(W);
            int rotation = rand.nextInt(4);
            System.out.println(x + " " + rotation);
        }
    }
}