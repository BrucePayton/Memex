# Platform Feature Completion & Wiki Dashboard Enhancement

## Session Overview
Date: 2026-05-09
Context: Continuing from previous session that fixed 5 platform issues (Wiki 404, domain config/provider routing, notification center, external resources tab, Claw Code panel). This session focused on completing the Wiki Dashboard's Memex-style interface and writing the platform fix code to the repository.

## Part 1: Wiki Dashboard Feature Completion

### Background
The Wiki Dashboard (`web/src/features/wiki-dashboard/`) is a Memex-style full-screen UI for the Wiki knowledge base. It was introduced as a replacement for `WikiManagementPage`'s inline content, but only 7 of ~25 view types had real implementations — the rest showed "coming soon" placeholders.

### Architecture
- Route: `/wiki` → `WikiManagementPage` (thin shell) → `WikiDashboardLayout`
- Layout: Header (stats bar) → Body (Sidebar + Main(Toolbar + Content))
- DashboardViews is a switch on `ViewType` that renders the appropriate component
- All views follow `ViewPanel` pattern: `max-w-[820px] mx-auto px-11 py-9`

### Previously Implemented Views (7)
- SearchView (full-text search), GraphView (knowledge graph), LintView (health checks), ReflectView (meta-analysis), ProvenanceView (citation coverage), SettingsView (external service status), BrowsePlaceholder (stub)

### New Views Implemented (12)

**BrowseView** (`BrowseView.tsx`)
- Two modes: Folder mode (page list via `getFolderPages()`) and Page mode (single page content via `getPage()`)
- States: no-folder-selected (decorative icon + prompt), loading (spinner), empty (folder has no pages), error (retry button), data (page list with title + preview + tags)
- Page viewer: back button, title, word count, creation/update dates, tags, content rendered as pre-formatted text

**HealthView** (`HealthView.tsx`)
- Auto-loads `getWikiHealth()` on mount
- Displays composite health score with color coding (green >= 0.8, orange >= 0.5, red < 0.5)
- Lists individual health items with pass/warn/fail icons
- Manual refresh button

**RawView** (`RawView.tsx`)
- Reuses existing `WikiRawSourcesTab` component (~20 lines)
- Handles all loading, filtering, and error states internally

**HistoryView** (`HistoryView.tsx`)
- Calls `getWikiLogs(200)` for full activity history
- Entity type filter dropdown (all/pages/folders/raw sources)
- Log entries with timestamp, action badge (color-coded), entity name, type
- Manual refresh button

**LogsView** (`LogsView.tsx`)
- System audit trail using `getWikiLogs(200)`
- Same rendering pattern as HistoryView
- Manual refresh button

**QueryView** (`QueryView.tsx`)
- Inline QA interface (adapted from `WikiQueryDialog`)
- Text input + submit button, answer display, citations as cards
- States: initial (prompt with icon), loading, error, results (answer + references)
- Uses new API wrapper: `wikiQuery()`

**ReviewView** (`ReviewView.tsx`)
- Reuses existing `WikiStaleReviewTab` component (~20 lines)
- Handles days input, stale page review trigger, and results internally

**CompareView** (`CompareView.tsx`)
- Reuses existing `WikiCompareTab` component (~20 lines)
- Handles page selection and comparison internally

**WriteView** (`WriteView.tsx`)
- Lightweight inline page editor
- Title input, folder selector (from `getFolderTree()`), tags (comma-separated), `WikiMarkdownEditor` component
- Save button calls `createPage()`, navigates to `/wiki` on success
- Loading state for folder fetching, saving state with disabled button

**IngestView** (`IngestView.tsx`)
- Compact ingest form adapted from `WikiIngestPage`
- Source text textarea, source name input, folder selector, tags input, auto-split toggle
- Preview button calls `wikiIngestPreview()`, Ingest button calls `wikiIngest()`
- States: input (form), preview (parsed pages), loading, result (success with created pages list), error
- Uses new API wrappers: `wikiIngestPreview()`, `wikiIngest()`

**SchemaView** (`SchemaView.tsx`)
- Static reference view — no API calls
- Sections: Frontmatter fields (title, type, tags, sources, citation format), Page types (source, entity, concept, technique, analysis, source-summary), Citation format (`[^src-1]` markers), Folder structure
- Styled as structured document with code blocks

**GuideView** (`GuideView.tsx`)
- Static in-app usage guide — no API calls
- Sections: Sidebar (Tree/Pages/Log/Raw), Toolbar (Work/Analyze/Browse/Create/More categories), Creating Content (+Folder/+Page), Keyboard Shortcuts
- Color-coded category sections (blue sidebar, green toolbar, purple creating)

### DashboardViews.tsx Updates
- Imported and rendered all 12 new views
- Added case handlers for 'write', 'compare', 'raw', 'history', 'schema', 'logs'
- Updated interface: removed unused props (`currentPageFilename`, `searchQuery`, `onSetBreadcrumb`), added `onSelectPage`, `onSelectFolder`
- Default case now renders BrowseView instead of BrowsePlaceholder
- All 25+ `ViewType` members are properly handled

### WikiDashboardLayout.tsx Updates
- Updated to pass new props: `onSelectPage`, `onSelectFolder` to DashboardViews
- Removed unused prop passes: `currentPageFilename`, `searchQuery`

### API Wrappers Added
5 new functions in `web/src/apis/wiki/index.ts`:
- `wikiQuery()` → `POST /api/wiki/query` — QA against wiki content
- `wikiIngest()` → `POST /api/wiki/ingest` — Import source text
- `wikiIngestPreview()` → `POST /api/wiki/ingest/preview` — Preview before ingest
- `wikiStaleReview()` → `POST /api/wiki/stale-review` — Find stale pages
- `wikiComparePages()` → `POST /api/wiki/pages/compare` — Compare two pages

### SettingsView — Execution Mode Selector
- Replaced "Configuration management coming soon" placeholder
- Added "Execution Mode" section with segmented toggle: **LLM** | **Claw Code**
- Preference stored in `localStorage` key `wiki-execution-mode` (default: `"llm"`)
- Dynamic summary text explaining each mode
- "Configure LLM Providers" button → `/llm-config`, "Configure Claw Code" button → `/claw`
- Pattern matches the existing External Services section

## Part 2: Platform Issues Fixed (Previous Session — Committed This Session)

### Fix 1: Wiki KB Binding 404
- **Root Cause**: Frontend API base path `/wiki` was not in `DIRECT_UNDER_API_PREFIXES` in `resolveApiEndpointPath()`, causing requests to route to `/api/wp/wiki/...` instead of `/api/wiki/...`.
- **Fix**: Added `'/wiki'` to `DIRECT_UNDER_API_PREFIXES` in `web/src/shared/api/client.ts`

### Fix 2: Domain Config & Provider Routes Not Mounted (P0)
- **Root Cause**: `domain_config_views.router` and `provider_views.router` existed in `core/modules/config/views/` but were never imported/mounted in `manage.py`'s `mount_routers()`. All API calls to `/api/config/domains/*` and `/api/config/providers/*` returned 404.
- **Fix**: Added imports and `(domain_config_router, None, None)` / `(provider_router, None, None)` to routers list in `manage.py`

### Fix 3: Claw Dashboard Back Navigation
- **Problem**: Hard-coded `navigate(ROUTES.PLATFORM_CONFIG)` regardless of entry point
- **Fix**: Changed to `window.history.length > 2 ? navigate(-1) : navigate(ROUTES.HOME)` (smart back)

### Fix 4: Static Domain Templates Removed → Dynamic Aggregation
- Removed 4 hardcoded builtin templates from `core/modules/chain_template/builtin_templates.py`
- Removed `seed_builtin_templates()` call from `manage.py` initialization
- Added `POST /api/chain-template/aggregate-from-snapshots` endpoint
- Frontend: removed builtin template cards, added "从快照聚合" (Aggregate from Snapshots) button and dialog

### Fix 5: External Resources Tab Layout
- Complete rewrite from card-based to Tabs layout
- "外部资源" Tab: unified table with kind filter, search, CRUD
- "平台管理" Tab: PlatformRegistration CRUD + resource discovery

### Fix 6: Claw Code Config Panel
- Platform config page added Claw Code entry card
- Claw Dashboard added "配置" (Config) Tab: ANTHROPIC_BASE_URL, AUTH_TOKEN, MODEL fields
- Backend: `POST /api/claw/config` (save to `.claw.json`) and `POST /api/claw/test-connection` endpoints
- Frontend: `saveConfig()` and `testConnection()` API methods

### Fix 7: Notification Center Enabled
- Added event-driven notification creation at key system events:
  - Chain snapshot creation → "task" type notification
  - Data source status change → "system" type notification
  - Wiki knowledge base sync completion → "task" type notification (success/error)
  - Service startup → welcome notification for admin users
- Used `NotificationService.create_notification()` existing service class
- All notification creation is wrapped in try/catch (non-fatal)

## Commit History
4 commits on `backup/dev_bruce_askdata`:
1. `db211183` — fix: routing fixes + template refactor
2. `ca6a740d` — feat: notification center + wiki enhancements
3. `239ef7de` — feat: external resources tab refactor
4. `eae5a353` — feat: claw code config panel
5. `c9e477bb` — feat: wiki dashboard completion (this session)

## Technical Details

### Key Files Modified (this session)
| File | Change |
|------|--------|
| `web/src/apis/wiki/index.ts` | +5 API wrappers |
| `web/src/features/wiki-dashboard/views/DashboardViews.tsx` | Full rewrite — all views wired |
| `web/src/features/wiki-dashboard/views/SettingsView.tsx` | +Execution mode selector |
| `web/src/features/wiki-dashboard/layout/WikiDashboardLayout.tsx` | Updated props |

### New Files Created (12 views)
All under `web/src/features/wiki-dashboard/views/`:
BrowseView, HealthView, RawView, HistoryView, LogsView, QueryView, ReviewView, CompareView, WriteView, IngestView, SchemaView, GuideView

### Reusable Components Used
| Component | View | Location |
|-----------|------|----------|
| WikiRawSourcesTab | RawView | `wiki/components/WikiRawSourcesTab.tsx` |
| WikiStaleReviewTab | ReviewView | `wiki/components/WikiStaleReviewTab.tsx` |
| WikiCompareTab | CompareView | `wiki/components/WikiCompareTab.tsx` |
| WikiMarkdownEditor | WriteView | `wiki/components/WikiMarkdownEditor.tsx` |
| ViewPanel | All views | `wiki-dashboard/views/ViewPanel.tsx` |
