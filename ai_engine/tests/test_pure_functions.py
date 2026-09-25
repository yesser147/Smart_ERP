"""
Unit tests for the pure functions of the AI engine (no database, no LLM).
Run from ai_engine/:   venv\\Scripts\\python -m unittest discover -s tests -v
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import config
from models.nl_assistant.nl_query_assistant import validate_sql
from models.recruitment.matcher import _blend, _weighted
from models.recruitment.cv_intelligence_core import normalize_education_level, build_cv_embedding_text
from models.recruitment.applicant_chat import _redact
from models.retention.preprocess import bucket_rare_categories, format_ml_features
import security
from models.retention.survival import kaplan_meier


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_token(claims: dict, secret_b64: str, alg="HS512") -> str:
    header = _b64url(json.dumps({"alg": alg}).encode())
    payload = _b64url(json.dumps(claims).encode())
    digest = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}[alg]
    sig = hmac.new(base64.b64decode(secret_b64), f"{header}.{payload}".encode(), digest).digest()
    return f"{header}.{payload}.{_b64url(sig)}"


class SqlGuardTest(unittest.TestCase):
    def test_allowed_queries(self):
        for q in [
            "SELECT * FROM v_department_turnover ORDER BY turnover_rate_pct DESC LIMIT 5;",
            "WITH top AS (SELECT * FROM v_department_turnover) SELECT * FROM top",
            "SELECT EXTRACT(YEAR FROM start_date), COUNT(*) FROM v_ai_retention_features GROUP BY 1",
            "SELECT * FROM (SELECT * FROM v_salary_distribution) s",
        ]:
            self.assertTrue(validate_sql(q), q)

    def test_blocked_queries(self):
        for q in [
            "SELECT * FROM users",
            "SELECT * FROM v_department_turnover, users",
            "SELECT pg_sleep(100) FROM v_department_turnover",
            "SELECT * FROM v_department_turnover; DROP TABLE users",
            "DELETE FROM v_department_turnover",
            "SELECT * FROM (SELECT * FROM employees) e",
        ]:
            self.assertFalse(validate_sql(q), q)


class MatcherScoreTest(unittest.TestCase):
    def test_missing_signal_is_dropped(self):
        self.assertAlmostEqual(_weighted([(0.4, 80), (0.25, None), (0.25, 60), (0.1, 50)]),
                               (0.4 * 80 + 0.25 * 60 + 0.1 * 50) / 0.75)

    def test_low_coverage_caps_the_score(self):
        self.assertLessEqual(_blend(95, 10, 90, 90), 35)


class CvCoreTest(unittest.TestCase):
    def test_education_normalization(self):
        self.assertEqual(normalize_education_level("Master of Science"), "Master's")
        self.assertIsNone(normalize_education_level("x" * 50))
        self.assertEqual(normalize_education_level("Diploma"), "Other")

    def test_embedding_text_puts_skills_first(self):
        self.assertTrue(build_cv_embedding_text("cv", ["Java"], 3, "PhD", "Dev").startswith("Skills: Java."))

    def test_redaction_keeps_date_ranges(self):
        out = _redact("Call +1 (555) 123-4567, mail a@b.com. 2015 - 2019. Ada Byron, Adams St.", ("Ada", "Byron"))
        self.assertIn("[name] [name]", out)
        self.assertIn("Adams", out)
        self.assertIn("[phone]", out)
        self.assertIn("[email]", out)
        self.assertIn("2015 - 2019", out)


class RetentionPreprocessTest(unittest.TestCase):
    def test_saved_mapping_is_reused(self):
        df = pd.DataFrame({"job_function": ["A"] * 40 + ["B"] * 2})
        _, mapping = bucket_rare_categories(df, ["job_function"])
        small = pd.DataFrame({"job_function": ["B", "B", "A"]})
        out, _ = bucket_rare_categories(small, ["job_function"], mapping=mapping)
        self.assertEqual(list(out["job_function"]), ["Other", "Other", "A"])

    def test_tenure_stops_at_exit_date(self):
        base = {c: [1, 1] for c in config.NUMERIC_FEATURES if c != "tenure_days"}
        base["overtime"] = [True, None]
        base.update({c: ["x", "x"] for c in config.CATEGORICAL_FEATURES})
        df = pd.DataFrame({"start_date": ["2020-01-01", "2020-01-01"],
                           "exit_date": ["2021-01-01", None], **base})
        X = format_ml_features(df)
        self.assertEqual(X["tenure_days"].iloc[0], 366)
        self.assertGreater(X["tenure_days"].iloc[1], 366)
        self.assertEqual(X["overtime"].iloc[0], 1.0)
        self.assertTrue(pd.isna(X["overtime"].iloc[1]))
        for protected in ("gender", "age", "marital_status"):
            self.assertNotIn(protected, X.columns)


class JwtTest(unittest.TestCase):
    def setUp(self):
        self._old = config.JWT_SECRET
        config.JWT_SECRET = base64.b64encode(b"k" * 64).decode()

    def tearDown(self):
        config.JWT_SECRET = self._old

    def test_valid_token(self):
        token = make_token({"sub": "a@b.c", "role": "ROLE_HR_MANAGER", "exp": time.time() + 60},
                           config.JWT_SECRET)
        self.assertEqual(security.decode_token(token)["role"], "ROLE_HR_MANAGER")

    def test_expired_or_forged_token(self):
        expired = make_token({"sub": "a", "exp": time.time() - 1}, config.JWT_SECRET)
        forged = make_token({"sub": "a", "exp": time.time() + 60}, base64.b64encode(b"x" * 64).decode())
        for token in (expired, forged, "not.a.token"):
            with self.assertRaises(ValueError):
                security.decode_token(token)

    def test_role_is_enforced(self):
        from fastapi import HTTPException
        token = make_token({"sub": "a", "role": "ROLE_EMPLOYEE", "exp": time.time() + 60}, config.JWT_SECRET)
        with self.assertRaises(HTTPException) as ctx:
            security.require_hr_user(f"Bearer {token}")
        self.assertEqual(ctx.exception.status_code, 403)


class SurvivalTest(unittest.TestCase):
    def test_kaplan_meier_with_and_without_censoring(self):
        import numpy as np
        # three people leave after 1, 2 and 3 years
        self.assertEqual(kaplan_meier(np.array([1.0, 2.0, 3.0]), np.array([1, 1, 1]), horizon=3),
                         [100.0, 66.7, 33.3, 0.0])
        # the one who is still here after 2 years is censored: the curve stops dropping for them
        self.assertEqual(kaplan_meier(np.array([1.0, 2.0, 3.0]), np.array([1, 0, 1]), horizon=3),
                         [100.0, 66.7, 66.7, 0.0])


class SafeJsonTest(unittest.TestCase):
    def test_nan_becomes_null(self):
        import main_api
        body = main_api.SafeJSONResponse({"a": float("nan"), "b": [1.5, float("inf")]}).body
        self.assertEqual(json.loads(body), {"a": None, "b": [1.5, None]})


if __name__ == "__main__":
    unittest.main()
