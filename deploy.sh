#!/bin/bash

# ForBill GitHub & Railway Deployment Script
# This script helps you set up GitHub repository and deploy to Railway

set -e  # Exit on error

echo "🚀 ForBill Deployment Setup"
echo "============================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

print_success "Git is installed"

# Check current directory
if [ ! -f "app/main.py" ]; then
    print_error "Please run this script from the ForBill AI root directory"
    exit 1
fi

print_success "Running from correct directory"

# Get GitHub username
echo ""
print_info "Enter your GitHub username:"
read -p "> " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    print_error "GitHub username is required"
    exit 1
fi

# Get repository name
echo ""
print_info "Enter repository name (default: forbill-ai):"
read -p "> " REPO_NAME
REPO_NAME=${REPO_NAME:-forbill-ai}

# Confirm
echo ""
echo "Repository will be created at:"
echo "https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Check for uncommitted changes
echo ""
print_info "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes. Committing them now..."
    git add -A
    git commit -m "chore: prepare for deployment"
    print_success "Changes committed"
else
    print_success "No uncommitted changes"
fi

# Ensure we're on main branch
echo ""
print_info "Ensuring main branch exists..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    if git show-ref --verify --quiet refs/heads/main; then
        git checkout main
    else
        git branch -M main
    fi
    print_success "Switched to main branch"
fi

# Check if remote already exists
echo ""
print_info "Checking for existing remote..."
if git remote | grep -q "origin"; then
    print_warning "Remote 'origin' already exists"
    EXISTING_REMOTE=$(git remote get-url origin)
    echo "Current remote: $EXISTING_REMOTE"
    read -p "Remove and replace with new remote? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
        print_success "Removed existing remote"
    else
        print_warning "Keeping existing remote. Skipping GitHub setup."
        SKIP_GITHUB=true
    fi
fi

if [ "$SKIP_GITHUB" != "true" ]; then
    # Add GitHub remote
    echo ""
    print_info "Adding GitHub remote..."
    GITHUB_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    git remote add origin $GITHUB_URL
    print_success "GitHub remote added: $GITHUB_URL"

    # Push to GitHub
    echo ""
    print_info "Pushing to GitHub..."
    echo "You may be prompted for GitHub credentials..."
    
    if git push -u origin main; then
        print_success "Code pushed to GitHub successfully!"
    else
        print_error "Failed to push to GitHub"
        echo ""
        echo "Please create the repository manually:"
        echo "1. Go to https://github.com/new"
        echo "2. Repository name: $REPO_NAME"
        echo "3. Choose Public or Private"
        echo "4. DO NOT initialize with README"
        echo "5. Click 'Create repository'"
        echo "6. Then run: git push -u origin main"
        exit 1
    fi
fi

# Print next steps
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "GitHub Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔗 Repository URL:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. DEPLOY TO RAILWAY"
echo "   • Go to https://railway.app"
echo "   • Click 'New Project' → 'Deploy from GitHub repo'"
echo "   • Select your $REPO_NAME repository"
echo "   • Railway will auto-detect configuration"
echo ""
echo "2. ADD DATABASE"
echo "   • In Railway dashboard, click 'New' → 'PostgreSQL'"
echo "   • DATABASE_URL will be auto-configured"
echo ""
echo "3. ADD ENVIRONMENT VARIABLES"
echo "   • Go to Variables tab in Railway"
echo "   • Add all variables from .env file:"
echo "     - WHATSAPP_TOKEN"
echo "     - WHATSAPP_PHONE_NUMBER_ID"
echo "     - WHATSAPP_VERIFY_TOKEN"
echo "     - PAYRANT_SECRET_KEY"
echo "     - PAYRANT_PUBLIC_KEY"
echo "     - TOPUPMATE_API_KEY"
echo "     - TOPUPMATE_PUBLIC_KEY"
echo "     - SECRET_KEY"
echo ""
echo "4. RUN MIGRATIONS"
echo "   • In Railway, go to Settings → Deploy Command"
echo "   • Or run: railway run alembic upgrade head"
echo ""
echo "5. CONFIGURE WEBHOOKS"
echo "   • WhatsApp: https://your-app.railway.app/webhooks/whatsapp"
echo "   • Payrant: https://your-app.railway.app/webhooks/payrant"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Ask about Railway deployment
echo ""
read -p "Do you want to install Railway CLI now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v npm &> /dev/null; then
        print_info "Installing Railway CLI..."
        npm install -g @railway/cli
        print_success "Railway CLI installed!"
        echo ""
        print_info "To deploy, run these commands:"
        echo "  1. railway login"
        echo "  2. railway init"
        echo "  3. railway up"
    else
        print_warning "npm not found. Install Node.js first: https://nodejs.org"
    fi
fi

echo ""
print_success "Setup complete! 🎉"
echo ""
