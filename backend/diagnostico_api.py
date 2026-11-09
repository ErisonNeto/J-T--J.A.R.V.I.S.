"""Read-only diagnostics. Does not print credentials or operational rows."""
from jarvis.config import Settings
from sqlalchemy import create_engine, text
import httpx

s = Settings()
s.validate()
print('Memoria:', 'PostgreSQL' if s.memory_url.startswith('postgresql') else 'SQLite local')
print('Modelo configurado:', s.model)
print('Indicadores aprovados:', s.approved or 'nenhum (validacao pendente)')
with create_engine(s.memory_url).connect() as connection:
    connection.execute(text('SELECT 1'))
print('Memoria: conexao OK')
if s.jt_api_url:
    for title, sql in [
        ('JT API', 'SELECT 1'),
        ('Gestao historica', 'SELECT COUNT(*) FROM jarvis.base_assignments'),
    ]:
        try:
            response = httpx.post(s.jt_api_url + '/query', headers={'X-API-Key': s.jt_api_key}, json={'sql': sql, 'params': []}, timeout=s.jt_api_timeout, follow_redirects=False)
            print(title + ': HTTP ' + str(response.status_code))
            if response.is_success:
                rows = response.json().get('rows')
                if title == 'Gestao historica' and rows:
                    print('Vinculos historicos cadastrados:', rows[0][0])
        except Exception as exc:
            print(title + ': falha de conexao (' + type(exc).__name__ + ')')
