# Plan 42: Migrate to @pytest.mark.parametrize

**Ngày**: 2026-04-24
**Mức độ**: Low — Code quality improvement
**Loại**: Refactor (no behavior change)

---

## Problem

`test_api_helpers.py` có 22 test methods viết tay cho camera brand RTSP URLs:
- 12 methods cho `get_rtsp_url` (6 brands × 2 channels + edge cases)
- 10 methods cho `get_rtsp_sub_url` (5 brands × 2 channels + edge cases)

Mỗi method lặp cùng pattern: setup → call → assert. Khi thêm brand mới → phải viết 2-4 methods mới. Dễ quên.

`test_database_edge_cases.py:182-193` dùng loop-based parameterization — không hiển thị từng case trong pytest output.

---

## Scope

### Files to change:
- `tests/test_api_helpers.py` — migrate 22 methods → 4-6 parameterized tests
- `tests/test_database_edge_cases.py` — migrate loop → `@pytest.mark.parametrize`

### Example transformation:

**Before (2 methods):**
```python
def test_get_rtsp_url_imou_ch1(self):
    url = get_rtsp_url("192.168.1.1", "imou", channel=1)
    assert url == "rtsp://192.168.1.1:554/cam/realmonitor?channel=1&subtype=0"

def test_get_rtsp_url_imou_ch2(self):
    url = get_rtsp_url("192.168.1.1", "imou", channel=2)
    assert url == "rtsp://192.168.1.1:554/cam/realmonitor?channel=2&subtype=0"
```

**After (1 parameterized test):**
```python
@pytest.mark.parametrize("channel,subtype", [(1, 0), (2, 0)])
def test_get_rtsp_url_imou(self, channel, subtype):
    url = get_rtsp_url("192.168.1.1", "imou", channel=channel)
    assert url == f"rtsp://192.168.1.1:554/cam/realmonitor?channel={channel}&subtype={subtype}"
```

---

## Constraints

- **NO test coverage change** — same cases, same assertions
- All 22 existing test cases must be preserved
- Test names should remain descriptive (use `ids=` parameter)
- Group by brand for readability

---

## Verification

- [ ] `pytest tests/test_api_helpers.py -v` — same number of test cases (22)
- [ ] `pytest tests/test_database_edge_cases.py -v` — all pass
- [ ] `pytest tests/ -q` — all 326+ tests pass
