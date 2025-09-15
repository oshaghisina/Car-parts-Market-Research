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

# Add remote origin
echo "🔗 Adding remote origin..."
git remote add origin https://github.com/oshaghisina/Car-parts-Market-Research.git

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin main

echo "✅ Setup complete!"
echo ""
echo "🎉 Your Torob Scraper has been pushed to GitHub!"
echo "Repository: https://github.com/oshaghisina/Car-parts-Market-Research"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com/oshaghisina/Car-parts-Market-Research"
echo "2. Verify all files are uploaded correctly"
echo "3. Set up GitHub Actions secrets (if needed):"
echo "   - PYPI_API_TOKEN (for PyPI publishing)"
echo "   - DOCKER_USERNAME (for Docker Hub)"
echo "   - DOCKER_PASSWORD (for Docker Hub)"
echo "4. Enable GitHub Actions in repository settings"
echo ""
echo "🚀 Your CI/CD pipeline is ready to go!"
