"""
Mechanical smoke test for ml/training/train_photo_model.py — proves the data
loading, model wiring, training loop and artifact-saving have no bugs, using
a handful of tiny synthetic solid-colour images. This does NOT prove the
resulting model detects real plant diseases; that needs the real
PlantVillage/PlantDoc dataset, which this sandbox's network policy blocks
(see the module docstring). Skipped automatically if torch/torchvision
aren't installed.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml" / "training"))

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from PIL import Image  # noqa: E402

import train_photo_model  # noqa: E402


@pytest.fixture()
def synthetic_dataset(tmp_path):
    classes = {"healthy": (60, 160, 60), "diseased": (150, 90, 40)}
    for class_name, rgb in classes.items():
        class_dir = tmp_path / class_name
        class_dir.mkdir()
        for i in range(6):
            img = Image.new("RGB", (32, 32), rgb)
            img.save(class_dir / f"img_{i}.jpg")
    return tmp_path


def test_training_pipeline_runs_end_to_end(synthetic_dataset, tmp_path):
    out_dir = tmp_path / "out"
    result = train_photo_model.train(
        data_dir=str(synthetic_dataset), out_dir=str(out_dir),
        epochs=1, batch_size=2, val_fraction=0.34, lr=1e-3, pretrained=False,
    )
    assert set(result["classes"]) == {"healthy", "diseased"}
    assert (out_dir / "photo_model.pt").exists()
    assert (out_dir / "photo_classes.json").exists()
    saved_classes = json.loads((out_dir / "photo_classes.json").read_text())
    assert saved_classes == result["classes"]


def test_build_model_output_shape_matches_num_classes():
    model = train_photo_model.build_model(num_classes=4, pretrained=False)
    model.eval()
    with torch.no_grad():
        out = model(torch.zeros(1, 3, 224, 224))
    assert out.shape == (1, 4)
