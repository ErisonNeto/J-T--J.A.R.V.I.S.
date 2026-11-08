"""Fixed SQL only. Historical scope is defined by reviewed base_assignments."""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from .periods import default_period, comparisons, today

SPECS = {
    "sla": (
        "public.entregas r",
        "r.data_sla",
        "r.codigo_base",
        "CASE WHEN r.no_prazo THEN 1 ELSE 0 END",
        "1",
        "%",
        "ratio",
        True,
    ),
    "t0": (
        "public.t0_diario r",
        "r.data",
        "r.codigo_base",
        "r.t0_ok",
        "r.total_pedidos",
        "%",
        "ratio",
        True,
    ),
    "capotamento": (
        "public.capotamento_diario r",
        "r.data",
        "r.codigo_base",
        "CASE WHEN UPPER(TRIM(r.status_risco)) IN ('ALERTA','CAPOTADA') THEN 1 ELSE 0 END",
        "1",
        "%",
        "ratio",
        False,
    ),
    "shipping": (
        "public.shipping_time_diario r",
        "r.data",
        "r.codigo_base",
        "(r.etapa_6_h+r.etapa_7_h+r.etapa_8_h)*r.pacotes",
        "r.pacotes",
        "h",
        "weighted",
        False,
    ),
    "sem_mov": (
        "public.sem_mov_retidos_detalhe r",
        "r.data",
        "r.base_codigo",
        "CASE WHEN r.aging_valor>3 THEN r.pedidos ELSE 0 END",
        "CASE WHEN r.aging_valor>10 THEN r.pedidos ELSE 0 END",
        "pacotes-dia",
        "sum",
        False,
    ),
    "retidos": (
        "public.sem_mov_retidos_detalhe r",
        "r.data",
        "r.base_codigo",
        "CASE WHEN r.aging_valor>3 THEN r.pedidos ELSE 0 END",
        "CASE WHEN r.aging_valor>10 THEN r.pedidos ELSE 0 END",
        "pacotes-dia",
        "sum",
        False,
    ),
    "1bd": (
        "public.jt_1bd_registros r JOIN public.jt_1bd_gestao g ON g.base_chave=r.base_chave",
        "r.data_avaliacao",
        "g.codigo",
        "r.entregue",
        "1",
        "%",
        "ratio",
        True,
    ),
    "5cd": (
        "public.jt_5cd_registros r JOIN public.jt_1bd_gestao g ON g.base_chave=r.base_chave",
        "r.data_relatorio",
        "g.codigo",
        "1",
        "1",
        "remessas/dia",
        "daily_mean",
        False,
    ),
}
for key in ("avaria", "extravio", "pnr"):
    SPECS[key] = (
        "public.jt_arbitragem_ocorrencias r",
        "CAST(r.fechada_em AS date)",
        "r.codigo_base",
        "r.valor_centavos",
        "1",
        "R$",
        "money",
        False,
    )


class Unavailable(Exception):
    pass


class Operations:
    def __init__(self, settings):
        self.settings = settings
        self.engine = (
            create_engine(
                settings.operational_url,
                pool_size=2,
                max_overflow=1,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 8},
            )
            if settings.operational_url
            else None
        )

    def catalog(self):
        return [
            {
                "id": k,
                "enabled": bool(self.engine and k in self.settings.approved.split(",")),
                "unit": s[5],
                "approval_required": True,
            }
            for k, s in SPECS.items()
        ] + [
            {
                "id": "csat",
                "enabled": False,
                "reason": "Fonte e fórmula não identificadas nos repositórios.",
            }
        ]

    def rows(self, kind, start, end, base=None, manager=None):
        if kind not in SPECS:
            raise Unavailable("Indicador sem fonte validada: " + kind)
        if not self.engine:
            raise Unavailable(
                "PostgreSQL operacional não configurado ou Predator desconectado."
            )
        if kind not in self.settings.approved.split(","):
            raise Unavailable(
                "Indicador aguarda validação do esquema e da gestão histórica: " + kind
            )
        table, day, code, num, den, *_ = SPECS[kind]
        extra = ""
        if kind in {"sem_mov", "retidos"}:
            extra = " AND r.indicador=:kind"
        if kind in {"avaria", "extravio", "pnr"}:
            extra = " AND r.tipo=:claim AND UPPER(TRIM(r.status)) IN ('PROCESSO ENCERRADO','ARBITRAGEM FINALIZADA')"
        # NULL stage times must not silently become zero.
        if kind == "shipping":
            extra = " AND r.etapa_6_h IS NOT NULL AND r.etapa_7_h IS NOT NULL AND r.etapa_8_h IS NOT NULL"
        sql = f"""SELECT CAST({day} AS date) AS day,a.base_code,a.base_name,a.manager,
           SUM({num}) AS numerator,SUM({den}) AS denominator
           FROM {table} JOIN jarvis.base_assignments a
           ON a.base_code=CAST({code} AS text)
           AND CAST({day} AS date)>=a.valid_from AND CAST({day} AS date)<=a.valid_to
           WHERE a.regional=:rm AND CAST({day} AS date) BETWEEN :start AND :end
           AND (CAST(:base AS text) IS NULL OR a.base_code=:base)
           AND (CAST(:manager AS text) IS NULL OR a.manager=:manager) {extra}
           GROUP BY CAST({day} AS date),a.base_code,a.base_name,a.manager
           ORDER BY 1,2 LIMIT 20001"""
        try:
            with self.engine.connect() as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    c.execute(text("SET LOCAL statement_timeout='12000ms'"))
                    rows = [
                        dict(r)
                        for r in c.execute(
                            text(sql),
                            dict(
                                rm=self.settings.rm,
                                start=start,
                                end=end,
                                base=base,
                                manager=manager,
                                kind=kind,
                                claim={
                                    "avaria": "Avaria",
                                    "extravio": "Extravio",
                                    "pnr": "PNR",
                                }.get(kind),
                            ),
                        ).mappings()
                    ]
            if len(rows) > 20000:
                raise Unavailable("Consulta excede o limite. Reduza o período.")
            return rows
        except Unavailable:
            raise
        except Exception as e:
            raise Unavailable(
                "Falha na leitura: confira disponibilidade, permissões e diagnóstico do esquema."
            ) from e

    def analyze(self, filters):
        start, end = (
            (filters.start, filters.end)
            if filters.start
            else default_period(filters.indicator)
        )
        ranges = {"current": (start, end), **comparisons(start, end)}
        allrows = self.rows(
            filters.indicator,
            min(a for a, b in ranges.values()),
            max(b for a, b in ranges.values()),
            filters.base_code,
            filters.manager,
        )
        result = {
            "indicator": filters.indicator,
            "period": {"start": str(start), "end": str(end)},
            "unit": SPECS[filters.indicator][5],
            "sources": [
                {
                    "title": SPECS[filters.indicator][0],
                    "type": "PostgreSQL somente leitura",
                }
            ],
            "warnings": [
                "Recorte restrito às bases com gestão histórica validada. Cobertura de dias não comprova completude dos relatórios."
            ],
            "comparisons": {},
        }
        if filters.indicator == "shipping":
            result["warnings"].append(
                "Registros com alguma etapa nula são excluídos; valide a completude na origem."
            )
        for name, (a, b) in ranges.items():
            chosen = [r for r in allrows if a <= r["day"] <= b]
            value = aggregate(chosen, filters.indicator)
            value.update(
                start=str(a),
                end=str(b),
                expected_days=max(0, (min(b, today()) - a).days + 1),
            )
            if name == "current":
                result.update(value)
            else:
                result["comparisons"][name] = value
        groups = defaultdict(list)
        daily = defaultdict(list)
        for r in allrows:
            if start <= r["day"] <= end:
                groups[(r["base_code"], r["base_name"], r["manager"])].append(r)
                daily[str(r["day"])].append(r)
        result["ranking"] = [
            dict(
                base_code=k[0],
                base_name=k[1],
                manager=k[2],
                **aggregate(v, filters.indicator),
            )
            for k, v in groups.items()
        ]
        higher = SPECS[filters.indicator][7]
        result["ranking"].sort(
            key=lambda r: (
                r["value"] is None,
                (r["value"] or 0) * (1 if higher else -1),
            )
        )
        result["series"] = [
            dict(day=k, **aggregate(v, filters.indicator))
            for k, v in sorted(daily.items())
        ]
        result["latest_in_period"] = max(daily, default=None)
        if not daily:
            result["warnings"].append(
                "Sem dados ou sem gestão histórica validada para o recorte."
            )
        elif max(daily) < str(min(end, today())):
            result["warnings"].append(
                "Última data disponível no recorte anterior à data final."
            )
        for c in result["comparisons"].values():
            c["delta"] = (
                None
                if result["value"] is None or c["value"] is None
                else round(result["value"] - c["value"], 6)
            )
            c["delta_unit"] = "p.p." if result["unit"] == "%" else result["unit"]
        return result


def aggregate(rows, kind):
    n = sum((Decimal(str(r["numerator"] or 0)) for r in rows), Decimal(0))
    d = sum((Decimal(str(r["denominator"] or 0)) for r in rows), Decimal(0))
    days = len({r["day"] for r in rows})
    mode = SPECS[kind][6]
    v = None
    if days:
        if mode in {"ratio", "weighted"}:
            v = n / d * (100 if mode == "ratio" else 1) if d else None
        elif mode == "daily_mean":
            v = n / days
        elif mode == "money":
            v = n / 100
        else:
            v = n
    return {
        "value": float(v) if v is not None else None,
        "numerator": str(n),
        "denominator": str(d),
        "days": days,
        **({"above_10": float(d)} if kind in {"sem_mov", "retidos"} else {}),
    }
