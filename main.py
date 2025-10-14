# %%
import docker
client = docker.from_env()
image_name = "selenium/standalone-chrome:latest"
image = client.images.pull(image_name)
client.images.get(image_name)
