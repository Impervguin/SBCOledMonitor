#!/bin/bash
set -e  # Exit on error

# ============================================
# CONFIGURATION
# ============================================
APP_NAME="oled-monitor"
APP_USER="oled-monitor"
APP_GROUP="oled-monitor"
INSTALL_DIR="/usr/local/$APP_NAME"
CONFIG_DIR="/etc/$APP_NAME"
SERVICE_NAME="oled-monitor"
LOG_DIR="/var/log/$APP_NAME"
DATA_DIR="/var/lib/$APP_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# HELPER FUNCTIONS
# ============================================
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# ============================================
# PRECHECK
# ============================================
print_info "Starting installation of $APP_NAME..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (sudo ./install.sh)"
   exit 1
fi

# Check required commands
check_command "python3"
check_command "pip3"
check_command "systemctl"

# ============================================
# CREATE SYSTEM USER AND GROUPS
# ============================================
print_info "Creating system user and groups..."

# Create group if not exists
if ! getent group "$APP_GROUP" &>/dev/null; then
    groupadd -r "$APP_GROUP"
    print_success "Created group: $APP_GROUP"
else
    print_info "Group $APP_GROUP already exists"
fi

# Create user if not exists
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -g "$APP_GROUP" -s /bin/false -d "$INSTALL_DIR" "$APP_USER"
    print_success "Created system user: $APP_USER"
else
    print_info "User $APP_USER already exists"
fi

# ============================================
# SETUP I2C ACCESS
# ============================================
print_info "Setting up I2C access..."

# Check if i2c group exists
if ! getent group i2c &>/dev/null; then
    groupadd i2c
    print_success "Created group: i2c"
else
    print_info "Group i2c already exists"
fi

# Add user to i2c group
usermod -a -G i2c "$APP_USER"
print_success "Added $APP_USER to i2c group"

# ============================================
# CREATE DIRECTORIES
# ============================================
print_info "Creating directories..."

# Application directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Set permissions
chown -R "$APP_USER:$APP_GROUP" "$INSTALL_DIR"
chown -R "$APP_USER:$APP_GROUP" "$CONFIG_DIR"
chown -R "$APP_USER:$APP_GROUP" "$LOG_DIR"
chown -R "$APP_USER:$APP_GROUP" "$DATA_DIR"

print_success "Created directories:"
echo "  - $INSTALL_DIR (application)"
echo "  - $CONFIG_DIR (configuration)"
echo "  - $LOG_DIR (logs)"
echo "  - $DATA_DIR (data)"

# ============================================
# COPY APPLICATION FILES
# ============================================
print_info "Copying application files..."

# Copy source code
cp -r ./src/* "$INSTALL_DIR/"
cp ./requirements.txt "$INSTALL_DIR/"

# Set ownership of application files
chown -R "$APP_USER:$APP_GROUP" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"

print_success "Copied application files to $INSTALL_DIR"

# ============================================
# SETUP PYTHON VIRTUAL ENVIRONMENT
# ============================================
print_info "Setting up Python virtual environment..."

# Create venv
python3 -m venv "$INSTALL_DIR/venv"
chown -R "$APP_USER:$APP_GROUP" "$INSTALL_DIR/venv"

# Install dependencies
print_info "Installing Python dependencies..."
sudo -u "$APP_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

print_success "Virtual environment created and dependencies installed"

# ============================================
# SETUP CONFIGURATION
# ============================================
print_info "Setting up configuration..."

CONFIG_FILE="$CONFIG_DIR/config.yaml"
TEMPLATE_FILE="./config/config.yaml.template"

if [ ! -f "$CONFIG_FILE" ]; then
    if [ -f "$TEMPLATE_FILE" ]; then
        # Replace template variables
        sed -e "s/{{APP_NAME}}/$APP_NAME/g" \
            -e "s|{{DATA_DIR}}|$DATA_DIR|g" \
            -e "s|{{LOG_DIR}}|$LOG_DIR|g" \
            "$TEMPLATE_FILE" > "$CONFIG_FILE"
        
        chown "$APP_USER:$APP_GROUP" "$CONFIG_FILE"
        chmod 640 "$CONFIG_FILE"
        print_success "Created configuration from template: $CONFIG_FILE"
    else
        print_error "Template file not found: $TEMPLATE_FILE"
    fi
else
    print_warning "Configuration already exists, keeping it: $CONFIG_FILE"
fi

# ============================================
# SETUP ENVIRONMENT FILE (for secrets)
# ============================================
ENV_FILE="$CONFIG_DIR/.env"
touch $ENV_FILE
print_info "Created $ENV_FILE"

# ============================================
# SETUP SYSTEMD SERVICE
# ============================================
print_info "Setting up systemd service..."

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
TEMPLATE_SERVICE="./systemd/$SERVICE_NAME.service.template"

if [ -f "$TEMPLATE_SERVICE" ]; then
    # Replace template variables
    sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" \
        -e "s|{{APP_USER}}|$APP_USER|g" \
        -e "s|{{APP_GROUP}}|$APP_GROUP|g" \
        -e "s|{{CONFIG_DIR}}|$CONFIG_DIR|g" \
        -e "s|{{LOG_DIR}}|$LOG_DIR|g" \
        -e "s|{{DATA_DIR}}|$DATA_DIR|g" \
        "$TEMPLATE_SERVICE" > "$SERVICE_FILE"
    
    print_success "Created systemd service from template: $SERVICE_FILE"
else
    print_errot "Template not found: $TEMPLATE_SERVICE"
fi

# Set permissions
chmod 644 "$SERVICE_FILE"

# ============================================
# ENABLE AND START SERVICE
# ============================================
print_info "Configuring systemd service..."

# Reload systemd
systemctl daemon-reload
print_success "Reloaded systemd"

# Enable service (start at boot)
systemctl enable "$SERVICE_NAME"
print_success "Enabled service: $SERVICE_NAME"

# Start service
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_info "Service is already running, restarting..."
    systemctl restart "$SERVICE_NAME"
else
    systemctl start "$SERVICE_NAME"
fi
print_success "Started service: $SERVICE_NAME"

# ============================================
# FINAL CHECKS
# ============================================
print_info "Checking service status..."
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_success "Service is running"
    systemctl status "$SERVICE_NAME" --no-pager
else
    print_error "Service failed to start. Check logs:"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi

# ============================================
# POST-INSTALLATION SUMMARY
# ============================================
echo ""
echo "============================================"
print_success "Installation completed successfully!"
echo "============================================"
echo ""
echo "📁 Installation details:"
echo "  Application: $INSTALL_DIR"
echo "  Configuration: $CONFIG_DIR/config.yaml"
echo "  Environment: $CONFIG_DIR/.env"
echo "  Logs: $LOG_DIR/"
echo "  Data: $DATA_DIR/"
echo ""
echo "🔧 Service management:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "📝 Configuration:"
echo "  Edit config:    sudo nano $CONFIG_DIR/config.yaml"
echo "  Edit env:       sudo nano $CONFIG_DIR/.env"
echo "  Restart after:  sudo systemctl restart $SERVICE_NAME"
echo ""
echo "🖥️  I2C access:"
echo "  User $APP_USER is in group 'i2c'"
echo "  Test: sudo -u $APP_USER i2cdetect -y 1"
echo ""
echo "============================================"