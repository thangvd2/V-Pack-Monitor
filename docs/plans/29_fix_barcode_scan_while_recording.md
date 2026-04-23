# Fix: Barcode scan while recording silently overwrites waybill

**Status**: DONE — Implemented and merged.

## Bug Description

When an OPERATOR scans a new barcode while video recording is in progress for a previous barcode:
- **Expected**: Show warning toast "Đang ghi đơn. Quét STOP trước", keep displaying original barcode
- **Actual**: No warning shown, toast silently switches to display the new barcode value, while FFmpeg continues recording the original barcode

## Root Cause

**Frontend-backend status ambiguity** in `sendScanAction()` (App.jsx:763).

The backend returns `status: "recording"` for TWO different scenarios:
1. **Successful new recording** (routes_records.py:219): `{"status": "recording", "record_id": 123, "message": "Bắt đầu ghi hình..."}`
2. **Blocked — already recording** (routes_records.py:320): `{"status": "recording", "message": "Đang ghi đơn..."}`

The frontend treats both identically — enters `if (res.data.status === 'recording')` branch and calls `setCurrentWaybill(finalBarcode)`, overwriting the displayed waybill with the new barcode. The backend's warning message is never shown.

## Fix Strategy

**Option A: Frontend-only (check `record_id` presence)** — RECOMMENDED

No API contract change. Distinguish the two cases by checking if `record_id` exists in the response:
- `record_id` present → genuine new recording → update waybill
- `record_id` absent → blocked scan → show warning, keep current waybill

Add a proactive client-side guard (`packingStatus === 'packing'`) for instant feedback before API call.

## Files to Change (1 file)

### `web-ui/src/App.jsx`

#### Change 1: `sendScanAction()` — distinguish recording vs blocked (line 763-766)

**Before:**
```javascript
if (res.data.status === 'recording') {
    activeRecordIdRef.current = res.data.record_id || null;
    setPackingStatus('packing');
    setCurrentWaybill(finalBarcode);
}
```

**After:**
```javascript
if (res.data.status === 'recording') {
    if (res.data.record_id) {
        // Genuine new recording started
        activeRecordIdRef.current = res.data.record_id;
        setPackingStatus('packing');
        setCurrentWaybill(finalBarcode);
    } else {
        // Blocked: already recording a different barcode
        showToast(res.data.message || 'Đang ghi đơn. Quét STOP trước khi quét mã mới.', 'warning');
        playRecordingWarning();
    }
}
```

**Why `playRecordingWarning()`?**: The `recording_warning` SSE event already uses this sound (line 494). Reusing it provides audio feedback that the scan was rejected.

#### Change 2: Barcode scanner listener — proactive guard (line 895-896)

**Before:**
```javascript
if (finalBarcode.length > 0) {
    await sendScanAction(finalBarcode);
}
```

**After:**
```javascript
if (finalBarcode.length > 0) {
    if (packingStatus === 'packing' && finalBarcode !== 'STOP' && finalBarcode !== 'EXIT') {
        showToast('Đang ghi đơn. Quét STOP trước khi quét mã mới.', 'warning');
        playRecordingWarning();
    } else {
        await sendScanAction(finalBarcode);
    }
}
```

**Why this guard?**: Provides instant feedback (0ms network latency) when operator scans during recording. `STOP` and `EXIT` must bypass this check since they are valid commands during recording.

**Important**: `packingStatus` is read from state, NOT from a ref. Verify that `packingStatus` is fresh when the keydown handler reads it. Since `packingStatus` is in the dependency concept but NOT in the `useEffect` deps array (line 916: `eslint-disable-next-line`), this could be a stale closure.

**Stale closure fix**: Use a ref to track packing status:
```javascript
const packingStatusRef = useRef(packingStatus);
packingStatusRef.current = packingStatus;
```
Then in the guard: `if (packingStatusRef.current === 'packing' && ...)`

#### Change 3: Add `packingStatusRef` (near line 272 where `activeRecordIdRef` is defined)

```javascript
const packingStatusRef = useRef(packingStatus);
packingStatusRef.current = packingStatus;
```

## Files NOT Changed

- `routes_records.py` — Backend guard is correct, no change needed
- `routes_stations.py` — Not related
- `database.py` — Not related
- `recorder.py` — Not related

## Testing

### Manual test:
1. Login as nv1 (OPERATOR)
2. Select station, scan barcode "SPX001" → recording starts (red indicator)
3. While recording, scan barcode "SPX002"
4. **Expected**: Warning toast "Đang ghi đơn. Vui lòng quét STOP để kết thúc đơn hàng hiện tại." + warning sound
5. **Expected**: Waybill display still shows "SPX001"
6. Scan "STOP" → recording stops for SPX001
7. Scan "SPX002" → new recording starts normally

### Edge cases:
- Scan "STOP" while recording → should stop normally (not trigger warning)
- Scan "EXIT" while recording → should exit normally (not trigger warning)
- Rapid scanning → warning should fire each time, no duplicate toast issues

### Backend test (pytest):
Not needed — backend behavior unchanged. Existing tests cover the guard at `routes_records.py:318-322`.

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Stale `packingStatus` in keydown handler | Medium | Use `packingStatusRef` instead of direct state |
| Warning sound too aggressive | Low | Reuses existing `playRecordingWarning()` |
| API contract change | None | Frontend-only fix, no backend changes |

## Scope Boundary

**IN scope:**
- Fix the silent waybill overwrite bug
- Add warning toast + sound when scanning during recording
- Proactive client-side guard for instant feedback

**OUT of scope:**
- Backend changes
- Toast color theming (currently all amber, separate concern)
- Recording indicator redesign
- Any changes to STOP/EXIT flow
