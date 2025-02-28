#!/bin/bash

# Script to push the Twitter agent code to GitHub repository using SSH
# Repository: https://github.com/zjianyi/kokoro

# Set error handling
set -e
echo "Starting GitHub push process using SSH..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    echo "Git repository initialized."
else
    echo "Git repository already initialized."
fi

# Check if remote exists, if not add it
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin with SSH..."
    git remote add origin git@github.com:zjianyi/kokoro.git
    echo "Remote origin added."
else
    echo "Remote origin already exists. Updating URL to use SSH..."
    git remote set-url origin git@github.com:zjianyi/kokoro.git
    echo "Remote URL updated."
fi

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "SSH key not found. Would you like to generate one? (y/n)"
    read -r generate_key
    if [ "$generate_key" = "y" ]; then
        echo "Generating SSH key..."
        ssh-keygen -t rsa -b 4096 -C "$(git config user.email)"
        echo "SSH key generated."
        echo "Please add this SSH key to your GitHub account:"
        cat ~/.ssh/id_rsa.pub
        echo "Press Enter after adding the key to GitHub..."
        read -r
    else
        echo "Please set up SSH authentication manually before continuing."
        exit 1
    fi
fi

# Create .gitignore file if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
logs/

# Environment variables
.env

# OS specific files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOL
    echo ".gitignore file created."
fi

# Add all files
echo "Adding files to git..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Twitter agent with crypto insights and automated posting capabilities"

# Test SSH connection
echo "Testing SSH connection to GitHub..."
ssh -T git@github.com || true

# Push to GitHub
echo "Pushing to GitHub repository..."
git push -u origin main || git push -u origin master

echo "Push completed successfully!"
echo "Repository URL: https://github.com/zjianyi/kokoro" 