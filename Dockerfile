FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends git git-lfs ffmpeg curl ca-certificates libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && cd ComfyUI && git checkout 3c1b7a17 && pip install -r requirements.txt
RUN mkdir -p /opt/ComfyUI/custom_nodes && cd /opt/ComfyUI/custom_nodes && \
 git clone https://github.com/pixaroma/ComfyUI-Pixaroma.git && cd ComfyUI-Pixaroma && git checkout e464839a && cd .. && \
 git clone https://github.com/kijai/ComfyUI-KJNodes.git && cd ComfyUI-KJNodes && git checkout a325041 && cd .. && \
 git clone https://github.com/ltdrdata/ComfyUI-Manager.git && cd ComfyUI-Manager && git checkout 7a978c9 && cd .. && \
 git clone https://github.com/MoonGoblinDev/Civicomfy.git && cd Civicomfy && git checkout e6df468 && cd .. && \
 git clone https://github.com/MadiatorLabs/ComfyUI-RunpodDirect.git && cd ComfyUI-RunpodDirect && git checkout 2411e9a
RUN set -e; for d in /opt/ComfyUI/custom_nodes/*; do if [ -f "$d/requirements.txt" ]; then pip install -r "$d/requirements.txt"; fi; done
COPY workflows/Minimax_H3_ref2va.json /opt/ComfyUI/user/default/workflows/Minimax_H3_ref2va.json
COPY startup.sh download_models.sh /opt/
RUN chmod +x /opt/startup.sh /opt/download_models.sh
EXPOSE 8188
CMD ["/opt/startup.sh"]
