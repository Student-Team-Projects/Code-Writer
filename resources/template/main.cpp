
#include <iostream>
#include <stdexcept>

// Function to calculate the factorial of a number
unsigned long long factorial(int n) {
    if (n < 0) {
        throw std::invalid_argument("Factorial is not defined for negative numbers.");
    }
    unsigned long long result = 1;
    for (int i = 1; i <= n; ++i) {
        result *= static_cast<unsigned long long>(i);
    }
    return result;
}

int main() {
    try {
        int input;
        std::cin >> input;
        unsigned long long result = factorial(input);
        std::cout << result << std::endl;
    } catch (const std::invalid_argument& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "An unexpected error occurred." << std::endl;
        return 1;
    }
    return 0;
}
