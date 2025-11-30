#!/bin/bash

echo "🔍 Emergency Response System - Installation Verification"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -n "Checking Python 3.8+... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
fi

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | cut -d' ' -f3)
    echo -e "${GREEN}✓ Found PostgreSQL $PG_VERSION${NC}"
else
    echo -e "${RED}✗ PostgreSQL not found${NC}"
fi

# Check MongoDB
echo -n "Checking MongoDB... "
if command -v mongod &> /dev/null; then
    MONGO_VERSION=$(mongod --version | grep "db version" | cut -d' ' -f3)
    echo -e "${GREEN}✓ Found MongoDB $MONGO_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ MongoDB not found (optional for basic functionality)${NC}"
fi

# Check PostGIS
echo -n "Checking PostGIS... "
if sudo -u postgres psql -c "SELECT PostGIS_version();" &> /dev/null; then
    echo -e "${GREEN}✓ PostGIS installed${NC}"
else
    echo -e "${RED}✗ PostGIS not installed${NC}"
fi

# Check project structure
echo ""
echo "Checking project structure..."
DIRS=("1_ARCGIS_PRO" "2_DATABASE" "3_BACKEND" "4_FRONTEND" "5_DOCS" "6_SCRIPTS")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir"
    else
        echo -e "  ${RED}✗${NC} $dir"
    fi
done

# Check key files
echo ""
echo "Checking key files..."
FILES=(
    "README.md"
    "2_DATABASE/postgis/4_create_tables.sql"
    "3_BACKEND/app/main.py"
    "3_BACKEND/requirements.txt"
    "4_FRONTEND/user/index.html"
)
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file"
    fi
done

echo ""
echo "=========================================================="
echo "Verification complete!"
echo ""
echo "Next steps:"
echo "1. Read README.md for full documentation"
echo "2. Follow 5_DOCS/QUICK_START.md for 15-minute setup"
echo "3. Run database setup scripts in 2_DATABASE/"
echo ""
