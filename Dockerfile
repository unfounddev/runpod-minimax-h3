FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg curl ca-certificates libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && cd ComfyUI && git checkout 3c1b7a17 && pip install -r requirements.txt
RUN git clone https://github.com/pixaroma/ComfyUI-Pixaroma.git /opt/ComfyUI/custom_nodes/ComfyUI-Pixaroma && cd /opt/ComfyUI/custom_nodes/ComfyUI-Pixaroma && git checkout e464839a && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
COPY workflows/Minimax_H3_ref2va.json /opt/template/Minimax_H3_ref2va.json
COPY startup.sh download_models.sh /opt/template/
RUN chmod +x /opt/template/*.sh
EXPOSE 8188
CMD ["/opt/template/startup.sh"]
