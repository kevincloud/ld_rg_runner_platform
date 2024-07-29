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
WorkingDirectory=/opt/ld_rg_runner_platform
ExecStart=/usr/bin/python server.py

[Install]
WantedBy=multi-user.target
EOF

# Start Code Server
systemctl enable rg-runner
systemctl start rg-runner