import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import { dirFor, type SupportedLanguage } from '../../i18n'

export interface StatusBarChartEntry {
  status: string
  count: number
  label: string
  color: string
}

// Section 2.1: "charts and map controls must also flip correctly" in RTL.
// A horizontal bar chart's bars conventionally grow away from the axis
// origin in the reading direction, so the whole chart mirrors for Arabic:
// the category axis moves to the right (where Arabic reading starts) and
// the value axis reverses so bars grow right-to-left.
export function StatusBarChart({ data }: { data: StatusBarChartEntry[] }) {
  const { t, i18n } = useTranslation()
  const dir = dirFor(i18n.language as SupportedLanguage)
  const isRtl = dir === 'rtl'

  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">{t('dashboard.no_data')}</p>
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(data.length * 40, 120)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 24 }}>
        <XAxis type="number" allowDecimals={false} reversed={isRtl} hide />
        <YAxis
          type="category"
          dataKey="label"
          orientation={isRtl ? 'right' : 'left'}
          width={140}
          tickLine={false}
          axisLine={false}
          tick={{ fill: 'var(--color-foreground)', fontSize: 13 }}
        />
        {/* Numeric values are always shown as text on the bar itself
            (not hover-only) per the chart a11y guidance — Tooltip is
            still there for the exact figure on hover, not as the only
            way to read it. */}
        <Tooltip
          contentStyle={{
            background: 'var(--color-background)',
            border: '1px solid var(--color-border)',
            borderRadius: 8,
            direction: dir,
          }}
        />
        <Bar dataKey="count" radius={4} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell key={entry.status} fill={entry.color} />
          ))}
          <LabelList
            dataKey="count"
            position={isRtl ? 'left' : 'right'}
            fill="var(--color-foreground)"
            fontSize={13}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
