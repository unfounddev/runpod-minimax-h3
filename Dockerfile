# The PyTorch image tag and upstream dependency compatibility are verified by GitHub Actions build, not assumed.
FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg curl ca-certificates libgl1 libglib2.0-0 python3-venv \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv --system-site-packages /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /opt
RUN git clone https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && cd /opt/ComfyUI \
    && git checkout 3c1b7a17 \
    && python -m pip install -r requirements.txt -r manager_requirements.txt
COPY patch_comfy_proxy.py /opt/template/patch_comfy_proxy.py
RUN python /opt/template/patch_comfy_proxy.py /opt/ComfyUI
COPY custom_nodes/framekit_h3 /opt/ComfyUI/custom_nodes/framekit_h3
RUN mkdir -p /opt/template
COPY startup.sh download_models.sh /opt/template/
RUN sed -i 's/\r$//' /opt/template/startup.sh /opt/template/download_models.sh
COPY services.py /opt/template/services.py
COPY install_filebrowser.py /opt/template/install_filebrowser.py
RUN python /opt/template/install_filebrowser.py
ENV FILE_BROWSER_USERNAME=admin FILE_BROWSER_PASSWORD=adminadmin12
COPY tests/smoke_browser.py /opt/template/smoke_browser.py
RUN bash -n /opt/template/startup.sh && python /opt/template/smoke_browser.py /opt/template/services.py
COPY tests/smoke_nodes.py /opt/template/smoke_nodes.py
COPY tests/smoke_proxy.py /opt/template/smoke_proxy.py
RUN python /opt/template/smoke_proxy.py /opt/ComfyUI
RUN chmod +x /opt/template/startup.sh /opt/template/download_models.sh
RUN python /opt/template/smoke_nodes.py --comfy /opt/ComfyUI --pack /opt/ComfyUI/custom_nodes/framekit_h3
COPY tests/smoke_startup.py /opt/template/smoke_startup.py
RUN python /opt/template/smoke_startup.py /opt/ComfyUI
EXPOSE 8188 8080
CMD ["python", "/opt/template/services.py"]
# The PyTorch image tag and upstream dependency compatibility are verified by GitHub Actions build, not assumed.
FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg curl ca-certificates libgl1 libglib2.0-0 python3-venv \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv --system-site-packages /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /opt
RUN git clone https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && cd /opt/ComfyUI \
    && git checkout 3c1b7a17 \
    && python -m pip install -r requirements.txt -r manager_requirements.txt
COPY patch_comfy_proxy.py /opt/template/patch_comfy_proxy.py
RUN python /opt/template/patch_comfy_proxy.py /opt/ComfyUI
COPY custom_nodes/nexus_h3 /opt/ComfyUI/custom_nodes/nexus_h3
RUN mkdir -p /opt/template
COPY startup.sh download_models.sh /opt/template/
RUN sed -i 's/\r$//' /opt/template/startup.sh /opt/template/download_models.sh
COPY services.py /opt/template/services.py
RUN python -m pip install copyparty==1.20.25
COPY tests/smoke_browser.py /opt/template/smoke_browser.py
RUN bash -n /opt/template/startup.sh && python /opt/template/smoke_browser.py /opt/template/services.py
COPY tests/smoke_nodes.py /opt/template/smoke_nodes.py
COPY tests/smoke_proxy.py /opt/template/smoke_proxy.py
RUN python /opt/template/smoke_proxy.py /opt/ComfyUI
RUN chmod +x /opt/template/startup.sh /opt/template/download_models.sh
RUN python /opt/template/smoke_nodes.py --comfy /opt/ComfyUI --pack /opt/ComfyUI/custom_nodes/nexus_h3
COPY tests/smoke_startup.py /opt/template/smoke_startup.py
RUN python /opt/template/smoke_startup.py /opt/ComfyUI
EXPOSE 8188 8080
CMD ["python", "/opt/template/services.py"]
