import {PGlite} from '@electric-sql/pglite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
for(const file of ['001_memory.sql','002_historical_scope.sql','003_permissions.sql']){
 await db.exec(await readFile('../migrations/'+file,'utf8'));console.log('PASS migration',file);
}
await db.exec("INSERT INTO jarvis.base_assignments VALUES ('891108','CST-PA','Johan','ORLEAN DA SILVA DO NASCIMENTO','2026-11-01','2026-11-08','Fixture isolada');");
await assert.rejects(db.exec("INSERT INTO jarvis.base_assignments VALUES ('891108','CST-PA','Johan','ORLEAN DA SILVA DO NASCIMENTO','2026-11-05','2026-11-10','Fixture isolada');"));
console.log('PASS historical overlap denied');
await db.exec("SET ROLE jarvis_reader");
assert.equal(Number((await db.query('SELECT count(*) FROM jarvis.base_assignments')).rows[0].count),1);
await assert.rejects(db.exec("DELETE FROM jarvis.base_assignments"));
await assert.rejects(db.exec("INSERT INTO jarvis.memories(id) VALUES ('forbidden')"));
await db.exec('RESET ROLE; SET ROLE jarvis_memory;');
await assert.rejects(db.exec('DELETE FROM jarvis.audit'));
await assert.rejects(db.exec('UPDATE jarvis.memory_revisions SET reason=\'tamper\''));
console.log('PASS reader/writer permissions and append-only history');
await db.close();
