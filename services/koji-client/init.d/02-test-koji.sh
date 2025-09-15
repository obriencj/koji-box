#!/bin/bash


echo "Configuring Koji client..."
mkdir -p ~/.koji
echo << EOF > ~/.koji/config
[koji]
username = friend

[koji-admin]
username = superfriend
EOF

echo "PATH=./bin:$PATH" >> ~/.bashrc
ln -s `which koji` ~/.local/bin/koji-admin


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
    ~/.local/bin/koji-admin list-hosts || echo "Could not list hosts (may need authentication)"

else
    echo "✗ koji command is not available"
    exit 1
fi

echo "Koji client test complete"

# The end.
