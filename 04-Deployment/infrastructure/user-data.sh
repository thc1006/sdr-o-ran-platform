#!/bin/bash
# SDR-O-RAN Platform - EKS Node User Data Script
# Optimized for Kubernetes 1.33 and 2025 best practices

set -o errexit
set -o nounset
set -o pipefail

# Enable detailed logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting EKS node bootstrap process..."

# System optimizations for 5G RAN workloads
echo "Applying system optimizations..."

# Increase file descriptor limits for high-throughput workloads
cat <<EOF >> /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF

# Kernel parameter tuning for network-intensive workloads
cat <<EOF >> /etc/sysctl.conf
# Network tuning for 5G RAN
net.core.rmem_max = 536870912
net.core.wmem_max = 536870912
net.ipv4.tcp_rmem = 4096 87380 536870912
net.ipv4.tcp_wmem = 4096 65536 536870912
net.core.netdev_max_backlog = 250000
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# Increase connection tracking table size
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 600

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 5

# CPU scheduling
kernel.sched_migration_cost_ns = 5000000
kernel.sched_autogroup_enabled = 0
EOF

sysctl -p

# Configure transparent huge pages for better memory performance
echo "Configuring transparent huge pages..."
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo madvise > /sys/kernel/mm/transparent_hugepage/defrag

# Install additional utilities
echo "Installing additional utilities..."
yum install -y \
    amazon-cloudwatch-agent \
    aws-cfn-bootstrap \
    chrony \
    jq \
    nfs-utils \
    socat \
    sysstat \
    tcpdump \
    wget

# Configure chrony for time synchronization (critical for 5G timing)
echo "Configuring time synchronization..."
systemctl enable chronyd
systemctl start chronyd

# Enable enhanced networking features
echo "Enabling enhanced networking..."
ethtool -K eth0 sg on
ethtool -K eth0 tso on
ethtool -K eth0 gso on

# Configure Docker/containerd optimizations
echo "Configuring container runtime optimizations..."
mkdir -p /etc/containerd
cat <<EOF > /etc/containerd/config.toml
version = 2
[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "runc"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
    runtime_type = "io.containerd.runc.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
      SystemdCgroup = true
[plugins."io.containerd.grpc.v1.cri"]
  [plugins."io.containerd.grpc.v1.cri".registry]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
        endpoint = ["https://registry-1.docker.io"]
EOF

# Bootstrap EKS node
echo "Bootstrapping EKS node..."
/etc/eks/bootstrap.sh '${cluster_name}' \
  --b64-cluster-ca '${cluster_ca}' \
  --apiserver-endpoint '${cluster_endpoint}' \
  --kubelet-extra-args '--node-labels=nodegroup=sdr-oran,workload-type=5g-ran --max-pods=110'

# Install CloudWatch agent
echo "Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm
rm -f ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
cat <<EOF > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
{
  "metrics": {
    "namespace": "SDR-O-RAN/EKS",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"},
          {"name": "cpu_usage_iowait", "rename": "CPU_IOWAIT", "unit": "Percent"}
        ],
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}
        ],
        "resources": ["*"]
      },
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}
        ]
      },
      "net": {
        "measurement": [
          {"name": "bytes_sent", "rename": "NET_OUT", "unit": "Bytes"},
          {"name": "bytes_recv", "rename": "NET_IN", "unit": "Bytes"}
        ],
        "resources": ["eth0"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/eks/${cluster_name}/system",
            "log_stream_name": "{instance_id}/messages"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/eks/${cluster_name}/user-data",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

# Label node with hardware capabilities
echo "Applying node labels..."
INSTANCE_TYPE=$(ec2-metadata --instance-type | cut -d " " -f 2)
AVAILABILITY_ZONE=$(ec2-metadata --availability-zone | cut -d " " -f 2)

# Signal completion
echo "EKS node bootstrap completed successfully!"
echo "Instance Type: $INSTANCE_TYPE"
echo "Availability Zone: $AVAILABILITY_ZONE"
echo "Cluster: ${cluster_name}"

# Send signal to CloudFormation (if used)
/opt/aws/bin/cfn-signal --exit-code $? \
  --stack ${cluster_name} \
  --resource NodeGroup \
  --region $(ec2-metadata --availability-zone | cut -d " " -f 2 | sed 's/[a-z]$//') || true
