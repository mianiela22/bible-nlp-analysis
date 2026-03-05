import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend
} from 'recharts'

const OT_COLOR = '#8B4513'
const NT_COLOR = '#4169E1'
const ACCENT = '#DAA520'

function WordFrequencyTab({ data }) {
  const [showStops, setShowStops] = useState(false)
  const [compareMode, setCompareMode] = useState(false)

  if (!data) return <p>Loading word data...</p>

  // Top words chart data
  const topWords = showStops
    ? data.overall.top_50_with_stops.slice(0, 25)
    : data.overall.top_50_no_stops.slice(0, 25)

  const chartData = topWords.map(item => ({
    word: item.word,
    count: item.count,
  }))

  // OT vs NT comparison data
  const otWords = {}
  data.old_testament.top_30.forEach(item => {
    otWords[item.word] = item.count
  })

  const ntWords = {}
  data.new_testament.top_30.forEach(item => {
    ntWords[item.word] = item.count
  })

  // Combine top words from both testaments for comparison
  const allCompareWords = new Set([
    ...data.old_testament.top_30.slice(0, 15).map(i => i.word),
    ...data.new_testament.top_30.slice(0, 15).map(i => i.word),
  ])

  const compareData = Array.from(allCompareWords).map(word => ({
    word,
    'Old Testament': otWords[word] || 0,
    'New Testament': ntWords[word] || 0,
  })).sort((a, b) =>
    (b['Old Testament'] + b['New Testament']) - (a['Old Testament'] + a['New Testament'])
  ).slice(0, 20)

  return (
    <div className="tab-content">
      {/* Stats Overview */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-number">{data.overall.total_words.toLocaleString()}</div>
          <div className="stat-label">Total Words</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.overall.unique_words.toLocaleString()}</div>
          <div className="stat-label">Unique Words</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.old_testament.total_words.toLocaleString()}</div>
          <div className="stat-label">OT Words</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.new_testament.total_words.toLocaleString()}</div>
          <div className="stat-label">NT Words</div>
        </div>
      </div>

      {/* Toggle buttons */}
      <div className="controls">
        <button
          className={`control-btn ${!compareMode ? 'active' : ''}`}
          onClick={() => setCompareMode(false)}
        >
          Top Words Overall
        </button>
        <button
          className={`control-btn ${compareMode ? 'active' : ''}`}
          onClick={() => setCompareMode(true)}
        >
          OT vs NT Comparison
        </button>
        {!compareMode && (
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={showStops}
              onChange={(e) => setShowStops(e.target.checked)}
            />
            Include common words (the, and, of...)
          </label>
        )}
      </div>

      {/* Chart */}
      <div className="chart-container">
        <h3>{compareMode
          ? 'Old Testament vs New Testament — Top Words'
          : showStops
            ? 'Top 25 Words (All Words)'
            : 'Top 25 Meaningful Words (Stop Words Removed)'
        }</h3>

        <ResponsiveContainer width="100%" height={500}>
          {compareMode ? (
            <BarChart data={compareData} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="word" width={70} style={{ fontSize: 13 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Old Testament" fill={OT_COLOR} />
              <Bar dataKey="New Testament" fill={NT_COLOR} />
            </BarChart>
          ) : (
            <BarChart data={chartData} margin={{ bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="word"
                angle={-45}
                textAnchor="end"
                interval={0}
                style={{ fontSize: 12 }}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={ACCENT}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={index < 5 ? OT_COLOR : ACCENT} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Insight box */}
      <div className="insight-box">
        <h4>💡 Key Insight</h4>
        <p>
          <strong>"Lord"</strong> is the most common meaningful word in the Bible with{' '}
          {data.overall.top_50_no_stops[0].count.toLocaleString()} appearances — and{' '}
          {data.old_testament.top_30[0].count.toLocaleString()} of those are in the Old Testament alone.
          The shift from OT to NT is striking: the Old Testament emphasizes{' '}
          <em>nations and kingdoms</em> (Israel, king, people, house, land),
          while the New Testament shifts to <em>personal faith</em> (Jesus, Christ, father).
        </p>
      </div>
    </div>
  )
}

export default WordFrequencyTab