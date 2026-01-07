from CodeWriter.core.solver import Solver

if __name__ == "__main__":
    # path = input("Enter the path of file: ")
    path = "resources/prime-reduction"
    solver = Solver(path)
    tries = 0
    while tries < solver.timeout:

        if tries == 0:
            result = solver.begin_chat()
        else:
            result = solver.continue_chat()
        public = solver.validate_public()
        secret = solver.validate_secret()
        if public and secret:
            exit(0)
        tries += 1
    exit(1)



