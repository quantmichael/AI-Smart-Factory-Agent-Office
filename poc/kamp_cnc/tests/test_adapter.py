from __future__ import annotations

import copy
import unittest
from pathlib import Path

from poc.kamp_cnc.adapter import AdapterValidationError, KAMPCNCAdapter
from poc.kamp_cnc.contracts import FEATURE_COLUMNS


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "정밀가공_품질보증_데이터셋.csv"


def feature_count(observation: dict) -> int:
    process = observation["process_features"]
    return (
        len(process["spindle_speed"])
        + sum(len(v) for v in process["servo_current"].values())
        + sum(len(v) for v in process["servo_load"].values())
        + len(process["spindle_load"])
    )


def flatten_features(observation: dict) -> dict[str, float]:
    process = observation["process_features"]
    flattened = {f"SpindleSpeed_{stat}": value for stat, value in process["spindle_speed"].items()}
    for axis, statistics in process["servo_current"].items():
        flattened.update({f"ServoCurrent_{axis}_{stat}": value for stat, value in statistics.items()})
    for axis, statistics in process["servo_load"].items():
        flattened.update({f"ServoLoad_{axis}_{stat}": value for stat, value in statistics.items()})
    flattened.update({f"SpindleLoad_{stat}": value for stat, value in process["spindle_load"].items()})
    return flattened


class KAMPCNCAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = KAMPCNCAdapter()
        cls.rows = cls.adapter.read_csv(CSV_PATH)
        cls.pair_index = cls.adapter.build_pair_index(cls.rows)
        cls.unpaired_pass_index = next(i for i, r in enumerate(cls.rows) if r["passorfail"] == "0" and not cls.pair_index[i].paired_serial)
        paired_indices = [i for i, metadata in cls.pair_index.items() if metadata.paired_serial]
        cls.paired_pass_index = next(i for i in paired_indices if cls.rows[i]["passorfail"] == "0")
        cls.paired_fail_index = next(i for i in paired_indices if cls.rows[i]["passorfail"] == "1")

    def adapt(self, index: int) -> dict:
        return self.adapter.adapt_row(self.rows[index], index, self.pair_index[index]).to_dict()

    def test_01_normal_pass_row(self) -> None:
        obs = self.adapt(self.unpaired_pass_index)
        self.assertEqual(obs["ground_truth"]["status"], "PASS")
        self.assertFalse(obs["data_quality"]["paired_serial"])

    def test_02_normal_fail_mapping_with_valid_unpaired_fixture(self) -> None:
        row = copy.deepcopy(self.rows[self.unpaired_pass_index])
        row["passorfail"] = "1"
        obs = self.adapter.adapt_row(row, 2000).to_dict()
        self.assertEqual(obs["ground_truth"]["status"], "FAIL")
        self.assertFalse(obs["data_quality"]["paired_serial"])

    def test_03_paired_pass_observation(self) -> None:
        obs = self.adapt(self.paired_pass_index)
        self.assertEqual(obs["ground_truth"]["status"], "PASS")
        self.assertTrue(obs["data_quality"]["paired_serial"])

    def test_04_paired_fail_observation(self) -> None:
        obs = self.adapt(self.paired_fail_index)
        self.assertEqual(obs["ground_truth"]["status"], "FAIL")
        self.assertTrue(obs["data_quality"]["paired_serial"])

    def test_05_ground_truth_mapping(self) -> None:
        self.assertEqual(self.adapt(self.unpaired_pass_index)["ground_truth"]["raw_label"], 0)
        self.assertEqual(self.adapt(self.paired_fail_index)["ground_truth"]["raw_label"], 1)

    def test_06_ground_truth_is_not_prediction(self) -> None:
        ground_truth = self.adapt(self.paired_fail_index)["ground_truth"]
        self.assertEqual(ground_truth["source_type"], "dataset_ground_truth")
        self.assertIs(ground_truth["prediction"], False)

    def test_07_all_40_features_are_preserved(self) -> None:
        observation = self.adapt(self.unpaired_pass_index)
        flattened = flatten_features(observation)
        self.assertEqual(len(FEATURE_COLUMNS), 40)
        self.assertEqual(feature_count(observation), 40)
        self.assertEqual(set(flattened), set(FEATURE_COLUMNS))
        for column in FEATURE_COLUMNS:
            self.assertEqual(flattened[column], float(self.rows[self.unpaired_pass_index][column]))

    def test_08_paired_metadata(self) -> None:
        quality = self.adapt(self.paired_pass_index)["data_quality"]
        self.assertEqual(quality, {
            "paired_serial": True,
            "same_timestamp_pair": True,
            "paired_label_status": "PASS_FAIL_PAIR",
            "feature_vector_distinct": True,
        })

    def test_09_deterministic_sample_id(self) -> None:
        first = self.adapt(self.paired_pass_index)["observation"]["sample_id"]
        second = self.adapt(self.paired_pass_index)["observation"]["sample_id"]
        self.assertEqual(first, second)
        self.assertNotEqual(first, self.adapter.adapt_row(self.rows[self.paired_pass_index], 9999, self.pair_index[self.paired_pass_index]).to_dict()["observation"]["sample_id"])

    def test_10_invalid_label_fails_closed(self) -> None:
        row = copy.deepcopy(self.rows[0])
        row["passorfail"] = "2"
        with self.assertRaisesRegex(AdapterValidationError, "INVALID_LABEL"):
            self.adapter.adapt_row(row, 0)

    def test_11_missing_feature_fails_closed(self) -> None:
        row = copy.deepcopy(self.rows[0])
        del row[FEATURE_COLUMNS[0]]
        with self.assertRaisesRegex(AdapterValidationError, "MISSING_FEATURE"):
            self.adapter.adapt_row(row, 0)

    def test_12_invalid_numeric_fails_closed(self) -> None:
        row = copy.deepcopy(self.rows[0])
        row[FEATURE_COLUMNS[0]] = "not-a-number"
        with self.assertRaisesRegex(AdapterValidationError, "INVALID_NUMERIC"):
            self.adapter.adapt_row(row, 0)

    def test_13_invalid_timestamp_fails_closed(self) -> None:
        row = copy.deepcopy(self.rows[0])
        row["ReceivedDateTime"] = "not-a-timestamp"
        with self.assertRaisesRegex(AdapterValidationError, "INVALID_TIMESTAMP"):
            self.adapter.adapt_row(row, 0)

    def test_14_missing_metadata_fails_closed(self) -> None:
        row = copy.deepcopy(self.rows[0])
        row["SerialNo"] = ""
        with self.assertRaisesRegex(AdapterValidationError, "MISSING_METADATA"):
            self.adapter.adapt_row(row, 0)

    def test_15_full_dataset_compatibility(self) -> None:
        observations = self.adapter.adapt_all(self.rows)
        self.assertEqual(len(observations), 1085)
        self.assertEqual(len({o.observation["sample_id"] for o in observations}), 1085)


if __name__ == "__main__":
    unittest.main()
