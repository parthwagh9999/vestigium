"""Verify Phase 1 fixes."""
import sqlite3

conn = sqlite3.connect('vestigium.db')
c = conn.cursor()

print("=== VERIFICATION ===")

c.execute("SELECT id, name, root_entity_id FROM investigations")
print("\nInvestigations with root_entity_id:")
for r in c.fetchall():
    status = "OK" if r[2] else "MISSING"
    print(f"  [{status}] {r[1]}: root={r[2]}")

c.execute("""
SELECT COUNT(*) FROM entities e
WHERE e.is_deleted = 0
AND e.id NOT IN (SELECT source_entity_id FROM entity_relationships WHERE is_deleted=0)
AND e.id NOT IN (SELECT target_entity_id FROM entity_relationships WHERE is_deleted=0)
""")
remaining_orphans = c.fetchone()[0]
print(f"\nRemaining orphan nodes: {remaining_orphans}")

c.execute("SELECT status, COUNT(*) FROM transform_runs GROUP BY status")
print("\nTransform run status:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
print("\nPhase 1 verification complete!")
