"""Regression for explicit sentencing direction (AI-assisted: OpenAI Codex)."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('factors', Path(__file__).resolve().parents[2] / 'scripts/annotate/sentencing_factors.py')
factors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factors)

class DirectionTest(unittest.TestCase):
    def test_only_explicit_labels(self):
        for text in ('정상을 참작하여 감경한다', '죄질이 나쁘므로 엄히 처벌한다'):
            self.assertIsNone(factors.FAVOR.search(text))
            self.assertIsNone(factors.DISFAVOR.search(text))
        self.assertIsNotNone(factors.FAVOR.search('유리한 정상'))
        self.assertIsNotNone(factors.DISFAVOR.search('불리한 정상'))
