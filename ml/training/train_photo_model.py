"""
Real trained leaf-disease photo classifier (medium addition #6) — transfer
learning on MobileNetV2, meant to replace doctor/vision.py's HSV colour-
bucket heuristic once you have real labelled photos.

NOT run against real data in this session: PlantVillage/PlantDoc need
Kaggle or a large GitHub download, and this sandbox's egress policy blocks
kaggle.com (confirmed 403) and only allows small individual file fetches
from raw.githubusercontent.com, not a multi-GB dataset checkout — and a
real training pass over tens of thousands of images needs more time/compute
than a single sandboxed session budget allows anyway. This script IS
mechanically verified: `tests/ml/test_train_photo_model_smoke.py` runs it
end-to-end against a handful of synthetic solid-colour images (a few KB) to
prove the pipeline itself (data loading, model wiring, training loop,
saving artifacts) has no bugs — that is not the same as proving the
resulting model is any good at real disease detection, which needs the real
dataset trained on your own machine.

Usage (on your own machine, after `pip install torch torchvision` and
downloading PlantVillage via the Kaggle CLI into an ImageFolder layout —
one subfolder per class):

    python3 ml/training/train_photo_model.py \
        --data-dir /path/to/PlantVillage/color \
        --epochs 5 --out-dir ml/registry/v1

Produces photo_model.pt (state dict) and photo_classes.json (index -> class
name) in --out-dir. services/api/app/doctor/vision.py would need a new
function to load and run this model, added once you have real trained
weights to point it at (not stubbed here to avoid shipping a fake "vision
model loaded" path that silently does nothing).
"""
import argparse
import json
import os


def build_model(num_classes: int, pretrained: bool = True):
    import torch.nn as nn
    from torchvision import models

    weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
    try:
        model = models.mobilenet_v2(weights=weights)
    except Exception as e:
        # No internet access to download pretrained weights (e.g. a sandboxed
        # environment) — fall back to a randomly-initialized backbone rather
        # than crash. Transfer learning needs the pretrained weights to be any
        # good; this fallback exists for smoke-testing the pipeline, not for
        # producing a usable model.
        print(f"[warn] could not load pretrained weights ({e}); using random init instead")
        model = models.mobilenet_v2(weights=None)
    for param in model.features.parameters():
        param.requires_grad = False  # freeze the backbone, train only the classifier head
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)
    return model


def train(data_dir: str, out_dir: str, epochs: int, batch_size: int, val_fraction: float, lr: float,
          pretrained: bool = True):
    import torch
    from torch import nn, optim
    from torch.utils.data import DataLoader, random_split
    from torchvision import datasets, transforms

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    full_dataset = datasets.ImageFolder(data_dir, transform=transform)
    class_names = full_dataset.classes
    n_val = max(1, int(len(full_dataset) * val_fraction))
    n_train = len(full_dataset) - n_val
    train_ds, val_ds = random_split(full_dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(len(class_names), pretrained=pretrained).to(device)
    optimizer = optim.Adam(model.classifier.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    print(f"Classes ({len(class_names)}): {class_names}")
    print(f"Train: {n_train}  Val: {n_val}  Device: {device}")

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                preds = model(images).argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        val_acc = correct / total if total else 0.0
        print(f"Epoch {epoch + 1}/{epochs}  train_loss={running_loss / max(n_train, 1):.4f}  val_acc={val_acc:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(out_dir, "photo_model.pt"))
    with open(os.path.join(out_dir, "photo_classes.json"), "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"Saved photo_model.pt + photo_classes.json to {out_dir}")
    return {"classes": class_names, "final_val_acc": val_acc}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="ImageFolder-structured dataset root")
    parser.add_argument("--out-dir", default="ml/registry/v1")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--no-pretrained", action="store_true",
                         help="Skip downloading pretrained ImageNet weights (only for smoke-testing "
                              "the pipeline — a model trained this way won't be any good).")
    args = parser.parse_args()
    train(args.data_dir, args.out_dir, args.epochs, args.batch_size, args.val_fraction, args.lr,
          pretrained=not args.no_pretrained)


if __name__ == "__main__":
    main()
