"""Click-a-header sorting for the journal site's tables.

Shared by the daily grids (lib/journal/day_page.py) and the strategy summary
(run_trade_review_pages.py) so both behave identically: every column sortable,
direction toggles on a second click, blanks always last whichever way.

Contract for a table that opts in:
  * <table class="grid"> with a <thead> row and a single <tbody>
  * each <th> carries class "num" when its column sorts numerically (dates sort
    numerically as YYYYMMDD), and an optional <span class="arrow"> indicator
  * each <td> carries data-v with the raw sort value ("" means blank)

No imports -- this module is the bottom of the dependency chain, so both
renderers can use it without importing each other.
"""
from __future__ import annotations

SORT_JS = """
document.querySelectorAll('table.grid').forEach(function (tbl) {
  var heads = tbl.tHead.rows[0].cells;
  function applySort(th, i, dir) {
    Array.prototype.forEach.call(heads, function (h) {
      delete h.dataset.dir; h.classList.remove('sorted');
      var a = h.querySelector('.arrow'); if (a) a.textContent = '\\u25B4\\u25BE';
    });
    th.dataset.dir = dir; th.classList.add('sorted');
    var arrow = th.querySelector('.arrow');
    if (arrow) arrow.textContent = dir === 'asc' ? '\\u25B4' : '\\u25BE';
    var numeric = th.classList.contains('num');
    var body = tbl.tBodies[0];
    var rows = Array.prototype.slice.call(body.rows);
    rows.sort(function (a, b) {
      var x = a.cells[i].dataset.v, y = b.cells[i].dataset.v;
      var xe = (x === undefined || x === ''), ye = (y === undefined || y === '');
      if (xe || ye) return xe && ye ? 0 : (xe ? 1 : -1);  // blanks last, both ways
      var c = numeric ? (parseFloat(x) - parseFloat(y)) : x.localeCompare(y);
      return dir === 'asc' ? c : -c;
    });
    rows.forEach(function (r) { body.appendChild(r); });
  }
  Array.prototype.forEach.call(heads, function (th, i) {
    th.addEventListener('click', function () {
      applySort(th, i, th.dataset.dir === 'asc' ? 'desc' : 'asc');
    });
    // Opt-in default sort applied on load: <th data-default-sort="desc">. One per grid.
    if (th.dataset.defaultSort) applySort(th, i, th.dataset.defaultSort);
  });
});
"""

# Header affordance, scoped so a page can opt a single table in.
SORT_CSS = """
  table.grid thead th { cursor: pointer; user-select: none; }
  table.grid thead th:hover { color: var(--accent); }
  table.grid thead th .arrow { opacity: .35; font-size: 9px; margin-left: 3px; }
  table.grid thead th.sorted { color: var(--accent); }
  table.grid thead th.sorted .arrow { opacity: 1; }
"""

ARROW = '<span class="arrow">▴▾</span>'


def th(label: str, numeric: bool = False, default_sort: str | None = None) -> str:
    """One sortable header cell.

    default_sort: "asc" | "desc" -- SORT_JS applies it on load. At most one per grid; the journal's
    convention (2026-09-23) is exit date descending, i.e. most recently closed first. Blanks sort last
    in both directions, so still-open trades land at the bottom rather than jumping to the top.
    """
    ds = f' data-default-sort="{default_sort}"' if default_sort else ""
    return f'<th class="{"num" if numeric else ""}"{ds}>{label}{ARROW}</th>'


def sort_date(iso: str | None) -> str:
    """'2026-09-15' -> '20260915' (sorts numerically); None/'' -> '' (sorts last)."""
    return (iso or "").replace("-", "")


def sort_num(v: float | None) -> str:
    return "" if v is None else str(v)
