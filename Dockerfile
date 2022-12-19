# from https://github.com/vercel/next.js/blob/canary/examples/with-docker/Dockerfile
# Install dependencies only when needed
FROM node:16-alpine AS jsdeps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies 
COPY mirror/package.json mirror/package-lock.json ./
RUN npm ci;

# Rebuild the source code only when needed
FROM node:16-alpine AS next
WORKDIR /app
COPY --from=jsdeps /app/node_modules ./node_modules/
COPY ./mirror /app/


# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run export

#####################################################

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
COPY --from=next /app/out /app/next
COPY ./modeling/ /app/modeling
COPY ./pipeline_stable_diffusion_ait.py ./client.js ./index.html ./ws-only.html ./server.py /app/
ENV DISABLE_TELEMETRY=YES
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/python3.10", "/app/server.py"]
