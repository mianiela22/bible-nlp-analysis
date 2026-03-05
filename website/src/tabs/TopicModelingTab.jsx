import { useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts'

// ── Small inline editable label ──────────────────────────────────────────────

function EditableLabel({ value, onChange, color }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)

  function commit() {
    setEditing(false)
    if (draft.trim()) onChange(draft.trim())
  }

  if (editing) {
    return (
      <input
        className="topic-label-input"
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false) }}
        autoFocus
        style={{ borderBottomColor: color }}
      />
    )
  }
  return (
    <span
      className="topic-label-editable"
      style={{ color }}
      onClick={() => { setDraft(value); setEditing(true) }}
      title="Click to rename"
    >
      {value} ✏️
    </span>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

function TopicModelingTab({ data }) {
  const [view, setView] = useState('discover')   // 'discover' | 'book_dna' | 'explorer' | 'compare'
  const [labels, setLabels] = useState(null)     // user-renamed labels
  const [activeTopic, setActiveTopic] = useState(0)
  const [selectedBook, setSelectedBook] = useState('Genesis')
  const [compareBookA, setCompareBookA] = useState('Genesis')
  const [compareBookB, setCompareBookB] = useState('Romans')

  if (!data) return <p>Loading topic modeling data...</p>

  const { topics, book_profiles, book_order, n_topics } = data

  // Initialize labels from suggested labels
  const topicLabels = labels || topics.map(t => t.suggested_label)

  function setLabel(idx, label) {
    const updated = [...topicLabels]
    updated[idx] = label
    setLabels(updated)
  }

  // ── Discover view: grid of topic cards ────────────────────────────────────

  // ── Book DNA: topic profile of selected book ──────────────────────────────

  const bookProfileData = useMemo(() => {
    const profile = book_profiles[selectedBook] || []
    return profile
      .map((weight, i) => ({
        topic: topicLabels[i],
        topicId: i,
        weight: +(weight * 100).toFixed(1),
        color: topics[i].color,
      }))
      .sort((a, b) => b.weight - a.weight)
  }, [selectedBook, book_profiles, topics, topicLabels])

  // ── All books × topics heatmap data for explorer ──────────────────────────

  const explorerData = useMemo(() => {
    return book_order.map(book => {
      const profile = book_profiles[book] || []
      return {
        book: book.length > 10 ? book.substring(0, 8) + '..' : book,
        fullBook: book,
        value: +(( profile[activeTopic] || 0) * 100).toFixed(1),
        testament: book_order.indexOf(book) < 39 ? 'OT' : 'NT',
      }
    })
  }, [activeTopic, book_profiles, book_order])

  // ── Compare two books ─────────────────────────────────────────────────────

  const compareData = useMemo(() => {
    const profileA = book_profiles[compareBookA] || []
    const profileB = book_profiles[compareBookB] || []
    return topics.map((t, i) => ({
      topic: topicLabels[i].length > 22 ? topicLabels[i].substring(0, 20) + '..' : topicLabels[i],
      fullLabel: topicLabels[i],
      [compareBookA]: +((profileA[i] || 0) * 100).toFixed(1),
      [compareBookB]: +((profileB[i] || 0) * 100).toFixed(1),
      color: t.color,
    }))
  }, [compareBookA, compareBookB, book_profiles, topics, topicLabels])

  const activeTopicData = topics[activeTopic]

  return (
    <div className="tab-content">

      {/* ── Intro ──────────────────────────────────────────────────────────── */}
      <div className="insight-box" style={{ marginBottom: 24 }}>
        <h4>🧠 Topic Modeling — Themes the Machine Discovered</h4>
        <p>
          Using <strong>LDA (Latent Dirichlet Allocation)</strong>, we gave the algorithm all 1,189 Bible chapters
          and asked: <em>"What recurring themes do you see?"</em> It found {n_topics} distinct topics — without
          knowing anything about theology. Each chapter is a mixture of topics, and each topic is defined
          by the words that cluster together. The result: the machine independently rediscovered themes
          scholars have identified for centuries. <strong>Click any topic label to rename it.</strong>
        </p>
      </div>

      {/* ── View selector ──────────────────────────────────────────────────── */}
      <div className="controls" style={{ marginBottom: 24 }}>
        <button className={'control-btn ' + (view === 'discover' ? 'active' : '')} onClick={() => setView('discover')}>
          🗺️ Discover Topics
        </button>
        <button className={'control-btn ' + (view === 'book_dna' ? 'active' : '')} onClick={() => setView('book_dna')}>
          🧬 Book DNA
        </button>
        <button className={'control-btn ' + (view === 'explorer' ? 'active' : '')} onClick={() => setView('explorer')}>
          🔍 Topic Explorer
        </button>
        <button className={'control-btn ' + (view === 'compare' ? 'active' : '')} onClick={() => setView('compare')}>
          ⚖️ Compare Books
        </button>
      </div>

      {/* ── DISCOVER: topic cards grid ─────────────────────────────────────── */}
      {view === 'discover' && (
        <div>
          <p className="chart-description" style={{ marginBottom: 20 }}>
            Each card is a theme the algorithm discovered automatically. The bars show which words most strongly
            define each topic. Click a card to explore where it shows up across the Bible.
            <strong> Click the label to rename any topic.</strong>
          </p>
          <div className="topic-cards-grid">
            {topics.map((topic, i) => (
              <div
                key={i}
                className="topic-card"
                style={{ borderTop: `4px solid ${topic.color}` }}
                onClick={() => { setActiveTopic(i); setView('explorer') }}
              >
                <div className="topic-card-header">
                  <span className="topic-card-number" style={{ background: topic.color }}>T{i}</span>
                  <EditableLabel
                    value={topicLabels[i]}
                    onChange={label => setLabel(i, label)}
                    color={topic.color}
                  />
                </div>

                {/* Top 8 words as mini bars */}
                <div className="topic-word-bars">
                  {topic.top_words.slice(0, 8).map((w, wi) => {
                    const maxW = topic.top_words[0].weight
                    const pct = Math.round(w.weight / maxW * 100)
                    return (
                      <div key={wi} className="topic-word-row">
                        <span className="topic-word-name">{w.word}</span>
                        <div className="topic-word-track">
                          <div className="topic-word-fill" style={{ width: pct + '%', background: topic.color }} />
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Top books */}
                <div className="topic-card-books">
                  {topic.dominant_books.slice(0, 3).map(b => (
                    <span key={b.book} className="topic-book-chip" style={{ borderColor: topic.color, color: topic.color }}>
                      {b.book}
                    </span>
                  ))}
                </div>

                <div className="topic-card-cta">Click to explore →</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── BOOK DNA ───────────────────────────────────────────────────────── */}
      {view === 'book_dna' && (
        <div>
          <h3 style={{ marginBottom: 12 }}>What themes make up each book?</h3>
          <p className="chart-description" style={{ marginBottom: 16 }}>
            Select any book to see its "topic DNA" — the blend of discovered themes that characterise it.
            Genesis mixes Creation, Covenant, and Genealogy. Leviticus is almost entirely Sacrifice.
            Romans is dominated by Faith &amp; Salvation. The proportions are the book's theological fingerprint.
          </p>

          {/* Book selector */}
          <div className="book-selector-grid">
            {book_order.map((book, i) => (
              <button
                key={book}
                className={'book-sel-btn ' + (selectedBook === book ? 'active' : '')}
                style={selectedBook === book ? { background: '#2C3E50', color: 'white' } : {}}
                onClick={() => setSelectedBook(book)}
              >
                {book}
              </button>
            ))}
          </div>

          {/* Topic DNA chart */}
          <div className="chart-container" style={{ marginTop: 24 }}>
            <h3>
              <span style={{ color: '#2C3E50' }}>{selectedBook}</span> — Topic Composition
            </h3>
            <ResponsiveContainer width="100%" height={420}>
              <BarChart data={bookProfileData} layout="vertical" margin={{ left: 200 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
                <XAxis type="number" tickFormatter={v => v + '%'} domain={[0, 'dataMax']} />
                <YAxis type="category" dataKey="topic" width={195} style={{ fontSize: 11 }} />
                <Tooltip formatter={v => v.toFixed(1) + '%'} />
                <Bar dataKey="weight" name="Topic weight">
                  {bookProfileData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top chapter hint */}
          <div className="insight-box" style={{ marginTop: 16 }}>
            <p>
              <strong>{selectedBook}</strong>'s dominant theme is{' '}
              <strong style={{ color: bookProfileData[0]?.color }}>{bookProfileData[0]?.topic}</strong>
              {' '}({bookProfileData[0]?.weight.toFixed(1)}% of its content).
              The topic mix above is the machine's answer to: "What is this book <em>about</em>?"
            </p>
          </div>
        </div>
      )}

      {/* ── TOPIC EXPLORER ─────────────────────────────────────────────────── */}
      {view === 'explorer' && (
        <div>
          {/* Topic selector */}
          <div className="controls" style={{ marginBottom: 16, flexWrap: 'wrap' }}>
            <span style={{ color: '#888', fontSize: 13, marginRight: 10 }}>Explore topic:</span>
            {topics.map((t, i) => (
              <button
                key={i}
                className={'control-btn ' + (activeTopic === i ? 'active' : '')}
                style={activeTopic === i ? { background: t.color, borderColor: t.color } : {}}
                onClick={() => setActiveTopic(i)}
                title={topicLabels[i]}
              >
                T{i}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
            {/* Topic definition */}
            <div className="insight-box" style={{ borderLeft: `4px solid ${activeTopicData.color}` }}>
              <h4 style={{ color: activeTopicData.color }}>
                <EditableLabel
                  value={topicLabels[activeTopic]}
                  onChange={label => setLabel(activeTopic, label)}
                  color={activeTopicData.color}
                />
              </h4>
              <p style={{ fontSize: '0.85rem', color: '#888', marginBottom: 10 }}>Top defining words:</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {activeTopicData.top_words.slice(0, 15).map((w, i) => (
                  <span
                    key={i}
                    className="word-chip"
                    style={{
                      background: activeTopicData.color + '22',
                      borderColor: activeTopicData.color,
                      fontSize: Math.max(0.7, 1.1 - i * 0.03) + 'rem',
                    }}
                  >
                    {w.word}
                  </span>
                ))}
              </div>
            </div>

            {/* Top chapters */}
            <div>
              <h4 style={{ marginBottom: 12 }}>Where this theme peaks</h4>
              {activeTopicData.top_chapters.map((ch, i) => (
                <div key={i} className="chapter-card" style={{ borderLeft: `3px solid ${activeTopicData.color}` }}>
                  <div className="chapter-ref" style={{ color: activeTopicData.color }}>
                    {ch.book} {ch.chapter}
                    <span className="chapter-score"> — {(ch.score * 100).toFixed(0)}% this topic</span>
                  </div>
                  <div className="chapter-preview">{ch.preview}…</div>
                </div>
              ))}
            </div>
          </div>

          {/* Distribution across all 66 books */}
          <div className="chart-container">
            <h3>
              "<span style={{ color: activeTopicData.color }}>{topicLabels[activeTopic]}</span>"
              — presence across all 66 books
            </h3>
            <p className="chart-description">
              How much of each book's content belongs to this topic. Higher = more dominant.
            </p>
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={explorerData} margin={{ bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
                <XAxis
                  dataKey="book"
                  angle={-90}
                  textAnchor="end"
                  interval={0}
                  style={{ fontSize: 8.5 }}
                  height={80}
                />
                <YAxis tickFormatter={v => v + '%'} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload?.length) {
                      const d = payload[0].payload
                      return (
                        <div className="custom-tooltip">
                          <strong>{d.fullBook}</strong>
                          <p style={{ color: activeTopicData.color }}>{d.value.toFixed(1)}% {topicLabels[activeTopic]}</p>
                          <p style={{ color: d.testament === 'OT' ? '#8B4513' : '#4169E1' }}>{d.testament}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Bar dataKey="value" name={topicLabels[activeTopic]}>
                  {explorerData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={activeTopicData.color}
                      opacity={entry.testament === 'OT' ? 0.65 : 1.0}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── COMPARE BOOKS ──────────────────────────────────────────────────── */}
      {view === 'compare' && (
        <div>
          <h3 style={{ marginBottom: 8 }}>Compare any two books' topic DNA side by side</h3>
          <p className="chart-description" style={{ marginBottom: 20 }}>
            Pick any two books and see how their theological content differs. Genesis vs Romans?
            Psalms vs Revelation? The algorithm's breakdown often confirms what you'd expect —
            and sometimes surprises you.
          </p>

          {/* Book pickers */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginBottom: 24 }}>
            {[
              { label: 'Book A', val: compareBookA, set: setCompareBookA },
              { label: 'Book B', val: compareBookB, set: setCompareBookB },
            ].map(({ label, val, set }) => (
              <div key={label}>
                <div style={{ fontWeight: 700, marginBottom: 8 }}>{label}: <span style={{ color: '#4169E1' }}>{val}</span></div>
                <select
                  value={val}
                  onChange={e => set(e.target.value)}
                  className="select-input"
                  style={{ width: '100%' }}
                >
                  {book_order.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
            ))}
          </div>

          {/* Grouped bar chart */}
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={480}>
              <BarChart data={compareData} layout="vertical" margin={{ left: 200 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
                <XAxis type="number" tickFormatter={v => v + '%'} />
                <YAxis type="category" dataKey="topic" width={195} style={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(v, name) => [v.toFixed(1) + '%', name]}
                  content={({ active, payload, label }) => {
                    if (active && payload?.length) {
                      return (
                        <div className="custom-tooltip">
                          <strong>{label}</strong>
                          {payload.map((p, i) => (
                            <p key={i} style={{ color: p.fill }}>{p.name}: {p.value.toFixed(1)}%</p>
                          ))}
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Legend />
                <Bar dataKey={compareBookA} fill="#8B4513" opacity={0.85} />
                <Bar dataKey={compareBookB} fill="#4169E1" opacity={0.85} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="insight-box" style={{ marginTop: 16 }}>
            <p>
              The longer the bar difference between <strong>{compareBookA}</strong> and{' '}
              <strong>{compareBookB}</strong>, the more that theme distinguishes them.
              Overlapping bars mean shared theological territory. Try{' '}
              <em>Leviticus vs Romans</em> — Law vs Grace — and watch the Sacrifice bar vs the Faith bar.
            </p>
          </div>
        </div>
      )}

    </div>
  )
}

export default TopicModelingTab
