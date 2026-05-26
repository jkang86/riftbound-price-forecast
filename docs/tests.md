# docs/tests.md — Riftbound Market Intelligence Platform

## TEST STRATEGY

**Framework:** Vitest + React Testing Library + Playwright (E2E)
**Philosophy:** Test behavior, not implementation. Tests document intent.

```
Unit tests   → src/components/__tests__/   (Vitest + RTL)
Hook tests   → src/hooks/__tests__/        (Vitest)
Pipeline     → pipeline/tests/             (pytest)
E2E          → e2e/                        (Playwright)
```

---

## PIPELINE TESTS (pytest)

### scraper.py

```python
# pipeline/tests/test_scraper.py

def test_fetch_card_list_returns_nonempty():
    """TCGPlayer returns at least 1 Riftbound card."""
    cards = fetch_card_list()
    assert len(cards) > 0

def test_card_has_required_fields():
    """Each card has id, name, and rarity."""
    cards = fetch_card_list()
    for card in cards:
        assert 'id' in card
        assert 'name' in card
        assert 'rarity' in card

def test_price_history_has_90_days():
    """Price history contains at least 60 rows (some gaps acceptable)."""
    history = fetch_price_history('jinx-loose-cannon', days=90)
    assert len(history) >= 60

def test_price_history_values_positive():
    """All fetched prices are positive floats."""
    history = fetch_price_history('jinx-loose-cannon', days=90)
    for row in history:
        assert row['price'] > 0

def test_retry_logic_on_429():
    """Scraper retries on rate-limit response and eventually succeeds."""
    # Mock 429 twice, then 200
    with mock_responses([429, 429, 200]):
        result = fetch_price_history('test-card', days=7)
    assert result is not None
```

### model.py

```python
# pipeline/tests/test_model.py

def test_prophet_forecast_returns_30_days():
    """Forecast output contains exactly 30 future rows."""
    forecast = run_prophet(sample_history_90d)
    future_rows = [r for r in forecast if r['date'] > TODAY]
    assert len(future_rows) == 30

def test_confidence_band_is_ordered():
    """yhat_lower <= yhat <= yhat_upper for all rows."""
    forecast = run_prophet(sample_history_90d)
    for row in forecast:
        assert row['yhat_lower'] <= row['yhat'] <= row['yhat_upper']

def test_rmse_is_finite():
    """RMSE metric is a finite positive float."""
    _, metrics = run_prophet_with_metrics(sample_history_90d)
    assert math.isfinite(metrics['rmse'])
    assert metrics['rmse'] > 0

def test_skip_card_with_insufficient_history():
    """Cards with < 30 days of data are skipped, not crashed."""
    result = run_prophet(sample_history_10d)
    assert result is None

def test_signal_strong_buy():
    assert compute_signal(delta_7d=20, delta_30d=15, forecast_slope=0.5) == "STRONG BUY"

def test_signal_sell():
    assert compute_signal(delta_7d=-15, delta_30d=-10, forecast_slope=-0.2) == "SELL"

def test_signal_hold():
    assert compute_signal(delta_7d=1, delta_30d=0, forecast_slope=0.01) == "HOLD"
```

### export.py

```python
# pipeline/tests/test_export.py

def test_cards_json_schema():
    """cards.json matches expected schema for every card."""
    data = load_json('public/data/cards.json')
    required = {'id','name','faction','rarity','current_price',
                'delta_7d_pct','signal','sparkline'}
    for card in data['cards']:
        assert required <= card.keys()

def test_sparkline_has_16_points():
    """Every sparkline array has exactly 16 data points."""
    data = load_json('public/data/cards.json')
    for card in data['cards']:
        assert len(card['sparkline']) == 16

def test_forecasts_json_schema():
    """forecasts.json has history, forecast, and metrics per card."""
    data = load_json('public/data/forecasts.json')
    for f in data['forecasts']:
        assert 'history' in f
        assert 'forecast' in f
        assert 'metrics' in f
        assert 'rmse' in f['metrics']

def test_market_json_has_aggregates():
    """market.json has total_cards, market_cap, and volatility_index."""
    data = load_json('public/data/market.json')
    assert 'total_cards' in data
    assert 'market_cap' in data
    assert 'volatility_index' in data
```

---

## COMPONENT TESTS (Vitest + RTL)

### `<ScoreBug />`

```js
// src/components/__tests__/ScoreBug.test.jsx
import { render, screen } from '@testing-library/react'
import { ScoreBug } from '../ScoreBug'

test('renders label and value', () => {
  render(<ScoreBug label="MARKET CAP" value="$42,813" />)
  expect(screen.getByText('MARKET CAP')).toBeInTheDocument()
  expect(screen.getByText('$42,813')).toBeInTheDocument()
})

test('renders positive delta in green', () => {
  render(<ScoreBug label="VOL" value="$1,200" delta={8.4} />)
  const delta = screen.getByText(/\+8\.4%/)
  expect(delta).toHaveStyle({ color: '#4CAF50' })
})

test('renders negative delta in red', () => {
  render(<ScoreBug label="VOL" value="$1,200" delta={-3.1} />)
  const delta = screen.getByText(/−3\.1%/)
  expect(delta).toHaveStyle({ color: '#FF5252' })
})

test('renders without delta when not provided', () => {
  render(<ScoreBug label="CARDS" value="142" />)
  expect(screen.queryByText(/▲|▼/)).not.toBeInTheDocument()
})
```

### `<Delta />`

```js
test('renders upward arrow for positive value', () => {
  render(<Delta value={5.2} />)
  expect(screen.getByText(/▲/)).toBeInTheDocument()
  expect(screen.getByText(/\+5\.2%/)).toBeInTheDocument()
})

test('renders downward arrow for negative value', () => {
  render(<Delta value={-3.7} />)
  expect(screen.getByText(/▼/)).toBeInTheDocument()
})

test('uses green for positive', () => {
  const { container } = render(<Delta value={2} />)
  expect(container.firstChild).toHaveStyle({ color: '#4CAF50' })
})

test('uses red for negative', () => {
  const { container } = render(<Delta value={-2} />)
  expect(container.firstChild).toHaveStyle({ color: '#FF5252' })
})
```

### `<Rarity />`

```js
test.each(['Mythic','Legend','Epic','Rare','Common'])(
  'renders rarity label for %s', (rarity) => {
    render(<Rarity kind={rarity} />)
    expect(screen.getByText(rarity)).toBeInTheDocument()
  }
)

test('Mythic applies red color', () => {
  const { container } = render(<Rarity kind="Mythic" />)
  expect(container.firstChild).toHaveStyle({ color: '#E2012D' })
})
```

### `<Signal />`

```js
test.each(['STRONG BUY','BUY','HOLD','WATCH','SELL'])(
  'renders signal %s', (signal) => {
    render(<Signal kind={signal} />)
    expect(screen.getByText(signal)).toBeInTheDocument()
  }
)
```

### `<BroadcastTicker />`

```js
test('renders all ticker items', () => {
  const items = [
    { name: 'Jinx', price: 24.99, delta: 8.2 },
    { name: 'Garen', price: 5.49, delta: -1.3 },
  ]
  render(<BroadcastTicker items={items} />)
  expect(screen.getAllByText('Jinx').length).toBeGreaterThan(0)
  expect(screen.getAllByText('Garen').length).toBeGreaterThan(0)
})

test('has aria-live="polite"', () => {
  render(<BroadcastTicker items={[]} />)
  expect(screen.getByRole('marquee')).toHaveAttribute('aria-live', 'polite')
})
```

### `<ConfidenceBand />`

```js
test('renders without crashing with valid forecast data', () => {
  const mockForecast = {
    history: [{ date: '2025-01-01', price: 20 }],
    forecast: [{ date: '2025-04-01', yhat: 25, yhat_lower: 22, yhat_upper: 28 }],
  }
  const { container } = render(<ConfidenceBand data={mockForecast} />)
  expect(container.querySelector('.recharts-wrapper')).toBeInTheDocument()
})

test('renders skeleton when data is null', () => {
  render(<ConfidenceBand data={null} />)
  expect(document.querySelector('.skeleton')).toBeInTheDocument()
})
```

### `<MarketCard />`

```js
test('links to correct detail page', () => {
  const card = { id: 'jinx-loose-cannon', name: 'Jinx, Loose Cannon' }
  render(<MarketCard card={card} />)
  expect(screen.getByRole('link')).toHaveAttribute('href', '#/cards/jinx-loose-cannon')
})

test('shows signal badge', () => {
  const card = { ...mockCard, signal: 'STRONG BUY' }
  render(<MarketCard card={card} />)
  expect(screen.getByText('STRONG BUY')).toBeInTheDocument()
})
```

---

## HOOK TESTS

### `useMarketData`

```js
// src/hooks/__tests__/useMarketData.test.js
import { renderHook, waitFor } from '@testing-library/react'
import { useMarketData } from '../useMarketData'

test('returns null on initial render', () => {
  const { result } = renderHook(() => useMarketData())
  expect(result.current).toBeNull()
})

test('returns data after fetch resolves', async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ cards: [mockCard], updated_at: '2025-01-01' })
  })
  const { result } = renderHook(() => useMarketData())
  await waitFor(() => expect(result.current).not.toBeNull())
  expect(result.current.cards.length).toBe(1)
})
```

### `useReducedMotion`

```js
test('returns false when no preference set', () => {
  window.matchMedia = vi.fn().mockReturnValue({ matches: false })
  const { result } = renderHook(() => useReducedMotion())
  expect(result.current).toBe(false)
})

test('returns true when prefers-reduced-motion matches', () => {
  window.matchMedia = vi.fn().mockReturnValue({ matches: true })
  const { result } = renderHook(() => useReducedMotion())
  expect(result.current).toBe(true)
})
```

---

## ROUTE TESTS

```js
// src/__tests__/routes.test.jsx
test('renders Landing at #/', () => {
  window.location.hash = '#/'
  render(<App />)
  expect(screen.getByText(/RIFTBOUND ECONOMY/i)).toBeInTheDocument()
})

test('renders Dashboard at #/dashboard', () => {
  window.location.hash = '#/dashboard'
  render(<App />)
  expect(screen.getByText(/MARKET OVERVIEW/i)).toBeInTheDocument()
})

test('renders Explorer at #/cards', () => {
  window.location.hash = '#/cards'
  render(<App />)
  expect(screen.getByPlaceholderText(/search cards/i)).toBeInTheDocument()
})

test('renders Detail at #/cards/:id', () => {
  window.location.hash = '#/cards/jinx-loose-cannon'
  render(<App />)
  expect(screen.getByText(/Jinx/i)).toBeInTheDocument()
})

test('renders MetaTracker at #/meta', () => {
  window.location.hash = '#/meta'
  render(<App />)
  expect(screen.getByText(/META TRACKER/i)).toBeInTheDocument()
})
```

---

## E2E TESTS (Playwright)

```js
// e2e/landing.spec.js
test('landing page loads and shows score-bug row', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('[data-testid="score-bug-row"]')).toBeVisible()
})

test('clicking card navigates to detail', async ({ page }) => {
  await page.goto('/#/cards')
  await page.locator('[data-testid="market-card"]').first().click()
  await expect(page).toHaveURL(/#\/cards\/.+/)
})

test('filter by rarity reduces card count', async ({ page }) => {
  await page.goto('/#/cards')
  const initialCount = await page.locator('[data-testid="market-card"]').count()
  await page.locator('[data-testid="rarity-filter-Mythic"]').click()
  const filteredCount = await page.locator('[data-testid="market-card"]').count()
  expect(filteredCount).toBeLessThan(initialCount)
})

test('confidence band chart renders on detail page', async ({ page }) => {
  await page.goto('/#/cards/jinx-loose-cannon')
  await expect(page.locator('.recharts-wrapper')).toBeVisible()
})

test('nav keyboard accessible', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  const focused = await page.evaluate(() => document.activeElement?.tagName)
  expect(['A', 'BUTTON']).toContain(focused)
})
```

---

## ACCESSIBILITY TESTS

```js
// e2e/a11y.spec.js — uses @axe-core/playwright
import { checkA11y } from 'axe-playwright'

test('landing page has no axe violations', async ({ page }) => {
  await page.goto('/')
  await checkA11y(page, null, {
    detailedReport: true,
    runOnly: ['wcag2a', 'wcag2aa']
  })
})

test('card detail has no axe violations', async ({ page }) => {
  await page.goto('/#/cards/jinx-loose-cannon')
  await checkA11y(page)
})

test('explorer has no axe violations', async ({ page }) => {
  await page.goto('/#/cards')
  await checkA11y(page)
})
```

---

## RUNNING TESTS

```bash
# Unit + hook tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# E2E (requires running dev server)
npx playwright test

# Pipeline tests
cd pipeline && pytest tests/ -v

# A11y only
npx playwright test e2e/a11y.spec.js
```

---

## TEST COVERAGE TARGETS

| Area | Target |
|---|---|
| Broadcast primitives | 100% |
| Data hooks | 90% |
| Utility functions | 100% |
| Route rendering | 100% |
| Pipeline (pytest) | 80% |
| E2E happy paths | All 6 pages |
