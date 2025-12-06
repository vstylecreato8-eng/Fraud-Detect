#!/bin/bash
set -e

echo "Cleaning up old model files..."
rm -f /app/model/Credit.pickle
rm -f /app/model/*.model
rm -f /app/model/*.pkl

echo "Installing Git LFS..."
apt-get update
apt-get install -y git-lfs

echo "Pulling LFS files..."
git lfs pull

echo "Verifying compressed model file..."
ls -lh /app/model/Credit.pickle.gz

echo "Build complete!"
echo "Git LFS setup complete"
