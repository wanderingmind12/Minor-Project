#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>

using namespace std;

// Function to calculate the total cost of connecting all wind farms to the control center
long long calculateCost(const vector<int>& x, const vector<int>& y, const vector<int>& premium, int cx, int cy) {
    long long totalCost = 0;
    int n = x.size();
    for (int i = 0; i < n; ++i) {
        int dist = abs(x[i] - cx) + abs(y[i] - cy);
        totalCost += (long long)premium[i] * dist;
    }
    return totalCost;
}

// Function to find the median in a sorted vector
int findMedian(vector<int>& v) {
    int n = v.size();
    sort(v.begin(), v.end());
    if (n % 2 == 0) {
        return v[n / 2 - 1]; // If even, take the lower median
    }
    return v[n / 2]; // If odd, take the middle element
}

int main() {
    int n;
    cin >> n; // Number of wind farms

    vector<int> x(n), y(n), premium(n);

    // Input coordinates and premium costs for each wind farm
    for (int i = 0; i < n; ++i) {
        cin >> x[i] >> y[i] >> premium[i];
    }

    // Find the median for x and y coordinates
    int cx = findMedian(x);
    int cy = findMedian(y);

    // Calculate the minimum cost to connect all wind farms to the control center at (cx, cy)
    long long minCost = calculateCost(x, y, premium, cx, cy);

    // Output the minimum cost
    cout << minCost << endl;

    return 0;
}

