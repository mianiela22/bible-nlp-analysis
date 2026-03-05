import { useState, useMemo } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Legend, ReferenceLine,
} from 'recharts'

// ── Name selector badge ─────────────────────────────────────────────────────

function NameBadge({ name, data, selected, onToggle }) {
  const total = data.total
  const otPct = total > 0 ? Math.round(data.ot_count / total * 100) : 0
  const ntPct = 100 - otPct
  const isSelected = selected.includes(name)

  return (
    <button
      className={'name-badge ' + (isSelected ? 'selected' : '')}
      style={{
        borderColor: data.color,
        background: isSelected ? data.color + '22' : 'transparent',
      }}
      onClick={() => onToggle(name)}
    >
      <span className="badge-short" style={{ color: data.color }}>{data.short}</span>
      <span className="badge-total">{total.toLocaleString()}</span>
      <div className="badge-split-bar">
        <div
          className="badge-ot-fill"
          style={{ width: otPct + '%', background: '#8B4513' }}
          title={`OT: ${data.ot_count.toLocaleString()}`}
        />
        <div
          className="badge-nt-fill"
          style={{ width: ntPct + '%', background: '#4169E1' }}
          title={`NT: ${data.nt_count.toLocaleString()}`}
        />
      </div>
      <div className="badge-split-label">
        <span style={{ color: '#8B4513' }}>{otPct}% OT</span>
        <span style={{ color: '#4169E1' }}>{ntPct}% NT</span>
      </div>
    </button>
  )
}

// ── Main component ───────────────────────────────────────────────────────────

function DivineNamesTab({ data }) {
  const [selected, setSelected] = useState(['LORD', 'Jesus', 'Christ', 'God'])
  const [view, setView] = useState('compare')   // 'compare' | 'ot_nt' | 'deepdive' | 'associations'
  const [showRate, setShowRate] = useState(false)
  const [activeName, setActiveName] = useState('LORD')
  const [compareNameA, setCompareNameA] = useState('LORD')
  const [compareNameB, setCompareNameB] = useState('Jesus')

  if (!data) return <p>Loading divine names data...</p>

  const { names, book_order, name_order } = data

  // ── Handlers ──────────────────────────────────────────────────────────────

  function toggleName(name) {
    setSelected(prev => {
      if (prev.includes(name)) {
        // Don't deselect the last one
        if (prev.length === 1) return prev
        return prev.filter(n => n !== name)
      }
      // Cap at 5 for readability
      if (prev.length >= 5) return [...prev.slice(1), name]
      return [...prev, name]
    })
    setActiveName(name)
  }

  // ── Compare view: multi-line chart across 66 books ─────────────────────────

  const compareData = useMemo(() => {
    const dataKey = showRate ? 'by_book_rate' : 'by_book'
    return book_order.map(book => {
      const point = { book: book.length > 10 ? book.substring(0, 8) + '..' : book, fullBook: book }
      for (const name of selected) {
        point[name] = names[name][dataKey][book] || 0
      }
      return point
    })
  }, [selected, showRate, book_order, names])

  // ── OT vs NT grouped bar ───────────────────────────────────────────────────

  const otNtData = useMemo(() => {
    return selected.map(name => ({
      name: names[name].short,
      fullName: name,
      OT: showRate
        ? +(names[name].ot_count / 23213 * 1000).toFixed(2)  // OT word total approx
        : names[name].ot_count,
      NT: showRate
        ? +(names[name].nt_count / 181253 * 1000).toFixed(2)  // NT word total approx
        : names[name].nt_count,
      color: names[name].color,
    }))
  }, [selected, showRate, names])

  // ── Deep dive: single name across 66 books ────────────────────────────────

  const deepDiveData = useMemo(() => {
    const dataKey = showRate ? 'by_book_rate' : 'by_book'
    return book_order.map((book, i) => ({
      book: book.length > 10 ? book.substring(0, 8) + '..' : book,
      fullBook: book,
      value: names[activeName][dataKey][book] || 0,
      testament: i < 39 ? 'OT' : 'NT',
    }))
  }, [activeName, showRate, book_order, names])

  // ── Custom Tooltips ───────────────────────────────────────────────────────

  const CompareTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const full = payload[0]?.payload?.fullBook || label
      return (
        <div className="custom-tooltip">
          <strong>{full}</strong>
          {payload.map((p, i) => (
            <p key={i} style={{ color: p.color }}>
              {p.dataKey}: {showRate ? p.value.toFixed(2) + ' per 1k' : p.value}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const activeNameData = names[activeName]

  return (
    <div className="tab-content">

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <div className="insight-box" style={{ marginBottom: 24 }}>
        <h4>🕊️ Divine Names in the Bible</h4>
        <p>
          The Bible uses different names and titles for God — each one revealing something
          distinct about his character and his relationship to humanity. In the KJV, <strong>LORD</strong> (all caps)
          translates the Hebrew <em>YHWH</em>, while <strong>God</strong> translates <em>Elohim</em>.
          The NT shift from LORD to <strong>Jesus</strong> and <strong>Christ</strong> is one of the most
          theologically charged patterns in all of Scripture. Select names below and explore.
        </p>
      </div>

      {/* ── Name selector badges ──────────────────────────────────────────── */}
      <h3 style={{ marginBottom: 12 }}>Select Names to Explore <span style={{ fontWeight: 400, fontSize: '0.85em', color: '#888' }}>(up to 5)</span></h3>
      <div className="name-badges-grid">
        {name_order.map(name => (
          <NameBadge
            key={name}
            name={name}
            data={names[name]}
            selected={selected}
            onToggle={toggleName}
          />
        ))}
      </div>

      {/* ── Controls ─────────────────────────────────────────────────────── */}
      <div className="controls" style={{ marginTop: 24 }}>
        <button className={'control-btn ' + (view === 'compare' ? 'active' : '')} onClick={() => setView('compare')}>
          📈 Compare Across Books
        </button>
        <button className={'control-btn ' + (view === 'ot_nt' ? 'active' : '')} onClick={() => setView('ot_nt')}>
          📖 OT vs NT Split
        </button>
        <button className={'control-btn ' + (view === 'deepdive' ? 'active' : '')} onClick={() => setView('deepdive')}>
          🔍 Deep Dive
        </button>
        <button className={'control-btn ' + (view === 'associations' ? 'active' : '')} onClick={() => setView('associations')}>
          🔤 Associations
        </button>
        <span style={{ margin: '0 16px', color: '#ccc' }}>|</span>
        <button className={'control-btn ' + (!showRate ? 'active' : '')} onClick={() => setShowRate(false)}>
          Raw Count
        </button>
        <button className={'control-btn ' + (showRate ? 'active' : '')} onClick={() => setShowRate(true)}>
          Per 1,000 Words
        </button>
      </div>

      {/* ── COMPARE VIEW: multi-line across 66 books ──────────────────────── */}
      {view === 'compare' && (
        <div className="chart-container">
          <h3>
            {selected.join(' · ')} — across all 66 books
            {showRate ? ' (per 1,000 words)' : ' (raw count)'}
          </h3>
          <p className="chart-description">
            Watch how names rise and fall across the Bible's narrative arc. The vertical boundary between
            book 39 (Malachi) and book 40 (Matthew) is the Old/New Testament divide.
          </p>
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={compareData} margin={{ bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
              <XAxis
                dataKey="book"
                angle={-90}
                textAnchor="end"
                interval={0}
                style={{ fontSize: 8.5 }}
                height={80}
              />
              <YAxis />
              <Tooltip content={<CompareTooltip />} />
              <ReferenceLine x={compareData[38]?.book} stroke="#888" strokeDasharray="5 5" label={{ value: 'OT | NT', position: 'top', fontSize: 10, fill: '#888' }} />
              <Legend verticalAlign="top" height={32} />
              {selected.map(name => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={names[name].color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <div className="insight-box" style={{ marginTop: 16 }}>
            <p>
              <strong>Try this:</strong> Select <em>LORD + Jesus + Christ</em> to see the great
              theological handoff — the Tetragrammaton dominating the OT, then Jesus/Christ
              erupting in the NT while LORD nearly vanishes. This is what the NT authors
              called "fulfillment."
            </p>
          </div>
        </div>
      )}

      {/* ── OT vs NT VIEW ─────────────────────────────────────────────────── */}
      {view === 'ot_nt' && (
        <div className="chart-container">
          <h3>OT vs NT — Where Each Name Lives</h3>
          <p className="chart-description">
            Some names are almost exclusively Old Testament; others are purely New Testament.
            This contrast is one of the Bible's most powerful internal arguments for its unity —
            each half needs the other.
          </p>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={otNtData} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
              <XAxis dataKey="name" style={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [
                  showRate ? value.toFixed(2) + ' per 1k' : value.toLocaleString(),
                  name
                ]}
              />
              <Legend />
              <Bar dataKey="OT" name="Old Testament" fill="#8B4513" opacity={0.85} />
              <Bar dataKey="NT" name="New Testament" fill="#4169E1" opacity={0.85} />
            </BarChart>
          </ResponsiveContainer>

          {/* Percentage breakdown cards */}
          <div className="stats-row" style={{ marginTop: 20 }}>
            {selected.map(name => {
              const d = names[name]
              const otPct = d.total > 0 ? (d.ot_count / d.total * 100).toFixed(1) : 0
              const ntPct = d.total > 0 ? (d.nt_count / d.total * 100).toFixed(1) : 0
              return (
                <div key={name} className="stat-card" style={{ borderLeft: `4px solid ${d.color}` }}>
                  <div className="stat-number" style={{ fontSize: '1.1rem', color: d.color }}>{d.short}</div>
                  <div className="stat-detail">{d.total.toLocaleString()} total</div>
                  <div className="stat-detail" style={{ marginTop: 4 }}>
                    <span style={{ color: '#8B4513' }}>▪ OT {otPct}%</span>
                    {' · '}
                    <span style={{ color: '#4169E1' }}>▪ NT {ntPct}%</span>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="insight-box" style={{ marginTop: 20 }}>
            <p>
              <strong>LORD of hosts</strong> is 100% OT — it's Yahweh as cosmic general,
              a title the NT never uses because the war has been won at the cross.
              <strong> Father</strong> is 99.6% NT — Jesus made it available. <strong> Almighty</strong> is
              the great exception: Job (OT suffering) and Revelation (NT glory) both cry it out.
            </p>
          </div>
        </div>
      )}

      {/* ── DEEP DIVE VIEW ────────────────────────────────────────────────── */}
      {view === 'deepdive' && (
        <div>
          {/* Name picker */}
          <div className="controls" style={{ marginBottom: 8 }}>
            <span style={{ marginRight: 12, color: '#aaa', fontSize: 13 }}>Dive into:</span>
            {name_order.map(name => (
              <button
                key={name}
                className={'control-btn ' + (activeName === name ? 'active' : '')}
                style={activeName === name ? { background: names[name].color, borderColor: names[name].color } : {}}
                onClick={() => setActiveName(name)}
              >
                {names[name].short}
              </button>
            ))}
          </div>

          {/* Distribution chart */}
          <div className="chart-container">
            <h3>
              <span style={{ color: activeNameData.color }}>"{activeName}"</span>
              {' '}— {activeNameData.description}
            </h3>
            <p className="chart-description">
              {activeNameData.total.toLocaleString()} occurrences · {' '}
              <span style={{ color: '#8B4513' }}>OT: {activeNameData.ot_count.toLocaleString()}</span>
              {' '}·{' '}
              <span style={{ color: '#4169E1' }}>NT: {activeNameData.nt_count.toLocaleString()}</span>
            </p>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={deepDiveData} margin={{ bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
                <XAxis
                  dataKey="book"
                  angle={-90}
                  textAnchor="end"
                  interval={0}
                  style={{ fontSize: 8.5 }}
                  height={80}
                />
                <YAxis />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload
                      return (
                        <div className="custom-tooltip">
                          <strong>{d.fullBook}</strong>
                          <p>{showRate ? payload[0].value.toFixed(2) + ' per 1,000 words' : payload[0].value + ' occurrences'}</p>
                          <p style={{ color: d.testament === 'OT' ? '#8B4513' : '#4169E1' }}>{d.testament}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <ReferenceLine x={deepDiveData[38]?.book} stroke="#888" strokeDasharray="5 5" />
                <Bar dataKey="value" name={activeName}>
                  {deepDiveData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={activeNameData.color}
                      opacity={entry.testament === 'OT' ? 0.65 : 1.0}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Theology + sample verses */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 20 }}>

            {/* Theology card */}
            <div className="insight-box" style={{ borderLeft: `4px solid ${activeNameData.color}` }}>
              <h4 style={{ color: activeNameData.color }}>Theological Significance</h4>
              <p style={{ lineHeight: 1.7 }}>{activeNameData.theology}</p>
            </div>

            {/* Sample verses */}
            <div>
              <h4 style={{ marginBottom: 12 }}>Sample Verses</h4>
              {activeNameData.sample_verses.length === 0 ? (
                <p style={{ color: '#888' }}>No sample verses available.</p>
              ) : (
                activeNameData.sample_verses.map((v, i) => (
                  <div key={i} className="verse-card" style={{ borderLeft: `3px solid ${activeNameData.color}`, marginBottom: 10 }}>
                    <div className="verse-ref" style={{ color: activeNameData.color }}>
                      {v.book} {v.chapter}:{v.verse}
                      <span style={{ marginLeft: 8, color: v.testament === 'Old Testament' ? '#8B4513' : '#4169E1', fontSize: '0.8em' }}>
                        {v.testament === 'Old Testament' ? 'OT' : 'NT'}
                      </span>
                    </div>
                    <div className="verse-text" style={{ fontSize: '0.9em', lineHeight: 1.6 }}>
                      {highlightName(v.text, activeName)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── ASSOCIATIONS VIEW ─────────────────────────────────────────── */}
      {view === 'associations' && (
        <AssociationsView
          names={names}
          name_order={name_order}
          nameA={compareNameA}
          nameB={compareNameB}
          setNameA={setCompareNameA}
          setNameB={setCompareNameB}
        />
      )}

    </div>
  )
}

// ── Associations view component ───────────────────────────────────────────────

function AssociationsView({ names, name_order, nameA, nameB, setNameA, setNameB }) {
  const dataA = names[nameA]
  const dataB = names[nameB]

  // Words in A's top associations
  const wordsA = new Set(dataA.associations.map(a => a.word))
  const wordsB = new Set(dataB.associations.map(a => a.word))

  // Categorise each word as unique to A, unique to B, or shared
  const uniqueToA = dataA.associations.filter(a => !wordsB.has(a.word))
  const uniqueToB = dataB.associations.filter(a => !wordsA.has(a.word))
  const sharedWords = dataA.associations.filter(a => wordsB.has(a.word))

  // Max specificity across both lists for scaling bar widths
  const maxSpec = Math.max(
    ...dataA.associations.map(a => a.specificity),
    ...dataB.associations.map(a => a.specificity),
    1
  )

  return (
    <div>
      {/* Name pickers */}
      <div style={{ display: 'flex', gap: 32, marginBottom: 24, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: 6 }}>Compare</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {name_order.map(n => (
              <button
                key={n}
                className={'control-btn ' + (nameA === n ? 'active' : '')}
                style={nameA === n ? { background: names[n].color, borderColor: names[n].color } : {}}
                onClick={() => { if (n !== nameB) setNameA(n) }}
              >
                {names[n].short}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: 6 }}>with</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {name_order.map(n => (
              <button
                key={n}
                className={'control-btn ' + (nameB === n ? 'active' : '')}
                style={nameB === n ? { background: names[n].color, borderColor: names[n].color } : {}}
                onClick={() => { if (n !== nameA) setNameB(n) }}
              >
                {names[n].short}
              </button>
            ))}
          </div>
        </div>
      </div>

      <p className="chart-description" style={{ marginBottom: 20 }}>
        Words that appear <em>distinctively often</em> in the same verse as each name — the higher the bar,
        the more specifically that word belongs to that name's world. Words appearing in both lists are shown in the middle.
      </p>

      {/* Three-column layout: unique A | shared | unique B */}
      <div className="assoc-grid">

        {/* Column A — unique words */}
        <div className="assoc-col">
          <h4 style={{ color: dataA.color, borderBottom: `2px solid ${dataA.color}`, paddingBottom: 6, marginBottom: 14 }}>
            Only near "{nameA}"
          </h4>
          {uniqueToA.slice(0, 18).map(a => (
            <AssocWord key={a.word} word={a.word} spec={a.specificity} count={a.count} maxSpec={maxSpec} color={dataA.color} />
          ))}
        </div>

        {/* Shared words */}
        <div className="assoc-col assoc-shared">
          <h4 style={{ color: '#888', borderBottom: `2px solid #ddd`, paddingBottom: 6, marginBottom: 14 }}>
            In both
          </h4>
          {sharedWords.slice(0, 12).map(a => {
            const bEntry = dataB.associations.find(b => b.word === a.word)
            return (
              <div key={a.word} className="assoc-shared-word">
                <span className="assoc-word-label" style={{ color: '#555' }}>{a.word}</span>
                <div style={{ display: 'flex', gap: 3, marginTop: 3 }}>
                  <div style={{ height: 4, width: Math.round(a.specificity / maxSpec * 60) + 'px', background: dataA.color, borderRadius: 2, opacity: 0.8 }} />
                  <div style={{ height: 4, width: Math.round((bEntry?.specificity || 0) / maxSpec * 60) + 'px', background: dataB.color, borderRadius: 2, opacity: 0.8 }} />
                </div>
              </div>
            )
          })}
          {sharedWords.length === 0 && (
            <p style={{ color: '#aaa', fontSize: '0.85rem', fontStyle: 'italic' }}>No shared words in top associations</p>
          )}
        </div>

        {/* Column B — unique words */}
        <div className="assoc-col">
          <h4 style={{ color: dataB.color, borderBottom: `2px solid ${dataB.color}`, paddingBottom: 6, marginBottom: 14 }}>
            Only near "{nameB}"
          </h4>
          {uniqueToB.slice(0, 18).map(a => (
            <AssocWord key={a.word} word={a.word} spec={a.specificity} count={a.count} maxSpec={maxSpec} color={dataB.color} />
          ))}
        </div>
      </div>

      {/* Theological read-out */}
      <div className="insight-box" style={{ marginTop: 28 }}>
        <h4>📖 What this reveals</h4>
        <p>
          These aren't just word counts — they're the <strong>theological fingerprint</strong> of each name.
          Words with high specificity appear far more often near this name than anywhere else in Scripture.
          <strong> "{nameA}"</strong> carries its own cluster of ideas, people, and contexts.
          <strong> "{nameB}"</strong> carries a completely different world.
          Compare <em>LORD + Jesus</em> to see the Old and New Covenant semantic universes side by side.
          Try <em>Father + LORD of hosts</em> to feel the contrast between intimacy and transcendence.
        </p>
      </div>
    </div>
  )
}

function AssocWord({ word, spec, count, maxSpec, color }) {
  const barWidth = Math.max(8, Math.round(spec / maxSpec * 100))
  return (
    <div className="assoc-word-row" title={`${count} occurrences · ${spec}x more common near this name`}>
      <span className="assoc-word-label">{word}</span>
      <div className="assoc-bar-track">
        <div className="assoc-bar-fill" style={{ width: barWidth + '%', background: color }} />
      </div>
      <span className="assoc-spec">{spec}×</span>
    </div>
  )
}

// ── Highlight the divine name within verse text ──────────────────────────────

function highlightName(text, name) {
  const parts = text.split(new RegExp(`(${escapeRegex(name)})`, 'g'))
  return parts.map((part, i) =>
    part === name
      ? <mark key={i} style={{ background: '#FFD700', padding: '0 2px', borderRadius: 2 }}>{part}</mark>
      : part
  )
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export default DivineNamesTab
