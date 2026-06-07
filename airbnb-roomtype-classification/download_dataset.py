import kagglehub

# Download latest version
path = kagglehub.dataset_download("vrindakallu/new-york-dataset")

print("Path to dataset files:", path)