#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# Set up access to Carbynestacks Github Packages
mkdir -p "$HOME"/.m2
echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" \
  "<settings xmlns=\"http://maven.apache.org/SETTINGS/1.2.0\"\n" \
  "          xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n" \
  "          xsi:schemaLocation=\"http://maven.apache.org/SETTINGS/1.2.0 http://maven.apache.org/xsd/settings-1.2.0.xsd\">\n" \
  "  <servers>\n" \
  "    <server>\n" \
  "      <id>github</id>\n" \
  "      <username>$GITHUB_USERNAME</username>\n" \
  "      <password>$CALIPER_PAT</password>\n" \
  "    </server>\n" \
  "  </servers>\n" \
  "</settings>" >"$HOME"/.m2/settings.xml

# Configure HashiCorp GPG key and repository
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --no-tty --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list >/dev/null

# Configure Kubectl GPG key and repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --no-tty --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg >/dev/null
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list >/dev/null

# Install NodeSource PPA
curl -s https://deb.nodesource.com/setup_18.x | sudo bash >/dev/null

# Update repositories and install required packages
sudo apt-get update >/dev/null
sudo apt-get install -y openjdk-8-jdk nodejs terraform kubectl python3-pip jq zip >/dev/null

# Install Azure-CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash >/dev/null

# Install cdktf
sudo npm install --global cdktf-cli@0.16.3 >/dev/null

# Authenticate Terraform to Azure
az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_T_ID" --output none

# Temporär
git clone https://"$CALIPER_PRIVATE_REPOS_PAT"@github.com/juliangrewe-bosch/carbynestack.git "$HOME/carbynestack"
git -C "$HOME/carbynestack" checkout -b cdktf-caliper origin/cdktf-caliper

# Download Prometheus Operator bundle
LATEST=$(curl -s https://api.github.com/repos/prometheus-operator/prometheus-operator/releases/latest | jq -cr .tag_name)
curl -o "$HOME"/carbynestack/deployments/manifests/prometheus-operator-bundle.yaml -sL https://github.com/prometheus-operator/prometheus-operator/releases/download/"${LATEST}"/bundle.yaml

# Install dependencies and synthesize infrastructure using cdktf
cd "$HOME"/carbynestack/deployments || exit 1

npm install >/dev/null
cdktf get >/dev/null
cdktf synth >/dev/null

# Initialize and apply Terraform
export TF_VAR_azureSubscriptionID=$AZURE_SUBSCRIPTION_ID
terraform -chdir=cdktf.out/stacks/private-aks-virtual-cloud/ init -input=false >/dev/null
terraform -chdir=cdktf.out/stacks/private-aks-virtual-cloud/ apply -auto-approve -input=false >/dev/null

# Get access credentials for private aks cluster
az aks get-credentials --name apollo-private --resource-group caliper-rg
az aks get-credentials --name starbuck-private --resource-group caliper-rg

# Run load-tests
cd "$HOME"/caliper || exit 1

export STARBUCK_FQDN=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}').sslip.io
kubectl config use-context apollo-private
export APOLLO_FQDN=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}').sslip.io

kubectl patch tuplegenerationscheduler cs-klyshko-tuplegenerationscheduler -p "{\"spec\":{\"threshold\":$TUPLE_THRESHOLD, \"concurrency\": 10}}" --type=merge
timeout=7200 # 2 hours
while true; do
  tuples_available=$(curl -s http://"$APOLLO_FQDN"/castor/intra-vcp/telemetry | jq '.metrics[] | select(.type == "INPUT_MASK_GFP") | .available')

  if [[ $tuples_available -ge $TUPLE_THRESHOLD ]]; then
    break
  fi

  if [[ $SECONDS -ge $timeout ]]; then
    break
  fi

  sleep 300
done

chmod +x mvnw
./mvnw -q gatling:test

# Generate cAdvisor and gatling charts
cd "$HOME"/caliper/scripts/python || exit 1

export PROMETHEUS_SERVER_PORT=32767
export APOLLO_NODE_IP=$(kubectl get node -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
kubectl config use-context starbuck-private
export STARBUCK_NODE_IP=$(kubectl get node -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

pip3 install -r requirements.txt >/dev/null
python3 generate_cAdvisor_charts.py
python3 generate_gatling_response_times_files.py
python3 generate_cAdvisor_report_files.py
