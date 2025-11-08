from sentence_transformers import SentenceTransformer

print("Downloading BGE-M3 model...")
print("This may take a few minutes (approximately 2.27GB)")

model = SentenceTransformer("BAAI/bge-m3")

print("✅ Download complete!")
print(f"Model loaded: {model}")
