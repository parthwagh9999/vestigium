"""Database audit script."""
import sqlite3

conn = sqlite3.connect('vestigium.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = c.fetchall()
print('=== TABLES ===')
for t in tables:
    print(t[0])

# Check investigations with root_entity_id
print('\n=== INVESTIGATIONS ===')
c.execute('SELECT id, name, root_entity_id, status FROM investigations')
for r in c.fetchall():
    print(r)

# Count entities per investigation
print('\n=== ENTITY COUNTS ===')
c.execute('SELECT investigation_id, COUNT(*) FROM entities WHERE is_deleted=0 GROUP BY investigation_id')
for r in c.fetchall():
    print(r)

# Count relationships per investigation
print('\n=== RELATIONSHIP COUNTS ===')
c.execute('SELECT investigation_id, COUNT(*) FROM entity_relationships WHERE is_deleted=0 GROUP BY investigation_id')
for r in c.fetchall():
    print(r)

# Check for orphan nodes (entities with zero relationships)
print('\n=== ORPHAN NODES (no relationships) ===')
c.execute('''
SELECT e.id, e.value, e.entity_type, e.investigation_id
FROM entities e
WHERE e.is_deleted = 0
AND e.id NOT IN (SELECT source_entity_id FROM entity_relationships WHERE is_deleted=0)
AND e.id NOT IN (SELECT target_entity_id FROM entity_relationships WHERE is_deleted=0)
''')
orphans = c.fetchall()
print(f'Total orphan nodes: {len(orphans)}')
for o in orphans[:20]:
    print(f'  {o}')

# Check for duplicate entities
print('\n=== DUPLICATE ENTITIES (same value in same investigation) ===')
c.execute('''
SELECT investigation_id, value, entity_type, COUNT(*) as cnt
FROM entities
WHERE is_deleted = 0
GROUP BY investigation_id, value, entity_type
HAVING cnt > 1
''')
dups = c.fetchall()
print(f'Total duplicate groups: {len(dups)}')
for d in dups[:10]:
    print(f'  {d}')

# Check transform runs
print('\n=== TRANSFORM RUNS ===')
c.execute('SELECT status, COUNT(*) FROM transform_runs GROUP BY status')
for r in c.fetchall():
    print(r)

# Check evidence count
print('\n=== EVIDENCE COUNT ===')
try:
    c.execute('SELECT COUNT(*) FROM evidence')
    print(c.fetchone())
except Exception as e:
    print(f'evidence table error: {e}')

# Check timeline events
print('\n=== TIMELINE EVENTS ===')
try:
    c.execute('SELECT COUNT(*) FROM timeline_events')
    print(c.fetchone())
except Exception as e:
    print(f'timeline_events table error: {e}')

# Check relationships pointing to non-existent entities
print('\n=== BROKEN RELATIONSHIPS (dangling references) ===')
c.execute('''
SELECT r.id, r.source_entity_id, r.target_entity_id, r.relationship_type
FROM entity_relationships r
WHERE r.is_deleted = 0
AND (r.source_entity_id NOT IN (SELECT id FROM entities WHERE is_deleted=0)
     OR r.target_entity_id NOT IN (SELECT id FROM entities WHERE is_deleted=0))
''')
broken = c.fetchall()
print(f'Total broken relationships: {len(broken)}')
for b in broken[:10]:
    print(f'  {b}')

# Check for self-referencing relationships
print('\n=== SELF-REFERENCING RELATIONSHIPS ===')
c.execute('''
SELECT id, source_entity_id, relationship_type
FROM entity_relationships
WHERE source_entity_id = target_entity_id AND is_deleted = 0
''')
selfrefs = c.fetchall()
print(f'Total self-refs: {len(selfrefs)}')

# Root entity check - find first entity per investigation
print('\n=== FIRST ENTITY PER INVESTIGATION (for root recovery) ===')
c.execute('''
SELECT i.id, i.name, i.root_entity_id, 
       (SELECT e.id FROM entities e WHERE e.investigation_id = i.id AND e.is_deleted = 0 ORDER BY e.created_at ASC LIMIT 1) as first_entity_id,
       (SELECT e.value FROM entities e WHERE e.investigation_id = i.id AND e.is_deleted = 0 ORDER BY e.created_at ASC LIMIT 1) as first_entity_value
FROM investigations i
''')
for r in c.fetchall():
    print(f'  inv={r[0][:8]}... name={r[1]} root={r[2]} first_entity={r[3]} first_value={r[4]}')

conn.close()
