#!/bin/bash

# Script to push the Twitter agent code to GitHub repository with a custom commit message
# Repository: https://github.com/zjianyi/kokoro
# Usage: ./push_to_github_custom.sh "Your commit message here"

# Set error handling
set -e

# Check if a commit message was provided
if [ -z "$1" ]; then
    echo "Error: No commit message provided."
    echo "Usage: $0 \"Your commit message here\""
    exit 1
fi

COMMIT_MESSAGE="$1"
echo "Starting GitHub push process with commit message: '$COMMIT_MESSAGE'..."

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
    echo "Adding remote origin..."
    git remote add origin https://github.com/zjianyi/kokoro.git
    echo "Remote origin added."
else
    echo "Remote origin already exists. Updating URL..."
    git remote set-url origin https://github.com/zjianyi/kokoro.git
    echo "Remote URL updated."
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
.env.example

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

# Commit changes with the provided message
echo "Committing changes with message: '$COMMIT_MESSAGE'..."
git commit -m "$COMMIT_MESSAGE"

# Try to pull with rebase before pushing
echo "Pulling latest changes from remote repository..."
if git pull --rebase origin main 2>/dev/null || git pull --rebase origin master 2>/dev/null; then
    echo "Successfully pulled and rebased with remote changes."
else
    echo "No remote branch found or unable to pull. Continuing with push..."
fi

# Push to GitHub with force if needed
echo "Pushing to GitHub repository..."
git push -u origin main || git push -u origin master || git push --force origin main || git push --force origin master

echo "Push completed successfully!"
echo "Repository URL: https://github.com/zjianyi/kokoro" 