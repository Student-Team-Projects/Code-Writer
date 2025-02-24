curl -fsSL https://ollama.com/install.sh | sh
ollama pull codellama
ollama serve &
g++ main.cpp -Iollama/ -o main
