import {PGlite} from '@electric-sql/pglite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
await db.exec(await readFile('../migrations/001_memory.sql','utf8'));
await db.exec(await readFile('../migrations/002_historical_scope.sql','utf8'));
await db.exec(`
CREATE TABLE entregas(data_sla date,codigo_base text,no_prazo boolean);
CREATE TABLE t0_diario(data date,codigo_base text,t0_ok integer,total_pedidos integer);
CREATE TABLE capotamento_diario(data date,codigo_base text,status_risco text);
CREATE TABLE shipping_time_diario(data date,codigo_base text,etapa_6_h numeric,etapa_7_h numeric,etapa_8_h numeric,pacotes integer);
CREATE TABLE sem_mov_retidos_detalhe(data date,base_codigo text,aging_valor integer,pedidos integer,indicador text);
CREATE TABLE jt_1bd_gestao(base_chave text,codigo text);
CREATE TABLE jt_1bd_registros(data_avaliacao text,base_chave text,entregue integer);
CREATE TABLE jt_5cd_registros(data_relatorio text,base_chave text);
CREATE TABLE jt_arbitragem_ocorrencias(fechada_em text,codigo_base text,valor_centavos bigint,tipo text,status text);
INSERT INTO jarvis.base_assignments VALUES ('1','Base teste','Gestor teste','ORLEAN DA SILVA DO NASCIMENTO','2026-11-01','2026-11-08','Fixture isolada'),('2','Outra regional','Outro','OUTRO RM','2026-11-01','2026-11-08','Fixture isolada');
INSERT INTO entregas VALUES ('2026-11-02','1',true),('2026-11-02','1',false),('2026-11-02','2',true),('2026-10-31','1',true);
INSERT INTO t0_diario VALUES ('2026-11-02','1',8,10);
INSERT INTO capotamento_diario VALUES ('2026-11-02','1','CAPOTADA');
INSERT INTO shipping_time_diario VALUES ('2026-11-02','1',2,3,4,10),('2026-11-02','1',NULL,3,4,10);
INSERT INTO sem_mov_retidos_detalhe VALUES ('2026-11-02','1',11,10,'sem_mov'),('2026-11-02','1',4,7,'sem_mov'),('2026-11-02','1',3,9,'sem_mov'),('2026-11-02','1',12,5,'retidos');
INSERT INTO jt_1bd_gestao VALUES ('BASE','1');
INSERT INTO jt_1bd_registros VALUES ('2026-11-02','BASE',1),('2026-11-02','BASE',0);
INSERT INTO jt_5cd_registros VALUES ('2026-11-02','BASE'),('2026-11-02','BASE');
INSERT INTO jt_arbitragem_ocorrencias VALUES ('2026-11-02','1',12345,'Avaria','PROCESSO ENCERRADO'),('2026-11-02','1',99999,'Avaria','Revogado'),('2026-11-02','1',23456,'Extravio','ARBITRAGEM FINALIZADA'),('2026-11-02','1',34567,'PNR','PROCESSO ENCERRADO');
`);
const queries=JSON.parse(await readFile('queries.json','utf8'));
const expected={sla:[1,2],t0:[8,10],capotamento:[1,1],shipping:[90,10],sem_mov:[17,10],retidos:[5,5],'1bd':[1,2],'5cd':[2,2],avaria:[12345,1],extravio:[23456,1],pnr:[34567,1]};
for(const [kind,{sql,params}] of Object.entries(queries)){
 const keys=[];const query=sql.replace(/(?<!:):(\w+)/g,(_,k)=>{if(!keys.includes(k))keys.push(k);return '$'+(keys.indexOf(k)+1)});
 const r=await db.query(query,keys.map(k=>params[k]));assert.equal(r.rows.length,1,kind);
 assert.equal(Number(r.rows[0].numerator),expected[kind][0],kind+' numerator');
 assert.equal(Number(r.rows[0].denominator),expected[kind][1],kind+' denominator');
 assert.equal(r.rows[0].base_code,'1');console.log('PASS actual adapter SQL',kind);
}
await db.close();
