#-----------------
# {meta}lib
# make your content unique
#-----------------
# Content-Noise-Content Machine learning script
#-----------------
# Copyright (C) 2026 by Mykhailo Samarin
# All rights reserved worldwide
#-----------------
# Under General Public License
#-----------------
# Visit http://github.com/samarin-dev for more information
#-----------------

import os
import glob
import random
import argparse
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

INPUT_DIR = "input"
OUTPUT_DIR = "output"
ML_DIR = "ML"
WEIGHTS_PATH = os.path.join(ML_DIR, "autoencoder.pth")

IMG_SIZE = 256
EPOCHS = 10
LEARNING_RATE = 0.001
BATCH_SIZE = 16


class Autoencoder(nn.Module):
    def __init__(self):
        super(Autoencoder, self).__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 16, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.ConvTranspose2d(16, 3, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


class MediaDataset(Dataset):
    def __init__(self, files):
        self.samples = []
        for filepath in files:
            ext = filepath.split(".")[-1].lower()
            if ext in ["jpg", "jpeg", "png", "bmp"]:
                self.samples.append(filepath)
            elif ext in ["mp4", "avi", "mov", "mkv"]:
                cap = cv2.VideoCapture(filepath)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                for i in range(frame_count):
                    self.samples.append((filepath, i))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        if isinstance(sample, tuple):
            filepath, frame_idx = sample
            cap = cv2.VideoCapture(filepath)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                frame = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        else:
            frame = cv2.imread(sample)
            if frame is None:
                frame = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)

        frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return torch.from_numpy(frame).permute(2, 0, 1)


def preprocess_frame(frame):
    original_shape = frame.shape
    frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    frame_normalized = frame_rgb.astype(np.float32) / 255.0
    tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1).unsqueeze(0)
    return tensor, original_shape


def postprocess_tensor(tensor, original_shape):
    output = tensor.squeeze(0).permute(1, 2, 0).cpu().detach().numpy()
    output = (output * 255.0).clip(0, 255).astype(np.uint8)
    output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
    return cv2.resize(output_bgr, (original_shape[1], original_shape[0]))


def run_inference(files, model, device):
    model.eval()
    for filepath in files:
        filename = os.path.basename(filepath)
        out_path = os.path.join(OUTPUT_DIR, filename)
        ext = filename.split(".")[-1].lower()

        if ext in ["jpg", "jpeg", "png", "bmp"]:
            img = cv2.imread(filepath)
            if img is None:
                print(f"[-] Can`t open photo: {filepath}")
                continue
            tensor, orig_shape = preprocess_frame(img)
            with torch.no_grad():
                output = model(tensor.to(device))
            cv2.imwrite(out_path, postprocess_tensor(output, orig_shape))
            print(f"[+] Photo saved: {out_path}")

        elif ext in ["mp4", "avi", "mov", "mkv"]:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                print(f"[-] Can`t open video: {filepath}")
                continue
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                tensor, orig_shape = preprocess_frame(frame)
                with torch.no_grad():
                    output = model(tensor.to(device))
                out.write(postprocess_tensor(output, orig_shape))
            cap.release()
            out.release()
            print(f"[+] Video saved: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--directml", action="store_true")
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--learn", action="store_true")
    args = parser.parse_args()

    for directory in [INPUT_DIR, OUTPUT_DIR, ML_DIR]:
        os.makedirs(directory, exist_ok=True)

    if args.device:
        device = torch.device(args.device)
    elif args.cuda:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif args.directml:
        import torch_directml
        device = torch_directml.device()
    else:
        device = torch.device("cpu")

    model = Autoencoder().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=0.9)

    if os.path.exists(WEIGHTS_PATH):
        map_loc = "cpu" if args.directml else device
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=map_loc, weights_only=False))
        print("[*] Weights loaded.")
    elif not args.learn:
        print("[!] Weights not found!.")

    files = glob.glob(os.path.join(INPUT_DIR, "*"))
    if not files:
        print(f"[-] In dir '{INPUT_DIR}' no files.")
        return

    if args.learn:
        dataset = MediaDataset(files)
        print(f"[*] Samples in dataset: {len(dataset)}")

        for epoch in range(EPOCHS):
            indices = list(range(len(dataset)))
            random.shuffle(indices)
            sampler = torch.utils.data.SubsetRandomSampler(indices)
            loader = DataLoader(dataset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)

            model.train()
            total_loss = 0.0

            for batch in loader:
                batch = batch.to(device)
                optimizer.zero_grad()
                output = model(batch)
                loss = criterion(output, batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(loader)
            print(f"Epoch {epoch + 1}/{EPOCHS} | Average loss: {avg_loss:.4f}")

        torch.save(model.state_dict(), WEIGHTS_PATH)
        print(f"[*] Weights saved: {WEIGHTS_PATH}")
    else:
        run_inference(files, model, device)


if __name__ == "__main__":
    main()