# Workspace Design Decisions

## Overview

This document explains the key design decisions behind the takeoff workspace UI, covering layout patterns, state management approach, interaction design, and technical trade-offs.

## Design Philosophy

### Estimator-First
The workspace is designed around the manual estimator workflow, not AI automation. The core loop is:
1. Navigate to a sheet
2. Select a condition
3. Draw measurements on the canvas
4. Review totals

AI features assist this loop but never replace it.

### Information Density
Construction estimators work with many conditions and sheets simultaneously. The UI prioritizes density over whitespace:
- Compact condition rows (24px height)
- 10px font for secondary information
- Minimal padding between sections
- All critical data visible without scrolling in normal cases

### Professional Tool Aesthetic
The dark theme (`neutral-950` background) with subtle borders reduces eye strain during long estimation sessions and matches the aesthetic of professional tools like Bluebeam Revu.

## Layout Decisions

### Three-Panel Layout
**Decision**: Fixed three-panel layout with resizable separators.

**Rationale**: Construction takeoff requires simultaneous access to:
- Sheet navigation (which sheet am I looking at?)
- Canvas (where am I measuring?)
- Conditions (what am I measuring for?)

A tabbed or stacked layout would require constant context switching. The three-panel layout keeps all three contexts visible.

**Trade-off**: Less canvas space on smaller screens. Mitigated by collapsible panels.

### Panel Size Constraints
| Panel | Default | Min | Max |
|---|---|---|---|
| Left (Sheets) | 20% | 15% | 35% |
| Center (Canvas) | — | 30% | — |
| Right (Conditions) | 25% | 18% | 40% |

**Rationale**: The center canvas needs at least 30% to be usable. Sheet names and condition names need at least 15-18% to be readable. Maximum constraints prevent accidentally hiding the canvas.

### Collapsible Panels
Both left and right panels can be collapsed via toolbar toggles, giving the canvas up to 100% width for detailed measurement work.

## State Management Decisions

### Single Zustand Store
**Decision**: One `workspaceStore` for all UI state.

**Rationale**: Workspace interactions are highly coupled:
- Selecting a condition enables drawing tools
- Switching sheets clears the drawing state
- Keyboard shortcuts need to check multiple state values simultaneously

A single store makes these cross-cutting concerns easy to implement without prop drilling or event buses.

**Trade-off**: The store file is large (~300 lines). Accepted because the alternative (multiple stores with synchronization) would be more complex.

### React Query for Server State
**Decision**: Separate server state (React Query) from UI state (Zustand).

**Rationale**: Server data has different lifecycle concerns:
- Caching and deduplication
- Background refetching
- Optimistic updates
- Cache invalidation on mutations

React Query handles all of these automatically. Mixing server data into Zustand would require reimplementing these features.

### Per-Project localStorage
**Decision**: SheetTree stores expanded/collapsed group state in localStorage keyed by project ID.

**Rationale**: Users work on multiple projects with different sheet structures. Global state would cause confusing behavior when switching projects. Per-project keying ensures each project's tree state is independent.

## Interaction Design

### Drawing Tool Invariant
**Decision**: Drawing tools require an active condition. Attempting to select a drawing tool without a condition shows a toast message.

**Rationale**: Every measurement must belong to a condition. Allowing drawing without a condition would create orphaned measurements or require a selection step after drawing. Enforcing condition-first prevents data integrity issues.

**Implementation**: `setActiveTool()` checks `activeConditionId` and sets `toolRejectionMessage` if null. The toast auto-dismisses after 3 seconds.

### Keyboard Shortcuts
**Decision**: Number keys 1-9 select conditions by position. Single-key shortcuts for common actions.

| Key | Action | Rationale |
|---|---|---|
| `1`-`9` | Select condition | Fast switching during measurement |
| `V` | Toggle visibility | Quick show/hide while drawing |
| `Ctrl+D` | Duplicate | Common pattern, matches other tools |
| `Delete` | Delete (with confirm) | Destructive action needs safety |
| `Escape` | Reset/deselect | Universal cancel pattern |

**Rationale**: Professional estimating tools use number keys for condition selection. This is the fastest way to switch between conditions during active measurement.

### Context Menu
**Decision**: Right-click on condition rows opens a context menu with all actions.

**Rationale**: Context menus are discoverable and don't consume screen space. They provide a secondary interaction path for users who prefer mouse-driven workflows over keyboard shortcuts.

### Delete Confirmation
**Decision**: Delete always requires confirmation via a modal dialog.

**Rationale**: Deleting a condition cascades to delete all its measurements. This is irreversible and potentially destructive (users may have hours of measurement work on a condition). The confirmation dialog shows the measurement count to help users understand the impact.

## Visual Design

### Condition Color Dots
Each condition has a color dot that matches its canvas drawing color. This provides instant visual association between the list and the canvas.

### Visibility Opacity
Hidden conditions (is_visible = false) render at 50% opacity in the list. This keeps them accessible but visually demoted.

### Active Condition Highlight
The active condition has:
- 2px blue left border (matches the blue accent color)
- Light blue background tint (30% opacity)

This provides clear selection feedback without overwhelming the compact layout.

### Scale Status Badges
Scale badges use traffic-light colors:
- Green: Calibrated (high confidence)
- Yellow: Detected (needs confirmation)
- Gray: No scale data

### Toast Feedback
Tool rejection messages appear as an amber toast at bottom-center. Amber (not red) because it's an informational constraint, not an error. The toast auto-dismisses because it's low-priority feedback that shouldn't require user interaction.

## Performance Decisions

### Image Preloading
**Decision**: Sheet images are preloaded before display, with a stale-flag pattern to prevent race conditions.

**Rationale**: Without preloading, switching sheets would show a blank canvas until the image loads. The stale flag prevents an old image's load callback from overwriting a newer image's state.

### Measurement Count Subquery
**Decision**: The sheets endpoint uses a SQL subquery for measurement counts instead of separate queries.

**Rationale**: A project may have 100+ sheets. Fetching measurement counts individually would require 100+ queries. The subquery computes all counts in a single database round-trip.

### Optimistic Visibility Toggle
**Decision**: Visibility toggles update the server via mutation and rely on React Query cache invalidation for UI update.

**Rationale**: For a simple boolean toggle, the React Query refetch (triggered by cache invalidation) is fast enough that optimistic updates aren't necessary. This keeps the implementation simple.

## Accessibility

### Focus Management
The workspace tracks focus region (`canvas`, `sheet-tree`, `conditions`, etc.) to scope keyboard shortcuts appropriately. Shortcuts are disabled in `dialog` and `search` focus regions to prevent conflicts with text input.

### Panel Interaction
Each panel has `tabIndex={0}` and `onFocus` handlers to update the focus region. This ensures keyboard navigation works correctly across all three panels.

### Semantic Structure
- Condition rows are `<button>` elements for keyboard accessibility
- Context menus use proper ARIA patterns
- Toast messages use `role="alert"` for screen reader announcement
