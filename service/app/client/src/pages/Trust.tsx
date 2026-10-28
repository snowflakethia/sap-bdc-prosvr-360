import { Card, Grid, Kpi, PageFrame, Table, WithData, fmt, usePage } from '@/components/ui';

export default function Trust() {
  const q = usePage('trust');
  return (
    <PageFrame id="P9" title="Data Trust" subtitle="Freshness and completeness of the data behind every number, the automated checkpoint gates, and the fee-boundary evidence.">
      <WithData q={q}>
        {(d) => {
          const latest = Object.values(d.tr_checks.reduce((a: Record<string, any>, r) => ((a[r.checkpoint] = a[r.checkpoint] ?? { cp: r.checkpoint, pass: 0, n: 0, at: r.run_at }), a[r.checkpoint].n++, r.result === 'PASS' && a[r.checkpoint].pass++, a), {}));
          const writes = d.tr_access[0];
          return (
            <>
              <Grid cols={4}>
                <Kpi label="Gates passing" info="gates" value={`${latest.filter((g: any) => g.pass === g.n).length} / ${latest.length}`} sub="latest run of each checkpoint gate" tone="good" />
                <Kpi label="Checks passing" info="checks" value={`${d.tr_checks.filter((r) => r.result === 'PASS').length} / ${d.tr_checks.length}`} />
                <Kpi label="Keys with nulls" info="key_nulls" value={String(d.tr_completeness.filter((r) => Number(r.null_pct) > 0).length)} sub={`of ${d.tr_completeness.length} conformed key columns`} />
                <Kpi label={String(writes?.check_name ?? 'Writes to CLDs').replace(/_/g, ' ')} value={fmt.text(writes?.value)} sub="from ACCESS_HISTORY snapshot" tone={Number(writes?.value) === 0 ? 'good' : 'bad'} />
              </Grid>
              <Card title="Fee boundary" info="fee_boundary" subtitle="How the app is kept on the governed side">
                <p className="text-sm text-gray-600">
                  Every app statement runs with <code>QUERY_TAG = 'ACOCO_APP'</code> and reads only <code>ACOCO_L2.SERVING</code>, <code>SEMANTIC</code> and <code>ONTOLOGY</code>
                  (linted in <code>tools/lint_app.py</code>). With a single <code>ACCOUNTADMIN</code> role grants cannot enforce it, so it is <b>evidenced</b>: <code>ACCESS_HISTORY</code>
                  for tag <code>ACOCO_APP</code> lists only those schemas and the L2 tables beneath them - never a CLD, <code>ACOCO_SIM</code> or <code>ACOCO_L1</code> directly.
                </p>
              </Card>
              <Grid cols={2}>
                <Card title="Freshness" info="freshness" subtitle="Date coverage of the key facts by source">
                  <Table rows={d.tr_freshness} cols={[
                    { key: 'object_name', label: 'Object' }, { key: 'date_column', label: 'Date column' }, { key: 'source_system', label: 'Source' },
                    { key: 'min_date', label: 'From', format: fmt.date }, { key: 'max_date', label: 'To', format: fmt.date },
                  ]} />
                </Card>
                <Card title="Checkpoint gates" subtitle="Latest automated gate per checkpoint (QUALITY.Q_CHECK_RESULTS)">
                  <Table rows={latest} cols={[
                    { key: 'cp', label: 'Checkpoint' }, { key: 'pass', label: 'Pass', align: 'right' }, { key: 'n', label: 'Checks', align: 'right' },
                    { key: 'at', label: 'Run at', format: (v) => String(v).slice(0, 16) },
                  ]} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Completeness" info="completeness" subtitle="Null rate of conformed keys per L1 object">
                  <Table max={360} rows={d.tr_completeness} cols={[
                    { key: 'object_name', label: 'Object' }, { key: 'column_name', label: 'Column' },
                    { key: 'row_count', label: 'Rows', format: fmt.num, align: 'right' }, { key: 'null_pct', label: 'Null %', format: fmt.pct, align: 'right' },
                  ]} />
                </Card>
                <Card title="All checks">
                  <Table max={360} rows={d.tr_checks} highlight={(r) => r.result !== 'PASS'} cols={[
                    { key: 'checkpoint', label: 'CP' }, { key: 'check_id', label: 'Check' }, { key: 'description', label: 'Description' },
                    { key: 'actual', label: 'Actual' }, { key: 'result', label: 'Result' },
                  ]} />
                </Card>
              </Grid>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
