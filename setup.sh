curl -fsSL https://ollama.com/install.sh | sh
ollama serve
g++ main.cpp -Iollama/ -o main