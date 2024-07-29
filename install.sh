#!/bin/bash

cd /opt

git clone https://github.com/kevincloud/ld_rg_runner_platform.git

cd ld_rg_runner_platform

pip install -r requirements-server.txt --break-system-packages

cat > /etc/systemd/system/rg-runner.service <<-EOF
[Unit]
Description=Release Guardian Runner
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=root
WorkingDirectory=/
ExecStart=/usr/bin/python --host 0.0.0.0 --port 8080 --auth none /opt/dotnet/

[Install]
WantedBy=multi-user.target
EOF

# Start Code Server
systemctl enable code-server
systemctl start code-server