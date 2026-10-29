#!/usr/bin/env python3
"""Build NANO POS v2.0.21 manufacturing screen update from the verified v2.0.20 ASAR."""
import hashlib, json, struct, sys, zipfile
from pathlib import Path

BASE_PATCH_SHA256 = "c11937ee352f67616d4c529f6eb5034e81460497a0e72dfc1fbbc8753d8c0202"
BASE_ASAR_SHA256 = "fa6442b369caeb29c8493e807341213b67c9c906523cdd6c526d6b464cc51f37"
BASE_VERSION = "2.0.20"
NEW_VERSION = "2.0.21"
MARKER = "__NANO_MANUFACTURING_CENTER_V221"

MANUFACTURING_UI = r'''
(function () {
  if (window.__nanoManufacturingCenterV221) return;
  window.__nanoManufacturingCenterV221 = true;

  var dictionaries = {
    ar: {
      title: 'مركز التصنيع والإنتاج',
      subtitle: 'لوحة تشغيل سريعة للتركيبات وأوامر الإنتاج ومراجعة المواد قبل التنفيذ.',
      newOrder: 'أمر إنتاج جديد',
      recipes: 'إدارة التركيبات',
      orders: 'أوامر الإنتاج',
      ingredients: 'المكونات والدفعات',
      statRecipes: 'التركيبات المعروضة',
      statOrders: 'أوامر الإنتاج المعروضة',
      statShortages: 'صفوف تحتاج متابعة',
      search: 'ابحث في جداول التصنيع: اسم المنتج، التركيبة، رقم الأمر…',
      clear: 'مسح',
      checklist: 'قائمة التحقق قبل تأكيد الإنتاج',
      checks: [
        'تحقق من التركيبة والكمية الناتجة والوحدة الصحيحة.',
        'راجع توفر المكونات وتواريخ صلاحية الدفعات.',
        'راجع تكلفة المواد والتكاليف الإضافية وسعر البيع المقترح.',
        'قبل التأكيد، تحقق من الكمية المراد إنتاجها ومخرج الدفعة.'
      ],
      statusReady: 'جاهز — البحث يصفّي الصفوف الظاهرة في جداول التصنيع فقط.',
      statusNoAction: 'لم أجد زر الإجراء في الجزء الظاهر. انتقلت إلى القسم الأقرب؛ استخدم أزرار الشاشة الأصلية عند الحاجة.',
      statusAction: 'تم فتح الإجراء من الواجهة الأصلية.',
      statusJump: 'تم الانتقال إلى القسم المطلوب.',
      statusFiltered: 'الصفوف المطابقة',
      noRows: '—',
      shortcuts: 'اختصارات',
      emptySearch: 'لا توجد صفوف مطابقة في الجداول الحالية.'
    },
    fr: {
      title: 'Centre de fabrication et production',
      subtitle: 'Accès rapide aux recettes, ordres de production et vérifications avant lancement.',
      newOrder: 'Nouvel ordre de production',
      recipes: 'Gérer les recettes',
      orders: 'Ordres de production',
      ingredients: 'Composants et lots',
      statRecipes: 'Recettes affichées',
      statOrders: 'Ordres affichés',
      statShortages: 'Lignes à vérifier',
      search: 'Rechercher dans les tableaux : produit, recette, numéro d’ordre…',
      clear: 'Effacer',
      checklist: 'Contrôles avant confirmation',
      checks: [
        'Vérifier la recette, la quantité produite et l’unité.',
        'Contrôler la disponibilité des composants et leur date d’expiration.',
        'Vérifier le coût matière, les frais supplémentaires et le prix suggéré.',
        'Confirmer la quantité prévue et le lot de sortie.'
      ],
      statusReady: 'Prêt — la recherche filtre uniquement les lignes visibles des tableaux de fabrication.',
      statusNoAction: 'Le bouton correspondant n’est pas visible. Le panneau a fait défiler vers la section la plus proche.',
      statusAction: 'Action ouverte depuis l’interface existante.',
      statusJump: 'Section demandée affichée.',
      statusFiltered: 'Lignes correspondantes',
      noRows: '—',
      shortcuts: 'Raccourcis',
      emptySearch: 'Aucune ligne correspondante dans les tableaux actuels.'
    },
    en: {
      title: 'Manufacturing & Production Center',
      subtitle: 'Quick access to recipes, production orders, and pre-production checks.',
      newOrder: 'New production order',
      recipes: 'Manage recipes',
      orders: 'Production orders',
      ingredients: 'Components & batches',
      statRecipes: 'Recipes shown',
      statOrders: 'Orders shown',
      statShortages: 'Rows to review',
      search: 'Search manufacturing tables: product, recipe, order number…',
      clear: 'Clear',
      checklist: 'Pre-production checklist',
      checks: [
        'Verify the recipe, output quantity, and unit.',
        'Check component availability and batch expiry dates.',
        'Review material cost, extra costs, and suggested selling price.',
        'Confirm the planned quantity and output batch.'
      ],
      statusReady: 'Ready — search filters rows in the manufacturing tables only.',
      statusNoAction: 'The matching action button is not visible. Scrolled to the closest section; use the original screen controls if needed.',
      statusAction: 'Opened the action through the existing interface.',
      statusJump: 'Scrolled to the requested section.',
      statusFiltered: 'Matching rows',
      noRows: '—',
      shortcuts: 'Shortcuts',
      emptySearch: 'No matching rows in the current tables.'
    }
  };

  function currentLanguage() {
    var value = '';
    try {
      value = (window.NANOI18N && typeof window.NANOI18N.current === 'function' ? window.NANOI18N.current() : '') ||
        window.currentLanguage || localStorage.getItem('nanoLanguage') || localStorage.getItem('appLanguage') ||
        document.documentElement.lang || 'ar';
    } catch (_) { value = document.documentElement.lang || 'ar'; }
    value = String(value).toLowerCase();
    return value.indexOf('fr') === 0 ? 'fr' : (value.indexOf('en') === 0 ? 'en' : 'ar');
  }

  function addStyles() {
    if (document.getElementById('nanoMfgCenterStyleV221')) return;
    var style = document.createElement('style');
    style.id = 'nanoMfgCenterStyleV221';
    style.textContent = [
      '#nanoManufacturingCenterV221{width:100%;box-sizing:border-box;margin:0 0 18px;padding:18px;border:1px solid #dbe5f2;border-radius:18px;background:linear-gradient(135deg,#fff 0%,#f7faff 100%);color:#172b4d;box-shadow:0 5px 18px rgba(15,45,90,.06);font-family:inherit}',
      '#nanoManufacturingCenterV221 *{box-sizing:border-box}',
      '#nanoManufacturingCenterV221 .nano-mfg-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}',
      '#nanoManufacturingCenterV221 .nano-mfg-title{font-size:clamp(18px,2vw,24px);font-weight:900;line-height:1.35;margin:0;color:#122a4a}',
      '#nanoManufacturingCenterV221 .nano-mfg-subtitle{font-size:12px;line-height:1.8;margin:5px 0 0;color:#60728c;font-weight:600}',
      '#nanoManufacturingCenterV221 .nano-mfg-chip{display:inline-flex;align-items:center;gap:6px;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;border-radius:999px;padding:6px 10px;font-size:11px;font-weight:800;white-space:nowrap}',
      '#nanoManufacturingCenterV221 .nano-mfg-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}',
      '#nanoManufacturingCenterV221 button{font:inherit;cursor:pointer;transition:transform .15s ease,background .15s ease,border-color .15s ease}',
      '#nanoManufacturingCenterV221 .nano-mfg-btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border-radius:11px;padding:9px 13px;border:1px solid #d7e2f0;background:#fff;color:#28415f;font-size:12px;font-weight:800;min-height:38px}',
      '#nanoManufacturingCenterV221 .nano-mfg-btn:hover{transform:translateY(-1px);border-color:#93c5fd;background:#f0f7ff}',
      '#nanoManufacturingCenterV221 .nano-mfg-btn-primary{background:#1d4ed8;border-color:#1d4ed8;color:#fff}',
      '#nanoManufacturingCenterV221 .nano-mfg-btn-primary:hover{background:#1e40af;border-color:#1e40af}',
      '#nanoManufacturingCenterV221 .nano-mfg-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:15px}',
      '#nanoManufacturingCenterV221 .nano-mfg-stat{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 14px;border:1px solid #e0e8f2;border-radius:13px;background:rgba(255,255,255,.9);min-width:0}',
      '#nanoManufacturingCenterV221 .nano-mfg-stat span{font-size:12px;font-weight:800;color:#5b6f89;line-height:1.5}',
      '#nanoManufacturingCenterV221 .nano-mfg-stat strong{font-size:20px;font-weight:900;color:#164e9a;font-variant-numeric:tabular-nums}',
      '#nanoManufacturingCenterV221 .nano-mfg-stat[data-stat=shortages] strong{color:#b45309}',
      '#nanoManufacturingCenterV221 .nano-mfg-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:13px}',
      '#nanoManufacturingCenterV221 .nano-mfg-search-wrap{display:flex;align-items:center;gap:8px;flex:1 1 300px;border:1px solid #cfdae8;border-radius:11px;background:#fff;padding:0 11px;min-height:41px}',
      '#nanoManufacturingCenterV221 .nano-mfg-search-wrap input{width:100%;min-width:0;border:0;outline:0;background:transparent;color:#1f344f;font:inherit;font-size:12px;padding:10px 0}',
      '#nanoManufacturingCenterV221 .nano-mfg-status{font-size:11px;line-height:1.7;color:#61748d;font-weight:700;margin:10px 1px 0;min-height:18px}',
      '#nanoManufacturingCenterV221 .nano-mfg-checks{margin-top:12px;border-top:1px solid #e4ebf3;padding-top:10px}',
      '#nanoManufacturingCenterV221 .nano-mfg-checks summary{cursor:pointer;font-size:12px;font-weight:900;color:#274665;padding:4px 0}',
      '#nanoManufacturingCenterV221 .nano-mfg-checks ul{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 18px;margin:10px 0 2px;padding-inline-start:20px;color:#596d85;font-size:11px;line-height:1.8;font-weight:650}',
      '#nanoManufacturingCenterV221 .nano-mfg-checks li::marker{color:#0f9f6e}',
      '#nanoManufacturingCenterV221 .nano-mfg-flash{outline:2px solid #93c5fd;outline-offset:3px;border-radius:10px}',
      '@media(max-width:900px){#nanoManufacturingCenterV221{padding:14px}.nano-mfg-stats{grid-template-columns:1fr 1fr!important}.nano-mfg-checks ul{grid-template-columns:1fr!important}}',
      '@media(max-width:540px){#nanoManufacturingCenterV221 .nano-mfg-stats{grid-template-columns:1fr!important}#nanoManufacturingCenterV221 .nano-mfg-stat strong{font-size:18px}#nanoManufacturingCenterV221 .nano-mfg-btn{flex:1 1 145px}}',
      '@media(prefers-color-scheme:dark){#nanoManufacturingCenterV221{background:linear-gradient(135deg,#111c2c,#17243a);border-color:#34445d;color:#e5edf8}#nanoManufacturingCenterV221 .nano-mfg-title{color:#f3f7ff}#nanoManufacturingCenterV221 .nano-mfg-subtitle,#nanoManufacturingCenterV221 .nano-mfg-status{color:#a7b7ce}#nanoManufacturingCenterV221 .nano-mfg-stat{background:#18263b;border-color:#34445d}#nanoManufacturingCenterV221 .nano-mfg-stat span{color:#b2c2d8}#nanoManufacturingCenterV221 .nano-mfg-stat strong{color:#93c5fd}#nanoManufacturingCenterV221 .nano-mfg-btn,#nanoManufacturingCenterV221 .nano-mfg-search-wrap{background:#17243a;border-color:#394a64;color:#e5edf8}#nanoManufacturingCenterV221 .nano-mfg-search-wrap input{color:#e5edf8}#nanoManufacturingCenterV221 .nano-mfg-checks{border-color:#34445d}#nanoManufacturingCenterV221 .nano-mfg-checks summary{color:#dbeafe}#nanoManufacturingCenterV221 .nano-mfg-checks ul{color:#afc0d6}}'
    ].join('');
    document.head.appendChild(style);
  }

  function visible(el) {
    if (!el || el.hidden) return false;
    var cs = window.getComputedStyle ? window.getComputedStyle(el) : null;
    return !cs || (cs.display !== 'none' && cs.visibility !== 'hidden');
  }

  function getRows(kind, root, panel) {
    var tables = Array.prototype.slice.call(root.querySelectorAll('table')).filter(function (table) { return !panel.contains(table); });
    var found = [];
    var headingTerms = {
      recipes: /recipe|recipes|recette|recettes|تركيبة|تركيبات|وصفة|الوصفات/i,
      orders: /production|order|orders|ordre|ordres|أمر إنتاج|أوامر الإنتاج|الإنتاج|الإنتاجات/i
    };
    tables.forEach(function (table) {
      var head = table.querySelector('thead');
      var label = (table.getAttribute('aria-label') || '') + ' ' + (table.querySelector('caption') ? table.querySelector('caption').textContent : '') + ' ' + (head ? head.textContent : '');
      var headings = Array.prototype.slice.call(root.querySelectorAll('h1,h2,h3,h4')).filter(function (h) { return !panel.contains(h) && (h.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING); });
      if (headings.length) label = headings[headings.length - 1].textContent + ' ' + label;
      if (!headingTerms[kind].test(label)) return;
      Array.prototype.slice.call(table.querySelectorAll('tbody tr')).forEach(function (row) {
        if (row.textContent.trim() && !row.querySelector('td[colspan]')) found.push(row);
      });
    });
    return found;
  }

  function updateStats(root, panel) {
    var recipes = getRows('recipes', root, panel);
    var orders = getRows('orders', root, panel);
    var bodyRows = Array.prototype.slice.call(root.querySelectorAll('tbody tr')).filter(function (row) {
      return !panel.contains(row) && row.textContent.trim() && !row.querySelector('td[colspan]');
    });
    var shortageRows = bodyRows.filter(function (row) {
      return /نقص|ناقص|غير متوفر|غير كاف|منتهي الصلاحية|rupture|insuffisant|shortage|expired|out of stock/i.test(row.textContent);
    });
    var r = panel.querySelector('[data-value=recipes]');
    var o = panel.querySelector('[data-value=orders]');
    var s = panel.querySelector('[data-value=shortages]');
    var t = panel.querySelector('[data-action-status]');
    if (r) r.textContent = recipes.length ? String(recipes.length) : '—';
    if (o) o.textContent = orders.length ? String(orders.length) : '—';
    if (s) s.textContent = String(shortageRows.length);
    if (t && !panel.dataset.hasSearched) t.textContent = dictionaries[currentLanguage()].statusReady;
  }

  function renderPanel(root, panel) {
    var lang = currentLanguage();
    var d = dictionaries[lang];
    var oldSearch = panel.querySelector('input') ? panel.querySelector('input').value : '';
    panel.dir = lang === 'ar' ? 'rtl' : 'ltr';
    panel.lang = lang;
    panel.innerHTML =
      '<div class="nano-mfg-head"><div><div class="nano-mfg-chip">⚙ ' + d.shortcuts + '</div><h2 class="nano-mfg-title">' + d.title + '</h2><p class="nano-mfg-subtitle">' + d.subtitle + '</p></div></div>' +
      '<div class="nano-mfg-actions">' +
      '<button type="button" class="nano-mfg-btn nano-mfg-btn-primary" data-action="new-order">＋ ' + d.newOrder + '</button>' +
      '<button type="button" class="nano-mfg-btn" data-action="recipes">▦ ' + d.recipes + '</button>' +
      '<button type="button" class="nano-mfg-btn" data-action="orders">☷ ' + d.orders + '</button>' +
      '<button type="button" class="nano-mfg-btn" data-action="ingredients">◈ ' + d.ingredients + '</button>' +
      '</div>' +
      '<div class="nano-mfg-stats">' +
      '<div class="nano-mfg-stat" data-stat="recipes"><span>' + d.statRecipes + '</span><strong data-value="recipes">—</strong></div>' +
      '<div class="nano-mfg-stat" data-stat="orders"><span>' + d.statOrders + '</span><strong data-value="orders">—</strong></div>' +
      '<div class="nano-mfg-stat" data-stat="shortages"><span>' + d.statShortages + '</span><strong data-value="shortages">0</strong></div>' +
      '</div>' +
      '<div class="nano-mfg-tools"><label class="nano-mfg-search-wrap" aria-label="' + d.search + '"><span>⌕</span><input type="search" data-mfg-search placeholder="' + d.search + '" autocomplete="off"></label><button type="button" class="nano-mfg-btn" data-action="clear">' + d.clear + '</button></div>' +
      '<div class="nano-mfg-status" role="status" aria-live="polite" data-action-status>' + d.statusReady + '</div>' +
      '<details class="nano-mfg-checks"><summary>' + d.checklist + '</summary><ul>' +
      d.checks.map(function (item) { return '<li>' + item + '</li>'; }).join('') +
      '</ul></details>';
    var input = panel.querySelector('[data-mfg-search]');
    if (input) input.value = oldSearch;
    function status(text) {
      var node = panel.querySelector('[data-action-status]');
      if (node) node.textContent = text;
    }
    function jump(pattern) {
      var candidates = Array.prototype.slice.call(root.querySelectorAll('h1,h2,h3,h4,legend,table,[data-mfg-section]')).filter(function (el) {
        return !panel.contains(el) && visible(el) && pattern.test((el.textContent || '') + ' ' + (el.getAttribute('aria-label') || ''));
      });
      if (!candidates.length) return false;
      var target = candidates[0];
      if (target.tagName === 'TABLE') target = target.closest('.overflow-auto,.overflow-y-auto,.overflow-x-auto,.rounded-xl,.rounded-2xl,div') || target;
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target.classList.add('nano-mfg-flash');
      window.setTimeout(function () { target.classList.remove('nano-mfg-flash'); }, 1600);
      return true;
    }
    function doAction(action) {
      var patterns = action === 'new-order'
        ? /أمر إنتاج|إنتاج جديد|production order|new production|create production|ordre de production|nouvel ordre/i
        : /تركيبة|وصفة|recipe|recette/i;
      var positive = action === 'new-order'
        ? /إضافة|إنشاء|جديد|new|create|add|plus|إنتاج سريع/i
        : /إضافة|إنشاء|جديد|add|create|new|plus/i;
      var negatives = /إلغاء|حذف|تعديل|عرض|تفاصيل|تأكيد|عكس|طباعة|cancel|delete|edit|view|detail|confirm|reverse|print/i;
      var buttons = Array.prototype.slice.call(root.querySelectorAll('button,[role=button]')).filter(function (el) {
        return !panel.contains(el) && visible(el);
      });
      var candidate = action === 'recipes' || action === 'orders' || action === 'ingredients' ? null : buttons.find(function (el) {
        var label = (el.innerText || el.textContent || '') + ' ' + (el.title || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('onclick') || '');
        return patterns.test(label) && positive.test(label) && !negatives.test(label);
      });
      if (candidate) {
        candidate.click();
        status(d.statusAction);
        return;
      }
      var moved = action === 'new-order' || action === 'orders'
        ? jump(/أمر إنتاج|أوامر الإنتاج|production order|orders|ordre de production/i)
        : action === 'recipes'
          ? jump(/تركيبة|وصفة|recipes|recettes/i)
          : jump(/مكوّن|مكونات|مواد خام|دفعات|ingredient|composant|batch|lot/i);
      status(moved ? d.statusJump : d.statusNoAction);
    }
    Array.prototype.slice.call(panel.querySelectorAll('[data-action]')).forEach(function (button) {
      button.addEventListener('click', function () {
        var action = button.getAttribute('data-action');
        if (action === 'clear') {
          if (input) { input.value = ''; input.dispatchEvent(new Event('input', { bubbles: true })); input.focus(); }
          status(d.statusReady);
          return;
        }
        if (action === 'recipes' || action === 'orders' || action === 'ingredients') {
          doAction(action);
          return;
        }
        doAction(action);
      });
    });
    if (input) input.addEventListener('input', function () {
      var query = input.value.trim().toLowerCase();
      var rows = Array.prototype.slice.call(root.querySelectorAll('tbody tr')).filter(function (row) { return !panel.contains(row); });
      var shown = 0;
      rows.forEach(function (row) {
        if (!row.hasAttribute('data-nano-mfg-was-hidden')) row.setAttribute('data-nano-mfg-was-hidden', row.hidden ? '1' : '0');
        var matches = !query || (row.textContent || '').toLowerCase().indexOf(query) !== -1;
        row.hidden = query ? (!matches || row.getAttribute('data-nano-mfg-was-hidden') === '1') : row.getAttribute('data-nano-mfg-was-hidden') === '1';
        if (!row.hidden && row.textContent.trim()) shown++;
      });
      panel.dataset.hasSearched = query ? '1' : '';
      status(query ? d.statusFiltered + ': ' + shown : d.statusReady);
      updateStats(root, panel);
      if (query && shown === 0) status(d.emptySearch);
    });
    updateStats(root, panel);
  }

  function boot() {
    var root = document.getElementById('mfgRoot');
    if (!root) return;
    addStyles();
    var panel = document.getElementById('nanoManufacturingCenterV221');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'nanoManufacturingCenterV221';
      panel.setAttribute('aria-label', dictionaries[currentLanguage()].title);
      root.prepend(panel);
      renderPanel(root, panel);
    } else if (panel.lang !== currentLanguage()) {
      renderPanel(root, panel);
    }
    updateStats(root, panel);
  }

  var root = document.getElementById('mfgRoot');
  if (root && window.MutationObserver) {
    var observer = new MutationObserver(function () {
      if (!document.getElementById('nanoManufacturingCenterV221') || document.getElementById('nanoManufacturingCenterV221').lang !== currentLanguage()) boot();
      else updateStats(root, document.getElementById('nanoManufacturingCenterV221'));
    });
    observer.observe(root, { childList: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
  window.addEventListener('nano-language-synchronized', boot);
  window.addEventListener('languagechange', boot);
})();
'''

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_asar(raw):
    magic, block, header_size, json_size = struct.unpack_from("<4I", raw)
    assert magic == 4 and block == header_size + 4, "Invalid ASAR header"
    tree = json.loads(raw[16:16 + json_size].decode("utf-8"))
    data_start = 8 + block
    entries = []
    def walk(node, prefix=""):
        for name, ent in node.get("files", {}).items():
            path = prefix + name
            if "files" in ent:
                walk(ent, path + "/")
            elif "offset" in ent and "size" in ent:
                start = data_start + int(ent["offset"])
                blob = raw[start:start + int(ent["size"])]
                assert len(blob) == int(ent["size"]), "Truncated ASAR entry: " + path
                entries.append((path, ent, blob))
    walk(tree)
    entries.sort(key=lambda item: int(item[1]["offset"]))
    return tree, entries

def main():
    if len(sys.argv) != 4:
        raise SystemExit("build-manufacturing-center-221.py BASE_PATCH.zip OUTPUT_PATCH.zip WORKDIR")
    base, output, workdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    assert sha(base.read_bytes()) == BASE_PATCH_SHA256, "Official v2.0.20 patch SHA-256 mismatch"
    with zipfile.ZipFile(base) as z:
        assert z.namelist() == ["payload/app.asar"], "Unexpected base patch contents"
        raw = z.read("payload/app.asar")
    assert sha(raw) == BASE_ASAR_SHA256, "Official v2.0.20 app.asar SHA-256 mismatch"
    tree, entries = read_asar(raw)
    out_data = bytearray()
    modified = []
    files = {}
    for path, ent, blob in entries:
        changed = False
        if path == "package.json":
            package = json.loads(blob.decode("utf-8"))
            assert package.get("version") == BASE_VERSION, "Expected package.json version " + BASE_VERSION
            package["version"] = NEW_VERSION
            blob = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            changed = True
        elif path == "renderer.js":
            src = blob.decode("utf-8")
            assert MARKER not in src, "Manufacturing screen marker already exists"
            assert "__nanoCartSpeechV202" in src, "Base app lost existing cart-price speech feature"
            assert "__nanoOperationalAnalyticsV217" in src, "Base app lost existing statistics feature"
            assert "NANO-HW1-" in src or "NANO-HW1-" in "".join(b.decode("utf-8", "ignore") for p, _, b in entries if p == "license-client.js"), "Base app lost hardware ID feature"
            src += "\n\n// " + MARKER + "\n" + MANUFACTURING_UI + "\n"
            blob = src.encode("utf-8")
            changed = True
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / "renderer.js").write_bytes(blob)
        files[path] = blob
        if changed:
            modified.append(path)
            if "integrity" in ent:
                ent["integrity"]["hash"] = sha(blob)
                integrity = ent["integrity"]
                block_size = int(integrity.get("blockSize", 4 * 1024 * 1024))
                integrity["blocks"] = [sha(blob[i:i + block_size]) for i in range(0, len(blob), block_size)]
        ent["offset"] = str(len(out_data))
        ent["size"] = len(blob)
        out_data.extend(blob)

    required = {"package.json", "index.html", "renderer.js", "manufacturing/manufacturing.js",
                "manufacturing/manufacturing-ui.js", "manufacturing/pos-produce.js"}
    missing = required - set(files)
    assert not missing, "Required ASAR files missing: " + ", ".join(sorted(missing))
    index = files["index.html"].decode("utf-8", "ignore")
    assert 'id="mfgRoot"' in index and 'id="manufacturingSection"' in index, "Manufacturing UI host was not found"
    manufacturing_ui = files["manufacturing/manufacturing-ui.js"].decode("utf-8", "ignore")
    assert len(manufacturing_ui) > 5000, "Manufacturing UI script appears incomplete"

    header = json.dumps(tree, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    padded = (len(header) + 7) & ~3
    final_asar = struct.pack("<4I", 4, padded + 4, padded, len(header)) + header + b"\0" * (padded - 4 - len(header)) + out_data
    _, check_entries = read_asar(final_asar)
    check_files = {p: b for p, _, b in check_entries}
    package = json.loads(check_files["package.json"].decode("utf-8"))
    renderer = check_files["renderer.js"].decode("utf-8")
    assert package.get("version") == NEW_VERSION, "Version mismatch after ASAR rebuild"
    assert MARKER in renderer and "nanoManufacturingCenterV221" in renderer and "MutationObserver" in renderer
    assert "__nanoCartSpeechV202" in renderer and "__nanoOperationalAnalyticsV217" in renderer
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("payload/app.asar", final_asar)
    with zipfile.ZipFile(output) as z:
        assert z.namelist() == ["payload/app.asar"]
        assert sha(z.read("payload/app.asar")) == sha(final_asar)
    print(json.dumps({
        "fromVersion": BASE_VERSION, "version": NEW_VERSION, "modifiedFiles": modified,
        "asarEntries": len(check_files), "appAsarSha256": sha(final_asar),
        "patchSha256": sha(output.read_bytes()), "sizeBytes": output.stat().st_size,
        "checks": ["manufacturing UI host exists", "live table search", "localized responsive command center",
                   "existing manufacturing operations retained", "existing license, stats and price speech retained"]
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
