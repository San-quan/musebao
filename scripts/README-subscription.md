# Subscription Processing Script - Usage Guide

## Overview

The `process_subscription.py` script is a utility tool for fetching, parsing, and processing Clash subscription URLs. It helps you:

- Download and decode subscription content (supports gzip and base64 encoding)
- Parse and analyze proxy nodes from Clash YAML configurations
- Display node statistics and details
- Optionally inject UDP support markers for all nodes
- Save processed configurations to files

## Prerequisites

### Python Dependencies

Install required packages:

```bash
pip install pyyaml requests
```

Or use a requirements file:

```bash
# Create requirements.txt
echo "pyyaml>=6.0" > requirements.txt
echo "requests>=2.28.0" >> requirements.txt

# Install dependencies
pip install -r requirements.txt
```

### Python Version

- Python 3.6 or higher recommended

## Usage

### Basic Usage - View Nodes Only

To simply view the nodes from your subscription without saving:

```bash
python3 scripts/process_subscription.py https://your-subscription-url
```

This will:
1. Fetch the subscription from the URL
2. Decode the content (gzip/base64/plain text)
3. Parse the YAML configuration
4. Display node count and details
5. Show UDP support status for each node

### Save Processed Configuration

To save the processed configuration to a file:

```bash
python3 scripts/process_subscription.py https://your-subscription-url -o output.yaml
```

### Inject UDP Support

To inject `udp: true` for all nodes and save:

```bash
python3 scripts/process_subscription.py https://your-subscription-url -o output.yaml --inject-udp
```

This is useful when your subscription doesn't explicitly enable UDP, but you want to ensure all nodes support UDP forwarding.

### Advanced Options

```bash
# Custom timeout (default: 30 seconds)
python3 scripts/process_subscription.py https://your-subscription-url --timeout 60

# Combine all options
python3 scripts/process_subscription.py https://your-subscription-url \
    -o processed_config.yaml \
    --inject-udp \
    --timeout 45
```

## Output Example

When running the script, you'll see output like:

```
正在从 URL 获取订阅: https://your-subscription-url
检测到 base64 编码，已解码

节点总数: 15

节点列表:
------------------------------------------------------------
  1. [vmess   ] 🇨🇳 中国节点-1                    | cn-node1.example.com          :  443 | UDP:✓
  2. [trojan  ] 🇨🇳 中国节点-2                    | cn-node2.example.com          :  443 | UDP:✓
  3. [ss      ] 🇨🇳 中国节点-3                    | cn-node3.example.com          : 8388 | UDP:✗
  ...
------------------------------------------------------------

已为 5 个节点注入 UDP 支持

配置已成功写入: output.yaml

处理完成！
```

## Integration with Clash Configuration

### Using the Subscription in optimized_clash_enhanced.ini

The main configuration file (`optimized_clash_enhanced.ini`) already includes a subscription provider:

```ini
[Proxy Providers]
subscription-return-cn.type = http
subscription-return-cn.url = https://your-subscription-url
subscription-return-cn.path = ./proxies/subscription-return-cn.yaml
subscription-return-cn.interval = 3600
subscription-return-cn.lazy = true
```

### Manual Integration

If you want to manually process and integrate nodes:

1. **Process the subscription:**
   ```bash
   python3 scripts/process_subscription.py https://your-subscription-url \
       -o proxies/processed_nodes.yaml --inject-udp
   ```

2. **Review the output:**
   ```bash
   cat proxies/processed_nodes.yaml
   ```

3. **Update your Clash configuration** to include these nodes in proxy groups

## Automation Tips

### Cron Job for Regular Updates

Update your subscription automatically every 6 hours:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed)
0 */6 * * * /usr/bin/python3 /path/to/scripts/process_subscription.py https://your-subscription-url -o /path/to/proxies/subscription.yaml --inject-udp >> /var/log/clash-update.log 2>&1
```

### Shell Script Wrapper

Create a wrapper script for easier management:

```bash
#!/bin/bash
# update_subscription.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBSCRIPTION_URL="https://your-subscription-url"
OUTPUT_FILE="$SCRIPT_DIR/../proxies/subscription.yaml"

# Create proxies directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/../proxies"

# Run the subscription processor
python3 "$SCRIPT_DIR/process_subscription.py" \
    "$SUBSCRIPTION_URL" \
    -o "$OUTPUT_FILE" \
    --inject-udp \
    --timeout 60

# Check if successful
if [ $? -eq 0 ]; then
    echo "Subscription updated successfully at $(date)"
else
    echo "Failed to update subscription at $(date)" >&2
    exit 1
fi
```

Make it executable:

```bash
chmod +x scripts/update_subscription.sh
```

### Systemd Timer (Linux)

For more robust scheduling on Linux systems:

1. **Create service file** (`/etc/systemd/system/clash-subscription-update.service`):

```ini
[Unit]
Description=Update Clash Subscription
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/musebao
ExecStart=/usr/bin/python3 /path/to/musebao/scripts/process_subscription.py https://your-subscription-url -o /path/to/proxies/subscription.yaml --inject-udp
StandardOutput=journal
StandardError=journal
```

2. **Create timer file** (`/etc/systemd/system/clash-subscription-update.timer`):

```ini
[Unit]
Description=Update Clash Subscription Timer
Requires=clash-subscription-update.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
Unit=clash-subscription-update.service

[Install]
WantedBy=timers.target
```

3. **Enable and start:**

```bash
sudo systemctl enable clash-subscription-update.timer
sudo systemctl start clash-subscription-update.timer
sudo systemctl status clash-subscription-update.timer
```

## Security Considerations

### Protecting Subscription URLs

⚠️ **IMPORTANT**: Subscription URLs often contain tokens or credentials. Never commit them to public repositories!

**Best practices:**

1. **Use environment variables:**
   ```bash
   export CLASH_SUBSCRIPTION_URL="https://your-subscription-url"
   python3 scripts/process_subscription.py "$CLASH_SUBSCRIPTION_URL" -o output.yaml
   ```

2. **Use a separate config file** (add to `.gitignore`):
   ```bash
   # Create config.env (add to .gitignore!)
   echo "SUBSCRIPTION_URL=https://your-subscription-url" > config.env
   
   # Load and use
   source config.env
   python3 scripts/process_subscription.py "$SUBSCRIPTION_URL" -o output.yaml
   ```

3. **Use secrets management tools** (for production):
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Docker secrets

### File Permissions

Ensure sensitive files have proper permissions:

```bash
# Restrict access to configuration files
chmod 600 optimized_clash_enhanced.ini
chmod 600 proxies/*.yaml

# Only owner can read subscription outputs
chmod 700 proxies/
```

## Troubleshooting

### Common Issues

**1. Import Error: Missing Dependencies**
```
错误：缺少必要的依赖库。请运行：pip install pyyaml requests
```
**Solution:** Install required packages as shown in Prerequisites section.

**2. Cannot Decode Subscription**
```
错误：无法解码订阅数据
```
**Solution:** The subscription might be using an unsupported encoding. Check with your provider.

**3. Invalid YAML Format**
```
错误：无法解析 YAML 配置
```
**Solution:** The subscription might be malformed. Try viewing the raw content to diagnose.

**4. Timeout Error**
```
错误：无法获取订阅内容 - ReadTimeout
```
**Solution:** Increase timeout: `--timeout 60` or check your network connection.

### Debug Mode

For detailed debugging, you can modify the script to add verbose output or use Python's logging module.

## Next Steps

1. **Test the script** with your subscription URL
2. **Set up automation** using one of the methods above
3. **Monitor updates** to ensure subscriptions are refreshed regularly
4. **Review security** settings and ensure tokens are protected
5. **Integrate with Clash** and test connectivity

## Support

For issues or questions:
- Check the script's help: `python3 scripts/process_subscription.py --help`
- Review error messages carefully
- Ensure all dependencies are installed
- Verify network connectivity

## License

This script is part of the musebao project. Please refer to the main repository license.
