#!/bin/bash

# GitHub Repository Setup Script for Torob Scraper
# This script helps set up a new GitHub repository with all necessary files

set -e

echo "🚀 Setting up GitHub repository for Torob Scraper..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to Git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Torob Scraper v1.0.0

- Advanced automotive parts price scraper
- Modern web interface with real-time logging
- Parallel processing and intelligent caching
- Comprehensive Excel export with analytics
- Docker support and CI/CD pipeline
- Production-ready with extensive documentation"

# Create main branch
echo "🌿 Creating main branch..."
git branch -M main

# Add remote origin (user needs to create repo first)
echo "🔗 Adding remote origin..."
echo "Please create a new repository on GitHub first, then run:"
echo "git remote add origin https://github.com/YOUR_USERNAME/torob-scraper.git"
echo "git push -u origin main"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub: https://github.com/new"
echo "2. Name it 'torob-scraper'"
echo "3. Don't initialize with README, .gitignore, or license (we have them)"
echo "4. Run the commands shown above to push to GitHub"
echo "5. Set up GitHub Actions secrets:"
echo "   - PYPI_API_TOKEN (for PyPI publishing)"
echo "   - DOCKER_USERNAME (for Docker Hub)"
echo "   - DOCKER_PASSWORD (for Docker Hub)"
echo ""
echo "🎉 Your Torob Scraper is ready for GitHub!"
