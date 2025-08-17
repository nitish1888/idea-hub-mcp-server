FROM registry.access.redhat.com/ubi9/python-312:9.5-1739191330

USER root

# Copy certificates
COPY ./aws-global-bundle.pem ./2022-IT-Root-CA.pem /usr/share/pki/ca-trust-source/anchors/
RUN update-ca-trust

USER default

WORKDIR /opt/app-root/src/

ENV VENV_PATH=/opt/app-root/src/.venv

# Install system dependencies needed for ML packages
USER root
RUN dnf install -y gcc gcc-c++ make libpq-devel && \
    dnf clean all

USER default

# Create virtual environment and install dependencies
RUN python3 -m venv $VENV_PATH && \
    $VENV_PATH/bin/pip install --upgrade pip setuptools wheel

# Copy requirements and install CPU-only PyTorch first (like main Idea Hub)
COPY ./requirements.txt ./
RUN $VENV_PATH/bin/pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt

# Create cache directories with proper permissions
USER root
RUN mkdir -p ./.cache/huggingface ./.cache/torch && \
    chgrp -R 0 ./.cache/huggingface ./.cache/torch && \
    chmod -R g=u ./.cache/huggingface ./.cache/torch && \
    chown -R default:0 ./.cache

USER default

# Pre-download HuggingFace embedding model during build
ENV HF_HOME=/opt/app-root/src/.cache/huggingface
ENV TRANSFORMERS_CACHE=/opt/app-root/src/.cache/huggingface

# Download model with internet access first (same as main Idea Hub)
RUN $VENV_PATH/bin/python -c "\
from transformers import AutoTokenizer, AutoModel; \
import sentence_transformers; \
print('🔄 Pre-downloading all-MiniLM-L6-v2 embedding model...'); \
model = sentence_transformers.SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
print('✅ Model downloaded successfully'); \
print('📁 Model cached at:', model.cache_folder if hasattr(model, 'cache_folder') else 'default location')" || echo "⚠️ Model download failed, will try at runtime"

# Set environment for runtime to prefer offline mode but allow fallback
ENV HF_HUB_OFFLINE=0
ENV TRANSFORMERS_OFFLINE=0

# Copy application code
COPY ./src ./src

# Set virtual env path and Python path
ENV PATH="$VENV_PATH/bin:$PATH"
ENV PYTHONPATH=/opt/app-root/src

# Expose both MCP and Web server ports
EXPOSE 8443 8000

# Start the web server (simpler than dual mode for now)
CMD ["/opt/app-root/src/.venv/bin/python", "src/web_server.py"]
