#include <iostream>

long long factorial(int n) {
    if (n < 0) {
        throw std::invalid_argument("Factorial is not defined for negative numbers.");
    }
    long long result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

int main() {
    int n;
    std::cout << "Enter a number: ";
    std::cin >> n;

    try {
        std::cout  << factorial(n) << std::endl;
    } catch (const std::invalid_argument &e) {
        std::cerr << e.what() << std::endl;
    }

    return 0;
}
