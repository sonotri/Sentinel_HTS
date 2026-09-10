from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_fds.agents.security_agent import SecurityAgent
from sentinel_fds.config import build_experiment_config
from sentinel_fds.evaluation.metrics import best_f1_threshold, classification_metrics
from sentinel_fds.fl.attacks import poison_labels, poison_weights
from sentinel_fds.fl.secure_aggregation import secure_aggregate_average
from sentinel_fds.models.artifacts import load_fds_artifact, save_fds_artifact, score_transactions
from sentinel_fds.models.fds import FraudMLP
from sentinel_fds.models.preprocessing import fit_transform_transactions
from sentinel_fds.privacy.dp import estimate_gaussian_epsilon
from sentinel_fds.privacy.leakage import gradient_leakage_attack
from sentinel_fds.simulation.transactions import SimulationConfig, generate_transactions
import torch


class SentinelSmokeTest(unittest.TestCase):
    def test_simulation_and_preprocessing(self) -> None:
        df = generate_transactions(SimulationConfig(samples_per_bank=20, seed=7))

        self.assertEqual(len(df), 60)
        self.assertEqual(set(df["bank"]), {"Bank A", "Bank B", "Bank C"})
        self.assertIn("is_fraud", df.columns)

        prepared = fit_transform_transactions(df)
        self.assertEqual(prepared.x.shape[0], 60)
        self.assertEqual(prepared.y.shape[0], 60)

    def test_security_agent_decision(self) -> None:
        df = generate_transactions(SimulationConfig(samples_per_bank=5, seed=9))
        decision = SecurityAgent().decide(df.iloc[0], fraud_score=0.8)

        self.assertEqual(decision.risk_level, "HIGH")
        self.assertEqual(decision.action, "BLOCK_TRANSACTION")
        self.assertTrue(decision.explanation)

    def test_threshold_tuning(self) -> None:
        y_true = [0, 0, 1, 1]
        scores = [0.05, 0.2, 0.7, 0.95]

        threshold, metrics = best_f1_threshold(y_true, scores)

        self.assertGreater(threshold, 0)
        self.assertLess(threshold, 1)
        self.assertEqual(metrics["f1"], 1.0)
        self.assertEqual(classification_metrics(y_true, scores, threshold)["f1"], 1.0)

    def test_privacy_estimate_increases_with_less_noise(self) -> None:
        lower_noise = estimate_gaussian_epsilon(noise_multiplier=0.5, sampling_rate=1.0, steps=3)
        higher_noise = estimate_gaussian_epsilon(noise_multiplier=1.0, sampling_rate=1.0, steps=3)

        self.assertGreater(lower_noise.epsilon, higher_noise.epsilon)
        self.assertEqual(higher_noise.delta, 1e-5)

    def test_config_and_artifact_roundtrip(self) -> None:
        config = build_experiment_config({"samples_per_bank": 12, "output_dir": "outputs/test"})
        df = generate_transactions(SimulationConfig(samples_per_bank=config.samples_per_bank, seed=11))
        prepared = fit_transform_transactions(df)
        model = FraudMLP(input_dim=prepared.x.shape[1])

        with tempfile.TemporaryDirectory() as tmp:
            artifact_dir = Path(tmp)
            save_fds_artifact(
                artifact_dir,
                model,
                prepared.transformer,
                threshold=0.5,
                metadata={"model_type": "test", "input_dim": prepared.x.shape[1]},
            )
            artifact = load_fds_artifact(artifact_dir)
            scored = score_transactions(artifact, df.head(3))

        self.assertEqual(config.samples_per_bank, 12)
        self.assertEqual(len(scored), 3)
        self.assertIn("predicted_fraud", scored.columns)

    def test_poisoning_helpers(self) -> None:
        labels = poison_labels(torch.tensor([0.0, 1.0]).numpy(), "label_flip")
        self.assertEqual(labels.tolist(), [1.0, 0.0])

        global_weights = {"w": torch.tensor([1.0, 2.0])}
        local_weights = {"w": torch.tensor([2.0, 4.0])}
        poisoned = poison_weights(global_weights, local_weights, "update_scale", scale=3.0)
        self.assertEqual(poisoned["w"].tolist(), [4.0, 8.0])

    def test_gradient_leakage_smoke(self) -> None:
        df = generate_transactions(SimulationConfig(samples_per_bank=8, seed=13))
        prepared = fit_transform_transactions(df)
        model = FraudMLP(input_dim=prepared.x.shape[1])

        result = gradient_leakage_attack(
            model,
            prepared.x[0],
            float(prepared.y[0]),
            iterations=2,
            seed=13,
        )

        self.assertGreaterEqual(result.feature_mse, 0)
        self.assertGreaterEqual(result.label_abs_error, 0)
        self.assertEqual(result.reconstructed_features.shape[0], prepared.x.shape[1])

    def test_secure_aggregation_matches_plain_average(self) -> None:
        client_weights = [
            {"w": torch.tensor([1.0, 3.0])},
            {"w": torch.tensor([5.0, 7.0])},
            {"w": torch.tensor([9.0, 11.0])},
        ]
        averaged, stats = secure_aggregate_average(client_weights, [1, 1, 1], seed=3)

        self.assertTrue(torch.allclose(averaged["w"], torch.tensor([5.0, 7.0]), atol=1e-6))
        self.assertLess(stats["reconstruction_mse"], 1e-10)
        self.assertGreater(stats["mean_mask_delta_norm"], 0)


if __name__ == "__main__":
    unittest.main()
