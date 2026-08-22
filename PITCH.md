# PITCH

## Problem
Retail and e-commerce teams sit on huge volumes of sales and inventory
data but rarely have a data analyst on hand to answer a quick question.
Business users end up either guessing or waiting on a report that takes
days to produce. By the time the answer arrives, the stockout or the
slow-moving inventory has already cost money.

## Solution
Our platform lets anyone type a plain-English question — "which
products need restocking?", "which region is growing fastest?" — and
get back an instant answer, a chart, and the actual query that was run,
all backed by Exasol running the analytics at full speed across the
entire sales history rather than a sampled subset.

## Why Exasol
- **Speed at scale**: the query-speed demo widget shows a full-table
  scan and aggregation across hundreds of thousands of rows completing
  in milliseconds — the kind of query that would make a business user
  wait on a traditional row-store warehouse.
- **SQL-native workflow**: our NL-to-SQL layer only has to generate
  standard SQL, no custom query language or proprietary API to learn —
  which also makes the AI-generated queries auditable and safe to
  restrict/validate before execution.
- **No infra overhead for a 1-day build**: the hosted SaaS trial meant
  our team spent zero hours on database installation or cluster tuning
  and all of our time on the actual product.

## Backup demo checklist (screen-record this in advance)
- [ ] KPI cards loading with real numbers
- [ ] Revenue trend line chart rendering
- [ ] Top 5 products bar chart rendering
- [ ] Restock alerts list showing at least one flagged product
- [ ] Query-speed benchmark button showing rows scanned + elapsed ms
- [ ] All 4 pre-set example questions answered correctly with charts
- [ ] One live free-text question, asked and answered on camera
- [ ] "Show SQL" panel expanded at least once, to prove it's real
