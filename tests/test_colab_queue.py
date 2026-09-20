import unittest

from colab_queue import ColabQueueError, build_colab_job, job_id


class ColabQueueTests(unittest.TestCase):
    def base_job(self):
        return {
            "instruction": "Create a premium zombie survivor sprite",
            "manifest": {
                "constraints": {
                    "generationWidth": 1024,
                    "generationHeight": 768,
                    "generationSteps": 30,
                    "seed": 42,
                }
            },
        }

    def test_build_job_is_deterministic(self):
        one = build_colab_job(self.base_job())
        two = build_colab_job(self.base_job())
        self.assertEqual(one["id"], two["id"])
        self.assertEqual(one["width"], 1024)
        self.assertEqual(one["height"], 768)
        self.assertEqual(one["steps"], 30)
        self.assertEqual(one["seed"], 42)

    def test_build_job_limits_references_to_ten(self):
        refs = [f"https://example.com/{index}.png" for index in range(12)]
        value = build_colab_job(self.base_job(), reference_urls=refs)
        self.assertEqual(len(value["references"]), 10)

    def test_missing_instruction_is_rejected(self):
        with self.assertRaisesRegex(ColabQueueError, "instruction"):
            build_colab_job({"manifest": {"constraints": {}}})

    def test_job_id_changes_with_semantic_input(self):
        first = build_colab_job(self.base_job())
        changed = self.base_job()
        changed["instruction"] += " in rain"
        second = build_colab_job(changed)
        self.assertNotEqual(first["id"], second["id"])

    def test_job_id_is_short_content_hash(self):
        value = job_id({"x": 1})
        self.assertEqual(len(value), 24)
        int(value, 16)


if __name__ == "__main__":
    unittest.main()
