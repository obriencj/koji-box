#!/bin/bash


echo "Configuring Koji client..."
mkdir -p $HOME/.koji
cat << EOF > $HOME/.koji/config
[koji]
username = friend
EOF
sed 's,\[koji],[koji-admin]\nusername = superfriend,g' /etc/koji.conf >> $HOME/.koji/config


mkdir -p $HOME/.local/bin
echo "PATH=$HOME/.local/bin:$PATH" >> $HOME/.bashrc
chmod +x $HOME/.bashrc
ln -s `which koji` $HOME/.local/bin/koji-admin


# Test Koji client functionality
echo "Testing Koji client functionality..."

# Test koji command availability
if command -v koji >/dev/null 2>&1; then
    echo "✓ koji command is available"

    # Test koji version
    echo "Koji version:"
    koji version || echo "Could not get koji version"

    # Test koji list-hosts (if authenticated)
    echo "Testing koji-admin list-hosts:"
    $HOME/.local/bin/koji-admin list-hosts || echo "Could not list hosts (may need authentication)"

else
    echo "✗ koji command is not available"
    exit 1
fi

echo "Koji client test complete"

# The end.
