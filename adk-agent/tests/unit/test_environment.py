# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Детерміновані тести середовища агента, без звернень до моделі."""

from app.environment import NOT_FOUND, check_property, lookup_http_method


def test_existing_method() -> None:
    assert lookup_http_method("delete").startswith("delete:")


def test_unknown_method() -> None:
    assert lookup_http_method("trace").startswith(NOT_FOUND)


def test_property_of_method() -> None:
    assert check_property("post", "idempotent").startswith("post: idempotent=no")
    assert check_property("head", "safe").startswith("head: safe=yes")
