import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Prepare the original BGE-M3 encoder for live queries")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    model_path = root / ".local/models/bge-m3"
    if args.download:
        from huggingface_hub import HfApi, snapshot_download
        available = HfApi().list_repo_files("BAAI/bge-m3")
        weights = "model.safetensors" if "model.safetensors" in available else "pytorch_model.bin"
        snapshot_download("BAAI/bge-m3", local_dir=str(model_path),
                          allow_patterns=["*.json", "*.txt", "sentencepiece.bpe.model", weights, "1_Pooling/*"],
                          ignore_patterns=["onnx/*", "imgs/*", "colbert_linear.pt", "sparse_linear.pt"])
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(str(model_path), device="cpu", local_files_only=True)
    vectors = model.encode(["고객의 반복 문의 처리 부담"], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    if vectors.shape != (1, 1024):
        raise RuntimeError("Expected the frozen BGE-M3 1024-dimensional encoder")
    print("BGE-M3 local encoder ready (1024d). No API key used.")


if __name__ == "__main__":
    main()
