# Database Persistence and Deduplication

## Problem Solved

**Issue**: With persistent Docker volumes, running the KG data loader multiple times on the same files would create duplicate papers, nodes, and relations in the database.

**Solution**: Added comprehensive deduplication logic to prevent duplicates while preserving existing data.

## Deduplication Strategy

### 1. Paper Deduplication

- **Check**: Query existing papers by filename before creating
- **Result**: If paper exists, return existing ID instead of creating new one
- **Benefit**: Safe to reload same paper multiple times

### 2. Node Deduplication

- **Check**: Query existing nodes by name, type, and namespace
- **Result**: If node exists, return existing ID instead of creating new one
- **Benefit**: Entities are created once regardless of how many papers mention them

### 3. Relation Deduplication

- **Check**: Query existing relations by subject, predicate, object, and source paper
- **Result**: If relation exists, skip creation entirely
- **Benefit**: Relationships aren't duplicated across multiple loads

## Safe Operations

**Now you can safely:**

- Run batch loading multiple times
- Reload individual papers without duplicates
- Add new papers to existing database
- Restart failed loading processes

## Performance Impact

**Minimal overhead:**

- Each creation operation includes one additional query check
- GraphQL queries are fast (sub-millisecond)
- Prevents exponential growth of duplicate data
- Overall improves long-term database performance

## Usage Examples

```bash
# Safe to run multiple times - no duplicates created
python scripts/batch_load.py --base-dir .

# Safe to reload same file - existing data preserved
python kg_data_loader.py kg_gen_pipeline/output/text_triples/same_paper.json
python kg_data_loader.py kg_gen_pipeline/output/text_triples/same_paper.json  # No duplicates

# Test deduplication is working
python scripts/test_deduplication.py
```

## Key Benefits

1. **Data Integrity**: No accidental duplicates
2. **Safe Re-runs**: Can restart failed processes
3. **Incremental Loading**: Add new papers to existing database
4. **Persistent Volumes**: Full benefit of Docker volume persistence
5. **Development Friendly**: Safe to experiment and iterate

Your database now maintains clean, deduplicated data while preserving all the benefits of persistent storage.
