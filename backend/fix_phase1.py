"""Phase 1: Fix critical data integrity issues.

1. Backfill root_entity_id for all investigations that have entities but NULL root
2. Fix stuck 'running' transform runs
3. Report orphan analysis
"""
import sqlite3
import datetime

conn = sqlite3.connect('vestigium.db')
c = conn.cursor()

print("=" * 60)
print("PHASE 1: DATA INTEGRITY FIXES")
print("=" * 60)

# 1. Backfill root_entity_id
print("\n--- Backfilling root_entity_id ---")
c.execute("""
SELECT i.id, i.name, 
       (SELECT e.id FROM entities e 
        WHERE e.investigation_id = i.id AND e.is_deleted = 0 
        ORDER BY e.created_at ASC LIMIT 1) as first_entity_id,
       (SELECT e.value FROM entities e 
        WHERE e.investigation_id = i.id AND e.is_deleted = 0 
        ORDER BY e.created_at ASC LIMIT 1) as first_entity_value
FROM investigations i
WHERE i.root_entity_id IS NULL
""")
rows = c.fetchall()
fixed_count = 0
for inv_id, inv_name, first_ent_id, first_ent_val in rows:
    if first_ent_id:
        c.execute("UPDATE investigations SET root_entity_id = ? WHERE id = ?", (first_ent_id, inv_id))
        print(f"  FIXED: {inv_name} -> root_entity_id = {first_ent_id} ({first_ent_val})")
        fixed_count += 1
    else:
        print(f"  SKIP: {inv_name} (no entities)")

print(f"\nBackfilled {fixed_count} investigations")

# 2. Fix stuck 'running' transform runs
print("\n--- Fixing stuck 'running' transform runs ---")
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
c.execute("""
UPDATE transform_runs 
SET status = 'failed', error_message = 'Stuck in running state - auto-cleaned', completed_at = ?
WHERE status = 'running'
""", (now,))
stuck_count = c.rowcount
print(f"  Fixed {stuck_count} stuck transform runs")

# 3. Fix orphan nodes - create missing relationships
print("\n--- Analyzing orphan nodes for relationship repair ---")
c.execute("""
SELECT e.id, e.value, e.entity_type, e.investigation_id, e.source
FROM entities e
WHERE e.is_deleted = 0
AND e.id NOT IN (SELECT source_entity_id FROM entity_relationships WHERE is_deleted=0)
AND e.id NOT IN (SELECT target_entity_id FROM entity_relationships WHERE is_deleted=0)
""")
orphans = c.fetchall()
print(f"  Found {len(orphans)} orphan nodes")

# For orphans, try to connect them to the root entity of their investigation
import uuid
orphans_fixed = 0
for ent_id, ent_val, ent_type, inv_id, source in orphans:
    # Get root entity for this investigation
    c.execute("SELECT root_entity_id FROM investigations WHERE id = ?", (inv_id,))
    root_row = c.fetchone()
    root_id = root_row[0] if root_row else None
    
    if root_id and root_id != ent_id:
        # Determine relationship type based on entity type
        rel_type_map = {
            'ip_address': 'resolves_to',
            'country': 'located_in',
            'city': 'located_in',
            'organization': 'registered_to',
            'service': 'uses',
            'domain': 'related_to',
            'subdomain': 'related_to',
        }
        rel_type = rel_type_map.get(ent_type, 'related_to')
        
        # Check if relationship already exists
        c.execute("""
        SELECT id FROM entity_relationships 
        WHERE investigation_id = ? AND source_entity_id = ? AND target_entity_id = ? AND relationship_type = ?
        AND is_deleted = 0
        """, (inv_id, root_id, ent_id, rel_type))
        
        if not c.fetchone():
            # For IP addresses, check if there's a better parent (another IP that was connected)
            # For now, connect to root as a reasonable default
            
            # But wait - for the Test Google investigation, orphan IPs should connect to google.com
            # For geolocation entities, they should connect to the IP that discovered them
            # Since we can't reconstruct the exact parent, connect to root
            
            rel_id = str(uuid.uuid4())
            now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # For geo entities (country, city), find the IP that might have discovered them
            parent_id = root_id
            if ent_type in ('country', 'city', 'organization'):
                # Check transform_results for a clue about which transform created this entity
                c.execute("""
                SELECT tr.input_entity_id FROM transform_runs tr
                JOIN transform_results tres ON tres.transform_run_id = tr.id
                WHERE tres.entity_id = ? AND tr.investigation_id = ?
                LIMIT 1
                """, (ent_id, inv_id))
                tr_row = c.fetchone()
                if tr_row:
                    parent_id = tr_row[0]
            
            c.execute("""
            INSERT INTO entity_relationships (id, investigation_id, source_entity_id, target_entity_id, 
                relationship_type, label, weight, confidence, source, is_bidirectional, is_deleted, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1.0, 0.8, 'Orphan recovery', 0, 0, ?, ?)
            """, (rel_id, inv_id, parent_id, ent_id, rel_type, rel_type.replace('_', ' '), now_str, now_str))
            orphans_fixed += 1
            print(f"  CONNECTED: {ent_val} ({ent_type}) -> parent {parent_id[:8]}... via '{rel_type}'")

print(f"\n  Fixed {orphans_fixed} orphan nodes")

conn.commit()

# Verify
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

c.execute("SELECT id, name, root_entity_id FROM investigations")
print("\nInvestigations with root_entity_id:")
for r in c.fetchall():
    status = "✅" if r[2] else "❌"
    print(f"  {status} {r[1]}: root={r[2]}")

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
print("\n✅ Phase 1 complete!")
