# Plan: Admin Tab Navigation

**Status**: DONE — Implemented and merged.

## Goal

Tách Admin UI thành 2 tabs: **[Vận hành]** (default) và **[Tổng quan]**. Tab Vận hành chứa live cameras + records. Tab Tổng quan chứa Dashboard stats + SystemHealth. Search bar giữ trong filter bar của records section.

## Current State

AdminDashboard.jsx gộp cả Dashboard stats + Live cameras. Records list nằm ở App.jsx render bên dưới. Khi admin scroll, tất cả trộn lẫn.

## Target Layout

```
Header:  V-Pack Monitor  [Vận hành*] [Tổng quan] [Cài đặt] [👤]
                         ^default active

Tab [Vận hành]:
  📹 Live Cameras Grid (camera cards)
  📋 Lịch sử ghi hình (search + filter + records)

Tab [Tổng quan]:
  📊 Dashboard (stats/charts)
  🏥 SystemHealth (CPU/RAM/Disk)
```

## Changes

### 1. Add `adminTab` state — `App.jsx`

New state variable:
```jsx
const [adminTab, setAdminTab] = useState('operations'); // 'operations' | 'overview'
```

Default = `'operations'` (Vận hành).

### 2. Add tab buttons in header — `App.jsx`

Replace current header buttons area (around line 1413-1422):
- Remove "← Tổng quan" back button (no longer needed)
- Add tab navigation buttons for admin when in grid mode:

```jsx
{/* Admin Tab Navigation */}
{currentUser?.role === 'ADMIN' && viewMode === 'grid' && (
  <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
    <button
      onClick={() => setAdminTab('operations')}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
        adminTab === 'operations'
          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      📹 Vận hành
    </button>
    <button
      onClick={() => setAdminTab('overview')}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
        adminTab === 'overview'
          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      📊 Tổng quan
    </button>
  </div>
)}
```

Location: In header `<div>` after station selector, before update info button.

### 3. Refactor `AdminDashboard.jsx` — Remove Dashboard section

AdminDashboard.jsx should ONLY contain the live cameras grid. Remove the Dashboard.jsx embedding:

```jsx
// REMOVE lines 27-35 (Dashboard section)
// KEEP lines 37-154 (Live Cameras Grid only)
```

The component becomes purely the live cameras grid.

### 4. Tab content rendering — `App.jsx`

In the main content area (line ~1576-1600), change the admin render logic:

```jsx
{currentUser?.role === 'ADMIN' && viewMode === 'grid' ? (
  adminTab === 'operations' ? (
    <AdminDashboard
      stations={stations}
      stationStatuses={stationStatuses}
      ...
      onStationClick={(id) => {
        setActiveStationId(id);
        setViewMode('single');
      }}
    />
  ) : (
    // Overview tab: Dashboard + SystemHealth
    <div className="space-y-8">
      <Dashboard
        stations={stations}
        activeStationId={''}
        storageInfo={storageInfo}
        currentUser={currentUser}
        analytics={analytics}
      />
      <SystemHealth currentUser={currentUser} />
    </div>
  )
) : viewMode === 'grid' ? (
  // ... operator grid view unchanged
)}
```

### 5. Records section — `App.jsx`

Records section (line ~1927) stays unchanged. It's always visible for admin in grid mode regardless of tab.

Wait — actually records should only show in [Vận hành] tab. Update guard:

```jsx
{(viewMode !== 'grid' || (currentUser?.role === 'ADMIN' && adminTab === 'operations')) && (
```

When admin switches to [Tổng quan], records section hides.

### 6. Back button update — `App.jsx`

"← Tổng quan" button (line 1414): change from `setViewMode('grid')` to also set `setAdminTab('operations')`:

```jsx
{viewMode === 'single' && currentUser?.role === 'ADMIN' && (
  <button
    onClick={() => {
      setViewMode('grid');
      setAdminTab('operations');
    }}
    ...
  >
    ← Tổng quan
  </button>
)}
```

### 7. Hide station selector for admin in grid mode — `App.jsx`

Station selector dropdown in header (line ~1343) is redundant for admin:
- Tab [Vận hành]: Records filter already has station dropdown
- Tab [Tổng quan]: No station selection needed
- Drill-down: Admin clicks station cards, not dropdown

Change guard from:
```jsx
{(viewMode !== 'grid' || currentUser?.role === 'ADMIN') && (
```
To:
```jsx
{(viewMode !== 'grid' && !(currentUser?.role === 'ADMIN' && viewMode === 'grid')) && (
```

Or simpler — just hide for admin in grid mode:
```jsx
{!(currentUser?.role === 'ADMIN' && viewMode === 'grid') && (
```

### 8. Import SystemHealth — `App.jsx`

Add import if not already present:
```jsx
import SystemHealth from './SystemHealth';
```

Check if SystemHealth is already imported.

## Files to Change

| File | Change |
|------|--------|
| `App.jsx` | Add `adminTab` state, tab buttons, tab rendering, hide station selector in grid mode, import SystemHealth |
| `AdminDashboard.jsx` | Remove Dashboard.jsx section, keep only live cameras |

## Files NOT Changed

- `Dashboard.jsx` — Reused as child component
- `SystemHealth.jsx` — Reused as child component
- Backend files — No changes needed
- Operator flow — Unchanged

## Testing

1. Admin login → default tab [Vận hành] → see live cameras + records
2. Click [Tổng quan] → see Dashboard stats + SystemHealth, records hidden
3. Click [Vận hành] → back to live cameras + records
4. Click station card → single station view → "← Tổng quan" back button
5. Operator flow unchanged — no tabs, no adminTab state
