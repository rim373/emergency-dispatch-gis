#!/bin/bash

# Emergency Response System - PostgreSQL/PostGIS/pgRouting Installation Script
# This script installs and configures PostgreSQL with PostGIS and pgRouting extensions

echo "================================================"
echo "Emergency Response System - Database Installation"
echo "================================================"
echo ""

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install PostgreSQL
echo "📦 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Install PostGIS
echo "🗺️  Installing PostGIS..."
sudo apt install -y postgis postgresql-14-postgis-3

# Install pgRouting
echo "🛣️  Installing pgRouting..."
sudo apt install -y postgresql-14-pgrouting

# Install additional tools
echo "🔧 Installing additional tools..."
sudo apt install -y osm2pgrouting postgresql-14-pgrouting-scripts

# Start PostgreSQL service
echo "🚀 Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check PostgreSQL status
echo ""
echo "✅ Checking PostgreSQL status..."
sudo systemctl status postgresql --no-pager

# Check installed versions
echo ""
echo "📊 Installed versions:"
sudo -u postgres psql -c "SELECT version();"
echo ""
sudo -u postgres psql -c "SELECT PostGIS_version();"

echo ""
echo "================================================"
echo "✅ Installation complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Run: sudo -u postgres psql"
echo "2. Create a password for postgres user: \\password postgres"
echo "3. Run the setup script: bash 2_setup_database.sql"
echo ""
