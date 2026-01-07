
#include <iostream>
#include <vector>

using namespace std;

int main() {
    int n;
    cin >> n;

    // Handle the case where n is 0
    if (n == 0) {
        cout << 1 << endl;
        return 0;
    }

    // Use a vector to store the digits of the factorial result
    vector<int> result(1, 1);

    for (int i = 2; i <= n; ++i) {
        // Multiply the current result by i
        int carry = 0;
        for (int j = 0; j < result.size(); ++j) {
            int product = result[j] * i + carry;
            result[j] = product % 10;
            carry = product / 10;
        }

        // Add any remaining carry
        while (carry > 0) {
            result.push_back(carry % 10);
            carry /= 10;
        }
    }

    // Output the result
    for (int digit : result) {
        cout << digit;
    }
    cout << endl;

    return 0;
}
