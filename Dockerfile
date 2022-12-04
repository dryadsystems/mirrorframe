FROM appropriate/curl as model
RUN curl -o stable-hf-cache.tar https://r2-public-worker.drysys.workers.dev/hf-cache-ait-verdant-2022-11-30.tar
RUN tar -xf stable-hf-cache.tar -C /
RUN find /root/.cache

FROM appropriate/curl as ait
RUN curl -o ait-verdant.tar https://r2-public-worker.drysys.workers.dev/ait-verdant-2022-11-30.tar
RUN mkdir /workdir
RUN tar -xf ait-verdant.tar -C /workdir

FROM python:3.10 as libbuilder
WORKDIR /app
RUN pip install poetry git+https://github.com/python-poetry/poetry.git git+https://github.com/python-poetry/poetry-core.git
RUN python3.10 -m venv /app/venv 
WORKDIR /app/
COPY ./pyproject.toml /app/
RUN VIRTUAL_ENV=/app/venv poetry install 

FROM python:3.10
WORKDIR /app
COPY --from=ait /workdir/tmp /app/tmp
COPY --from=model /root/.cache /root/.cache
COPY --from=libbuilder /app/venv/lib/python3.10/site-packages /app/
COPY ./modeling/ /app/modeling
COPY ./pipeline_stable_diffusion_ait.py ./client.js ./server.js /app/
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/python3.10", "/app/server.py"]
