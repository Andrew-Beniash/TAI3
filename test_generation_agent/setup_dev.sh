#!/bin/bash

echo "Setting up development environment for Test Generation Agent..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
else
  echo "Virtual environment already exists."
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Creating .env file from example..."
  cp .env.example .env
  echo "Please update the .env file with your configuration."
else
  echo ".env file already exists."
fi

# Create directories if they don't exist
echo "Creating necessary directories..."
mkdir -p checkpoints

echo ""
echo "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your configuration"
echo "2. Start the application with: python launch.py"
echo "3. Test the webhook with: python tests/test_webhook.py"
echo ""
echo "Happy coding!"
