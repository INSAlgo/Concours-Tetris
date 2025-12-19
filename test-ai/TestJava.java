import java.util.*;

class TestJava {

    static int W, H;
    static Map<String, List<int[]>> pieces = new HashMap<>();

    static void loadInputs() {
        Scanner scanner = new Scanner(System.in);
        String[] wh = scanner.nextLine().split(" ");
        W = Integer.parseInt(wh[0]);
        H = Integer.parseInt(wh[1]);
        int N = Integer.parseInt(scanner.nextLine());
        for (int i = 0; i < N; i++) {
            String line = scanner.nextLine();
            String[] parts = line.split(" ");
            String name = parts[0];
            List<int[]> coords = new ArrayList<>();
            for (int j = 1; j < parts.length; j++) {
                String[] xy = parts[j].split(",");
                int x = Integer.parseInt(xy[0]);
                int y = Integer.parseInt(xy[1]);
                coords.add(new int[]{x, y});
            }
            pieces.put(name, coords);
        }
    }

    public static void main(String[] args) {
        loadInputs();
        Scanner scanner = new Scanner(System.in);
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