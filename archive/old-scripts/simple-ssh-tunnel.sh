#!/bin/bash
# Simple SSH Tunnel Setup for Remote Monitoring
# This script establishes SSH tunnels to home server for monitoring

# Configuration
HOME_SERVER_IP="${HOME_SERVER_IP:-192.168.1.100}"  # Replace with your home IP
HOME_SERVER_USER="${HOME_SERVER_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SSH Tunnel Manager${NC}"

# Function to create tunnel
create_tunnel() {
    local name=$1
    local local_port=$2
    local remote_port=$3
    local host=${4:-$HOME_SERVER_IP}
    
    echo -e "${YELLOW}Creating tunnel: $name (localhost:$local_port -> $host:$remote_port)${NC}"
    
    # Check if tunnel already exists
    if lsof -i:$local_port > /dev/null 2>&1; then
        echo -e "${YELLOW}Port $local_port already in use, skipping $name${NC}"
        return 0
    fi
    
    # Create SSH tunnel in background
    ssh -f -N \
        -L $local_port:localhost:$remote_port \
        -i $SSH_KEY \
        -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3 \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        $HOME_SERVER_USER@$host \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Tunnel $name established on port $local_port${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to create tunnel $name${NC}"
        return 1
    fi
}

# Function to check tunnel health
check_tunnel() {
    local port=$1
    if lsof -i:$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Main tunnel setup
setup_tunnels() {
    echo "Setting up monitoring tunnels..."
    
    # LIMS Exporter tunnel
    create_tunnel "LIMS-Exporter" 9101 9101
    
    # Trading App tunnel (if needed)
    create_tunnel "Trading-App" 9103 8080
    
    # Kubernetes API tunnel (optional, for direct K8s monitoring)
    create_tunnel "K8s-API" 6443 6443
    
    echo -e "${GREEN}All tunnels established!${NC}"
}

# Health check loop
monitor_tunnels() {
    echo "Starting tunnel monitor..."
    while true; do
        sleep 60
        
        # Check each tunnel
        if ! check_tunnel 9101; then
            echo -e "${YELLOW}LIMS tunnel down, restarting...${NC}"
            create_tunnel "LIMS-Exporter" 9101 9101
        fi
        
        if ! check_tunnel 9103; then
            echo -e "${YELLOW}Trading tunnel down, restarting...${NC}"
            create_tunnel "Trading-App" 9103 8080
        fi
    done
}

# Kill existing tunnels (cleanup)
cleanup_tunnels() {
    echo "Cleaning up existing tunnels..."
    for port in 9101 9103 6443; do
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            kill $pid 2>/dev/null
            echo "Killed process on port $port"
        fi
    done
}

# Parse command line arguments
case "$1" in
    start)
        setup_tunnels
        ;;
    stop)
        cleanup_tunnels
        ;;
    restart)
        cleanup_tunnels
        sleep 2
        setup_tunnels
        ;;
    monitor)
        setup_tunnels
        monitor_tunnels
        ;;
    status)
        echo "Tunnel Status:"
        for port in 9101 9103 6443; do
            if check_tunnel $port; then
                echo -e "Port $port: ${GREEN}Active${NC}"
            else
                echo -e "Port $port: ${RED}Inactive${NC}"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|monitor|status}"
        echo ""
        echo "  start   - Start SSH tunnels"
        echo "  stop    - Stop all tunnels"
        echo "  restart - Restart tunnels"
        echo "  monitor - Start tunnels and monitor health"
        echo "  status  - Check tunnel status"
        exit 1
        ;;
esac