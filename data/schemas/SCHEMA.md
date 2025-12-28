# Board cache schema

The `BoardDatabase` Room cache stores board metadata along with a queue of boards waiting to be synced.

## Versions

- **v1** – Introduced the `boards` table for cached board metadata.
- **v2** – Added the `pending_sync` table to track boards awaiting upload. Migration `MIGRATION_1_2` creates the table without modifying existing data.

## Tables

### `boards`
- `id` (`TEXT`, PK)
- `name` (`TEXT`)
- `updated_at` (`TEXT` ISO-8601 timestamp)
- `attachments_version` (`INTEGER` monotonically increasing attachment state counter)

### `pending_sync`
- `id` (`TEXT`, PK)
- `name` (`TEXT`)
- `updated_at` (`TEXT` ISO-8601 timestamp)
- `attachments_version` (`INTEGER` counter aligned with the board attachments state)
- `enqueued_at` (`INTEGER` UTC epoch millis, used for FIFO ordering)

## Migrations
- `MIGRATION_1_2` – Creates the `pending_sync` table while leaving existing `boards` rows untouched.

## Backup/restore
`BoardDatabaseProvider` exposes `backup` and `restore` helpers. Backups force a WAL checkpoint to keep snapshots consistent before copying the file. Restores recreate the database directory if needed and replace the existing database file with the provided backup.
