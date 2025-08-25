#!/bin/bash
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama server to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama server..."
    sleep 2
done

echo "Ollama server is ready. Pulling models..."

echo "Pulling nomic-embed-text..."
ollama pull nomic-embed-text

echo "Pulling llama3.2:3b-instruct-q4_0..."
ollama pull llama3.2:3b-instruct-q4_0

echo "Pulling mistral:7b-instruct-q4_0..."
ollama pull mistral:7b-instruct-q4_0

echo "All models pulled successfully. Ollama is ready!"

# Wait for the Ollama server process
wait $OLLAMA_PID