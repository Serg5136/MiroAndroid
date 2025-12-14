# Android Porting Assessment

## Key dependencies
- **Runtime/UI:** Standard library Python 3.10+ with Tkinter widgets and dialogs for the full UI flow (canvas, sidebar, dialogs).【F:README.md†L3-L186】【F:src/main.py†L1-L20】
- **Imaging:** Pillow is required for PNG export of the board and image attachments.【F:README.md†L108-L116】【F:requirements.txt†L1-L1】
- **Persistence:** Uses the Python standard library (`json`, `os`, `pathlib`) to store/load board state and autosave files on local disk.【F:src/autosave.py†L5-L27】【F:src/files.py†L1-L20】

## Codebase layout reviewed
- `src/`: core application modules (UI layout, models, controllers, file I/O, history, tooltips).【F:Architectory.md†L3-L18】
- `tests/`: pytest suite covering models, history, grid/rounded connections, sidebar file menu, attachments, and routes.【F:Architectory.md†L20-L29】
- Top-level assets include example attachments, autosave sample, and saved boards for reference.【F:Architectory.md†L31-L39】

## Android platform targets
- **Minimum/target API level:** Not specified in the repository; current code is desktop Python/Tkinter and would need a reimplementation for Android.
- **Supported ABIs:** No Android build configuration exists, so architectures (armeabi-v7a, arm64-v8a, x86_64) are not yet defined.

## Platform feature mapping
- **UI toolkit:** Tkinter canvases, dialogs, and menus would need replacements with Android UI (Views/Compose) and equivalent gestures for drag/zoom/selection.
- **File system access:** Direct reads/writes of JSON and attachment PNG/JPEG files on local disk should be mapped to scoped storage or app-specific directories via Android storage APIs.【F:src/autosave.py†L14-L27】【F:src/files.py†L12-L42】
- **Image handling:** Pillow-based PNG export/processing should be replaced with Android Bitmap/Canvas utilities or third-party imaging libs.
- **Dialogs & clipboard:** Tkinter file/clipboard interactions (e.g., `filedialog`, copy/paste) require Android equivalents such as Storage Access Framework and ClipboardManager.【F:src/main.py†L1-L32】
- **Background/periodic work:** Autosave currently does synchronous file writes; on Android this would map to background tasks (e.g., WorkManager) to persist board state without blocking the UI.【F:src/autosave.py†L17-L27】
- **Networking/IPC:** The app is intentionally offline and does not use networking or external IPC, simplifying the port (no replacement network stack needed).【F:README.md†L3-L6】

## Android architecture and modularization choices
- **UI architecture:** Adopt **MVVM** with unidirectional data flow to keep UI state consistent across board canvas, toolbar, and dialogs. ViewModels expose `StateFlow`/`LiveData` for board data, selection state, and undo/redo availability while delegating commands to the domain layer.
- **Dependency injection:** Use **Hilt** for scoped dependencies (application, activity, and viewmodel scopes). Hilt handles WorkManager integration via `@HiltWorker`, simplifies ViewModel creation for navigation destinations, and enables easy swapping of storage/serialization implementations for testing.
- **Modules:**
  - `:core`: UI theme resources, design system components, common utilities (logging, result wrappers), permission helpers, and base navigation/DI setup shared across modules.
  - `:domain`: Pure Kotlin business logic—board entities, use cases (e.g., add card, connect nodes, autosave, export), validation, and undo/redo command abstractions. No Android dependencies.
  - `:data`: Repositories for board persistence (JSON serialization, attachments storage), autosave scheduler contracts, and mappers between storage DTOs and domain models. Includes WorkManager enqueue helpers and optional native bridges for image export if required.
  - `:app`: Android UI (Compose/Views), navigation graph, ViewModels, Hilt modules, and WorkManager workers. Depends on `:domain`, `:data`, and `:core`.
  - **Native extensions (optional):** Separate modules like `:native:image` for image processing or export acceleration using NDK/RenderScript replacements when Pillow-specific features need parity.

## Platform strategies
- **Permissions:** Centralize permission prompts in `:core` via a composable/utility that wraps `ActivityResultContracts.RequestPermission(s)`. Storage (scoped/MediaStore) and notification permissions (for foreground service status) are requested contextually with rationale dialogs. ViewModels expose permission intents; UI triggers requests and reports results back, keeping business logic permission-free.
- **Navigation:** Use **Jetpack Navigation** (preferably with the Compose integration) to structure main board, attachments picker, settings, and export flows. Graph destinations bind their ViewModels with Hilt; navigation arguments carry board IDs or attachment URIs. Deep links can restore specific boards from autosave files.
- **Background tasks:**
  - **WorkManager** schedules periodic autosave mirroring the Tkinter autosave cadence and one-off export or large attachment processing jobs. Workers use `setExpedited` when needed and share repositories injected by Hilt.
  - **Foreground service** reserved for long-running export or bulk image import operations where user-visible progress is required. Service APIs surface `Notification` channels and report progress back to ViewModels via shared flows.
