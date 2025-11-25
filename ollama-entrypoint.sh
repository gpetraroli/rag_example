#!/bin/sh
set -e

# Start Ollama in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in $(seq 1 90); do
  # Try to list models - if this works, Ollama is ready
  if ollama list > /dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  if [ $i -eq 90 ]; then
    echo "Ollama failed to start in time"
    exit 1
  fi
  sleep 2
done

# Pull models specified in OLLAMA_MODELS environment variable
if [ -n "$OLLAMA_MODELS" ]; then
  echo "Models to pull: $OLLAMA_MODELS"
  INSTALLED_MODELS=$(ollama list 2>/dev/null || echo "")
  
  for model in $OLLAMA_MODELS; do
    model=$(echo "$model" | xargs)  # Trim whitespace
    if [ -z "$model" ]; then
      continue
    fi
    
    echo "Checking for model: $model"
    if echo "$INSTALLED_MODELS" | grep -q "$model"; then
      echo "Model '$model' already exists"
    else
      echo "Pulling model '$model' (this may take a while)..."
      if ollama pull "$model"; then
        echo "Model '$model' pulled successfully!"
      else
        echo "Warning: Failed to pull model '$model'"
      fi
    fi
  done
else
  echo "No models specified in OLLAMA_MODELS environment variable"
fi

# Keep Ollama running in foreground
wait $OLLAMA_PID

