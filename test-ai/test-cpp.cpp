#include <iostream>
#include <string>
#include <sstream>
#include <cstdlib>
#include <ctime>
#include <map>
#include <vector>

using namespace std;

int W, H;
std::map<std::string, std::vector<std::pair<int, int>>> pieces;

void load_inputs() {
    std::string line;
    std::getline(std::cin, line);
    std::stringstream ss(line);
    ss >> W >> H;
    std::getline(std::cin, line);
    ss.str(line);
    ss.clear();
    int N;
    ss >> N;
    for(int i = 0; i < N; i++) {
        std::getline(std::cin, line);
        std::stringstream ss2(line);
        std::string name;
        ss2 >> name;
        std::vector<std::pair<int, int>> coords;
        std::string coord;
        while(ss2 >> coord) {
            size_t comma = coord.find(',');
            int x = std::stoi(coord.substr(0, comma));
            int y = std::stoi(coord.substr(comma + 1));
            coords.push_back({x, y});
        }
        pieces[name] = coords;
    }
}

int main()
{
    load_inputs();

    srand(time(NULL)); // Seed random number generator

    string line;
    while (getline(cin, line))
    {
        // Parse the piece name from the line
        stringstream ss(line);
        string piece_name;
        ss >> piece_name;

        // Generate random x (0 to W-1) and rotation (0-3)
        int x = rand() % W;
        int rotation = rand() % 4;

        // Output the result
        cout << x << " " << rotation << endl;
    }

    return 0;
}