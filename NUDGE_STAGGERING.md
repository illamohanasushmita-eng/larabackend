# Nudge Staggering Fix

## Problem
Even with the 6-hour cutoff, if you have multiple overdue tasks (e.g., 3 tasks from 1 hour ago), the backend sends **all 3 nudges at once** when the check runs, overwhelming you with notifications.

## Solution: ONE Nudge Per Check Cycle

### How It Works Now

**Before:**
```
Cycle 1 (3:00 PM):
- Task A (due 2:00 PM) → 30min passed → SEND NUDGE
- Task B (due 2:15 PM) → 30min passed → SEND NUDGE  
- Task C (due 2:30 PM) → 30min passed → SEND NUDGE
Result: 3 notifications at once! 😫
```

**After:**
```
Cycle 1 (3:00 PM):
- Task A (due 2:00 PM) → Oldest, 30min passed → SEND NUDGE ✅
- Task B & C → Skipped (already sent 1 nudge this cycle)

Cycle 2 (3:01 PM):
- Task A → Already nudged at 3:00 PM
- Task B (due 2:15 PM) → Oldest remaining, 30min passed → SEND NUDGE ✅
- Task C → Skipped

Cycle 3 (3:02 PM):
- Task A & B → Already nudged
- Task C (due 2:30 PM) → 30min passed → SEND NUDGE ✅

Result: Staggered nudges, 1 per minute! ✅
```

## Implementation Details

### 1. Priority Sorting
Tasks are sorted by **oldest waiting time** first:
```python
sorted_tasks = sorted(overdue_tasks, key=lambda x: (
    x[0].last_nudged_at if x[0].last_nudged_at else x[0].due_date
))
```

### 2. Limit Per Cycle
Only **1 nudge** is sent per check cycle (every minute):
```python
max_nudges_per_cycle = 1
if nudges_sent >= max_nudges_per_cycle:
    print("⏸️ Already sent 1 nudge this cycle. Waiting for next check.")
    break
```

### 3. Counter Increment
After each successful nudge, increment the counter:
```python
if success:
    task.last_nudged_at = now
    await db.commit()
    nudges_sent += 1  # Stop sending more this cycle
```

## Benefits

✅ **No Notification Storms**: Maximum 1 nudge per minute
✅ **Fair Ordering**: Oldest waiting task gets priority
✅ **Proper Spacing**: 30-minute gaps maintained between nudges for same task
✅ **Still Timely**: All eligible tasks get nudged, just staggered

## Example Timeline

**Scenario**: 3 tasks overdue, all eligible for first nudge

| Time | Task A (due 2:00 PM) | Task B (due 2:15 PM) | Task C (due 2:30 PM) |
|------|---------------------|---------------------|---------------------|
| **3:00 PM** | ✅ Nudge sent | ⏸️ Waiting | ⏸️ Waiting |
| **3:01 PM** | ⏸️ Waiting (just nudged) | ✅ Nudge sent | ⏸️ Waiting |
| **3:02 PM** | ⏸️ Waiting | ⏸️ Waiting (just nudged) | ✅ Nudge sent |
| **3:30 PM** | ✅ 2nd nudge (30min since last) | ⏸️ Waiting | ⏸️ Waiting |
| **3:31 PM** | ⏸️ Waiting (just nudged) | ✅ 2nd nudge | ⏸️ Waiting |
| **3:32 PM** | ⏸️ Waiting | ⏸️ Waiting (just nudged) | ✅ 2nd nudge |

## Adjusting the Limit

If you want to allow more nudges per cycle (e.g., 2 at a time):
```python
max_nudges_per_cycle = 2  # Change from 1 to 2
```

Current setting: **1 nudge per minute** for smooth, non-overwhelming experience.
