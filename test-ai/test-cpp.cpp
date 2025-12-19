#include <iostream>
#include <string>
#include <sstream>
#include <cstdlib>
#include <ctime>

using namespace std;

int main()
{
    int WIDTH, HEIGHT;
    cin >> WIDTH >> HEIGHT;
    cin.ignore(); // Ignore the newline after reading WIDTH and HEIGHT

    int N;
    cin >> N;
    cin.ignore(); // Ignore the newline after reading N

    // Discard N lines for the shapes
    for(int i = 0; i < N; i++)
    {
        string dummy;
        getline(cin, dummy);
    }

    srand(time(NULL)); // Seed random number generator

    string line;
    while (getline(cin, line))
    {
        // Parse the piece name from the line
        stringstream ss(line);
        string piece_name;
        ss >> piece_name;

        // Generate random x (0 to WIDTH-1) and rotation (0-3)
        int x = rand() % WIDTH;
        int rotation = rand() % 4;

        // Output the result
        cout << x << " " << rotation << endl;
    }

    return 0;
}