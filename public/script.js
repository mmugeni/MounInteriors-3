let PRODUCTS = [
  {
    id: 1,
    name: 'Ceramic Planter',
    category: 'planters',
    categoryLabel: 'Planters',
    badge: 'New',
    image: 'images/ceramic planter.JPG',
    description: 'A beautifully hand-finished ceramic planter in warm terracotta tones. Perfect for succulents, small indoor plants, or as a standalone décor piece. Adds an earthy, calming touch to any shelf or windowsill.',
    sizes: [
      { value: 'Small', available: true },
      { value: 'Medium', available: true },
      { value: 'Large', available: false },
    ],
    prints: [
      { name: 'Terracotta', image: 'images/ceramic planter.JPG', available: true },
      { name: 'Sage Green', image: 'images/sage green ceramic.JPG', available: true },
      { name: 'Cream White', image: 'images/cream white.JPG', available: true },
    ],
  },
  {
    id: 2,
    name: 'Scented Candle',
    category: 'candles',
    categoryLabel: 'Candles',
    badge: 'Bestseller',
    image: 'images/candle5.jpeg',
    description: 'Hand-poured soy wax candle with a warm, long-lasting scent. Burns cleanly for up to 40 hours. Available in multiple signature MOUN fragrances. Perfect for creating a calm, welcoming atmosphere in any room.',
    sizes: [
      { value: 'Standard', available: true },
    ],
    prints: [
      { name: 'Vanilla & Sandalwood', image: 'images/candle4.jpeg', available: true },
      { name: 'Morning Brew', image: 'images/Morning brew candle .jpeg', available: true },
      { name: 'Virunga Mountains', image: 'images/Virunga Mountains candle.jpeg', available: true },
      { name: 'Lemongrass Tea', image: 'images/Lemongrass tea candle.jpeg', available: true },
    ],
  },
  {
    id: 3,
    name: 'Terracotta Vase',
    category: 'vases',
    categoryLabel: 'Vases',
    badge: 'Popular',
    image: 'images/terracotta vase.JPG',
    description: 'A statement terracotta vase inspired by traditional African pottery forms. Handcrafted with a matte finish that brings warmth and texture to any interior space. Use with dried botanicals or as a standalone sculptural piece.',
    sizes: [
      { value: 'Small', available: true },
      { value: 'Medium', available: true },
      { value: 'Tall', available: true },
    ],
    prints: [
      { name: 'Terracotta', image: 'images/terracotta vase.JPG', available: true },
      { name: 'Matte Black', image: 'images/matte black terracotta.JPG', available: true },
      { name: 'Sand Beige', image: 'images/Sand Beige vase.jpg', available: true },
    ],
  },
  {
    id: 4,
    name: 'Woven Basket',
    category: 'baskets',
    categoryLabel: 'Baskets',
    badge: 'Handmade',
    image: 'images/woven basket.WEBP',
    description: 'Handwoven by local Rwandan artisans using traditional weaving techniques. This storage basket doubles as a beautiful décor piece — use it for blankets, plants, or as a statement accent in your living room.',
    sizes: [
      { value: 'Small', available: true },
      { value: 'Medium', available: true },
      { value: 'Large', available: false },
    ],
    prints: [
      { name: 'Natural Straw', image: 'images/woven basket.WEBP', available: true },
      { name: 'Black & Natural', image: 'images/black and natural wooven basket.JPG', available: true },
    ],
  },
  {
    id: 5,
    name: 'Dried Botanical Bunch',
    category: 'accessories',
    categoryLabel: 'Accessories',
    badge: 'New',
    image: 'images/neutral pampas.JPG',
    description: 'A curated bunch of dried botanicals and pampas grass — zero maintenance, maximum impact. Pairs perfectly with our terracotta vases. Lasts for months with no watering required.',
    sizes: [
      { value: 'Standard', available: true },
    ],
    prints: [
      { name: 'Neutral Pampas', image: 'images/neutral pampas.JPG', available: true },
      { name: 'Russet & Brown', image: 'images/russet brown.JPG', available: true },
      { name: 'Ivory White', image: 'images/ivory white.JPG', available: true },
    ],
  },
  {
    id: 6,
    name: 'Rattan Wall Mirror',
    category: 'accessories',
    categoryLabel: 'Accessories',
    badge: 'Limited',
    image: 'images/natural rattan.JPG',
    description: 'A circular wall mirror framed in hand-woven natural rattan. Adds depth, light, and a bohemian warmth to any wall. Available in two sizes. Each piece is slightly unique due to the handmade nature of the rattan frame.',
    sizes: [
      { value: '40cm', available: true },
      { value: '60cm', available: true },
    ],
    prints: [
      { name: 'Natural Rattan', image: 'images/natural rattan.JPG', available: true },
      { name: 'Bleached White', image: 'images/bleached white.JPG', available: false },
    ],
  },
  {
    id: 7,
    name: 'Linen Throw Cushion',
    category: 'accessories',
    categoryLabel: 'Accessories',
    badge: 'New',
    image: 'images/sand beige.JPG',
    description: 'A soft linen throw cushion in muted, earthy tones designed to complement any sofa or bed. Removable cover for easy washing. The subtle texture adds warmth without overpowering your existing décor.',
    sizes: [
      { value: '40x40cm', available: true },
      { value: '50x50cm', available: true },
    ],
    prints: [
      { name: 'Sand Beige', image: 'images/sand beige.JPG', available: true },
      { name: 'Terracotta', image: 'images/terracotta pillow.JPG', available: true },
      { name: 'Sage Green', image: 'images/sage green.JPG', available: true },
      { name: 'Dusty Rose', image: 'images/dusty rose.JPG', available: false },
    ],
  },
  {
    id: 8,
    name: 'Wooden Tray Set',
    category: 'accessories',
    categoryLabel: 'Accessories',
    badge: 'New',
    image: 'images/light arcacia.JPG',
    description: 'A set of two nesting wooden trays in smooth acacia wood. Use on your coffee table to style candles and botanicals, or on your dresser for jewellery and daily essentials. A simple way to instantly elevate any surface.',
    sizes: [
      { value: 'Set of 2', available: true },
    ],
    prints: [
      { name: 'Light Acacia', image: 'images/light arcacia.JPG', available: true },
      { name: 'Dark Walnut', image: 'images/dark walnut.JPG', available: true },
    ],
  },
];

let WA_NUMBER = '250793299348';
const MAX_QTY = 2;

/* ----------------------------------------------------------------
   2. PAGE ROUTING
   ---------------------------------------------------------------- */
function showPage(pageId) {
  document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));

  const target = document.getElementById('page-' + pageId);
  if (target) target.classList.add('active');

  document.querySelectorAll('.nav__link').forEach((link) => {
    link.classList.toggle('active', link.dataset.page === pageId);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
  closeMobileNav();
  setupRevealObserver();
}
window.showPage = showPage;

/* ----------------------------------------------------------------
   3. PRODUCT CARD RENDERING
   ---------------------------------------------------------------- */
function createProductCard(product) {
  const card = document.createElement('article');
  card.className = 'product-card reveal';
  card.setAttribute('data-category', product.category);
  card.innerHTML = `
    <div class="product-card__img-wrap">
      <img class="product-card__img" src="${product.image}" alt="${product.name}" loading="lazy" />
      ${product.badge ? `<span class="product-card__badge">${product.badge}</span>` : ''}
    </div>
    <div class="product-card__body">
      <p class="product-card__category">${product.categoryLabel}</p>
      <h3 class="product-card__name">${product.name}</h3>
      <span class="product-card__btn">View Product</span>
    </div>
  `;
  card.addEventListener('click', () => openProduct(product));
  return card;
}

function renderProductGrid(containerId, products) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';
  products.forEach((p, i) => {
    const card = createProductCard(p);
    if (i % 4 === 1) card.classList.add('reveal-delay-1');
    if (i % 4 === 2) card.classList.add('reveal-delay-2');
    if (i % 4 === 3) card.classList.add('reveal-delay-3');
    container.appendChild(card);
  });

  setupRevealObserver();
}

renderProductGrid('featured-products', PRODUCTS.slice(0, 4));
renderProductGrid('shop-products', PRODUCTS);

/* ----------------------------------------------------------------
   4. PRODUCT DETAIL PAGE
   ---------------------------------------------------------------- */
let currentProduct = null;
let selectedPrint = null;
let selectedSize = null;
let selectedColour = null;
let currentQty = 1;

function openProduct(product) {
  currentProduct = product;
  selectedPrint = null;
  selectedSize = null;
  selectedColour = null;
  currentQty = 1;

  const mainImg = document.getElementById('product-main-img');
  const category = document.getElementById('product-category');
  const name = document.getElementById('product-name');
  const price = document.getElementById('product-price');
  const desc = document.getElementById('product-desc');
  const qtyDisplay = document.getElementById('qty-display');

  if (mainImg) {
    mainImg.src = product.image;
    mainImg.alt = product.name;
  }
  if (category) category.textContent = product.categoryLabel;
  if (name) name.textContent = product.name;
  if (price) {
    const hasPrice = product.price !== null && product.price !== undefined && product.price !== '';
    price.textContent = hasPrice ? 'RWF ' + Number(product.price).toLocaleString('en-US') : '';
    price.hidden = !hasPrice;
  }
  if (desc) desc.textContent = product.description;
  if (qtyDisplay) qtyDisplay.textContent = '1';

  const printLabel = document.getElementById('selected-print-label');
  const sizeLabel = document.getElementById('selected-size-label');
  const colourLabel = document.getElementById('selected-colour-label');
  const printOosMsg = document.getElementById('print-oos-msg');
  const sizeOosMsg = document.getElementById('size-oos-msg');
  const colourOosMsg = document.getElementById('colour-oos-msg');

  if (printLabel) printLabel.textContent = '';
  if (sizeLabel) sizeLabel.textContent = '';
  if (colourLabel) colourLabel.textContent = '';

  if (printOosMsg) printOosMsg.hidden = true;
  if (sizeOosMsg) sizeOosMsg.hidden = true;
  if (colourOosMsg) colourOosMsg.hidden = true;

  setAvailability(true);

  buildThumbnailStrip(product);
  buildPrintSelector(product);
  buildColourSelector(product);
  buildSizeSelector(product);
  updateQtyNote();  /* set correct max qty note for this product */
  updateProductLinks(product.name);

  showPage('product');
}

function buildThumbnailStrip(product) {
  const strip = document.getElementById('product-thumbs');
  if (!strip) return;

  strip.innerHTML = '';

  /* Determine which array to use for thumbnails: prints or colours */
  const thumbSource = (product.prints && product.prints.length > 0)
    ? product.prints
    : (product.colours && product.colours.length > 0)
      ? product.colours
      : null;

  if (!thumbSource) {
    /* No variants — show single main product image */
    const thumb = document.createElement('button');
    thumb.type = 'button';
    thumb.className = 'thumb-btn active';
    thumb.innerHTML = `<img src="${product.image}" alt="${product.name}" />`;
    strip.appendChild(thumb);
    return;
  }

  thumbSource.forEach((item, index) => {
    const thumb = document.createElement('button');
    thumb.type = 'button';
    thumb.className = 'thumb-btn';
    thumb.setAttribute('aria-label', item.name);
    thumb.dataset.index = index;
    thumb.innerHTML =
      `<img src="${item.image}" alt="${item.name}" onerror="this.src='${product.image}'" />` +
      (!item.available ? '<span class="thumb-oos-overlay">&#x2715;</span>' : '');

    thumb.addEventListener('click', () => {
      const mainImg = document.getElementById('product-main-img');
      if (mainImg) mainImg.src = item.image;

      strip.querySelectorAll('.thumb-btn').forEach((b) => b.classList.remove('active'));
      thumb.classList.add('active');

      /* Sync print selector if this product uses prints */
      if (product.prints && product.prints.length > 0) {
        syncPrintSelection(index, item);
      }
      /* Sync earring list if this product uses colours */
      if (product.colours && product.colours.length > 0) {
        const listRows = document.querySelectorAll('.earring-list-row');
        listRows.forEach((r) => r.classList.remove('active'));
        if (listRows[index]) listRows[index].click();
      }
    });

    strip.appendChild(thumb);
  });

  /* Auto-activate first available */
  let firstAvail = thumbSource.findIndex((t) => t.available);
  if (firstAvail === -1) firstAvail = 0;

  const thumbBtns = strip.querySelectorAll('.thumb-btn');
  if (thumbBtns[firstAvail]) thumbBtns[firstAvail].classList.add('active');

  const mainImg = document.getElementById('product-main-img');
  if (mainImg) mainImg.src = thumbSource[firstAvail].image;

  /* Only sync print selection here — colour selection is handled by buildColourSelector */
  if (product.prints && product.prints.length > 0) {
    syncPrintSelection(firstAvail, product.prints[firstAvail]);
  }
}

function buildPrintSelector(product) {
  const group = document.getElementById('print-selector-group');
  const options = document.getElementById('print-options');
  const oosMsg = document.getElementById('print-oos-msg');

  if (!group || !options || !oosMsg) return;

  if (!product.prints || product.prints.length === 0) {
    group.hidden = true;
    return;
  }

  group.hidden = false;
  oosMsg.hidden = true;
  options.innerHTML = '';

  product.prints.forEach((print, index) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'print-swatch-btn' + (!print.available ? ' out-of-stock' : '');
    btn.setAttribute('aria-label', print.name + (!print.available ? ' (Out of Stock)' : ''));
    btn.title = print.name + (!print.available ? ' -- Out of Stock' : '');
    btn.innerHTML =
      `<img src="${print.image}" alt="${print.name}" onerror="this.style.background='#D5C8B5'" />` +
      (!print.available ? '<span class="swatch-oos-x">&#x2715;</span>' : '');

    btn.addEventListener('click', () => {
      const strip = document.getElementById('product-thumbs');
      const thumbs = strip ? strip.querySelectorAll('.thumb-btn') : [];
      thumbs.forEach((b) => b.classList.remove('active'));
      if (thumbs[index]) thumbs[index].classList.add('active');

      const mainImg = document.getElementById('product-main-img');
      if (mainImg) mainImg.src = print.image;

      syncPrintSelection(index, print);
    });

    options.appendChild(btn);
  });
}

function syncPrintSelection(index, print) {
  const options = document.getElementById('print-options');
  const label = document.getElementById('selected-print-label');
  const oosMsg = document.getElementById('print-oos-msg');

  if (options) {
    options.querySelectorAll('.print-swatch-btn').forEach((b, i) => {
      b.classList.toggle('active', i === index);
    });
  }

  selectedPrint = print;
  if (label) label.textContent = '-- ' + print.name;

  if (oosMsg) {
    if (print.available === false) {
      oosMsg.hidden = false;
    } else {
      oosMsg.hidden = true;
    }
  }

  setAvailability(print.available);
  updateQtyNote();  /* refresh max qty note and clamp currentQty for this print */
  updateProductLinks(currentProduct ? currentProduct.name : '');
}

function buildColourSelector(product) {
  const group = document.getElementById('colour-selector-group');
  const options = document.getElementById('colour-options');
  const oosMsg = document.getElementById('colour-oos-msg');

  if (!group || !options || !oosMsg) return;

  if (!product.colours || product.colours.length === 0) {
    group.hidden = true;
    return;
  }

  group.hidden = false;
  oosMsg.hidden = true;

  /* Switch the label to say "Select Style" for earrings */
  const labelEl = group.querySelector('.option-label');
  if (labelEl) {
    /* Preserve the selected-label span inside it */
    const selectedSpan = labelEl.querySelector('.option-selected-label');
    labelEl.textContent = 'Select Style ';
    if (selectedSpan) labelEl.appendChild(selectedSpan);
  }

  /* Build as a list: each row = small image + earring name */
  options.className = 'colour-options colour-options--list';
  options.innerHTML = '';

  product.colours.forEach((colour) => {
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'earring-list-row' + (!colour.available ? ' out-of-stock' : '');

    row.innerHTML =
      /* Thumbnail image */
      '<div class="earring-list-row__img-wrap">' +
        '<img src="' + colour.image + '" alt="' + colour.name + '" ' +
             'onerror="this.src=\'' + product.image + '\'" />' +
        (!colour.available ? '<span class="earring-list-row__oos-x">&#x2715;</span>' : '') +
      '</div>' +
      /* Name + availability tag */
      '<div class="earring-list-row__info">' +
        '<span class="earring-list-row__name">' + colour.name + '</span>' +
        (!colour.available
          ? '<span class="earring-list-row__tag earring-list-row__tag--oos">Out of Stock</span>'
          : '<span class="earring-list-row__tag earring-list-row__tag--avail">Available</span>') +
      '</div>' +
      /* Checkmark shown when selected */
      '<span class="earring-list-row__check" aria-hidden="true">&#10003;</span>';

    row.addEventListener('click', () => {
      /* Deselect all rows */
      options.querySelectorAll('.earring-list-row').forEach((b) => b.classList.remove('active'));
      row.classList.add('active');

      /* Update main product image to this earring's photo */
      const mainImg = document.getElementById('product-main-img');
      if (mainImg) mainImg.src = colour.image;

      /* Update the left thumbnail strip too */
      const strip = document.getElementById('product-thumbs');
      if (strip) {
        strip.querySelectorAll('.thumb-btn').forEach((b) => b.classList.remove('active'));
        /* Find the matching thumb by index */
        const idx = product.colours.indexOf(colour);
        const thumb = strip.querySelectorAll('.thumb-btn')[idx];
        if (thumb) thumb.classList.add('active');
      }

      selectedColour = colour.name;

      const label = document.getElementById('selected-colour-label');
      if (label) label.textContent = '-- ' + colour.name;

      if (oosMsg) {
        oosMsg.hidden = colour.available !== false;
      }

      setAvailability(colour.available);
      updateQtyNote();
      updateProductLinks(currentProduct ? currentProduct.name : '');
    });

    options.appendChild(row);
  });

  /* Auto-select the first available earring */
  const firstAvail = product.colours.findIndex((c) => c.available);
  const allRows = options.querySelectorAll('.earring-list-row');
  if (firstAvail >= 0 && allRows[firstAvail]) {
    allRows[firstAvail].click();
  }
}

function buildSizeSelector(product) {
  const group = document.getElementById('size-selector-group');
  const options = document.getElementById('size-options');
  const oosMsg = document.getElementById('size-oos-msg');

  if (!group || !options || !oosMsg) return;

  if (!product.sizes || product.sizes.length === 0) {
    group.hidden = true;
    return;
  }

  group.hidden = false;
  oosMsg.hidden = true;
  options.innerHTML = '';

  product.sizes.forEach((size) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'size-btn' + (!size.available ? ' out-of-stock' : '');
    btn.textContent = size.value;
    btn.dataset.size = size.value;

    btn.addEventListener('click', () => {
      options.querySelectorAll('.size-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      selectedSize = size.value;

      const label = document.getElementById('selected-size-label');
      if (label) label.textContent = '-- ' + size.value;

      if (oosMsg) {
        if (size.available === false) {
          oosMsg.hidden = false;
        } else {
          oosMsg.hidden = true;
        }
      }

      setAvailability(size.available);
      updateProductLinks(currentProduct ? currentProduct.name : '');
    });

    options.appendChild(btn);
  });

  const firstAvail = product.sizes.findIndex((s) => s.available);
  const allBtns = options.querySelectorAll('.size-btn');
  if (firstAvail >= 0 && allBtns[firstAvail]) {
    allBtns[firstAvail].click();
  }
}

function setAvailability(isAvailable) {
  const badge = document.getElementById('product-availability');
  const text = document.getElementById('avail-text');
  if (!badge || !text) return;

  badge.classList.toggle('unavailable', !isAvailable);
  text.textContent = isAvailable ? 'Available' : 'Out of Stock';
}

/* ----------------------------------------------------------------
   HELPER: getMaxQty()
   Returns the effective max quantity for the current selection:
   - If the product has a product-level maxQty (accessories), use that
   - If the selected print has a maxQty, use that
   - Otherwise fall back to the global MAX_QTY constant
   ---------------------------------------------------------------- */
function getMaxQty() {
  /* Product-level override (e.g. accessories always max 1) */
  if (currentProduct && currentProduct.maxQty !== undefined) {
    return currentProduct.maxQty;
  }
  /* Per-print override */
  if (selectedPrint && selectedPrint.maxQty !== undefined) {
    return selectedPrint.maxQty;
  }
  return MAX_QTY;
}

/* Update the quantity note text to show the correct maximum */
function updateQtyNote() {
  const note = document.querySelector('.qty-max-note');
  if (note) {
    const max = getMaxQty();
    note.textContent = max === 1 ? 'Maximum 1 per item' : 'Maximum ' + max + ' per item';
  }
  /* Also clamp currentQty if it now exceeds the new max */
  if (currentQty > getMaxQty()) {
    currentQty = getMaxQty();
    const display = document.getElementById('qty-display');
    if (display) display.textContent = currentQty;
  }
}
document.getElementById('qty-decrease')?.addEventListener('click', () => {
  if (currentQty > 1) {
    currentQty--;
    const qtyDisplay = document.getElementById('qty-display');
    if (qtyDisplay) qtyDisplay.textContent = currentQty;
    updateProductLinks(currentProduct ? currentProduct.name : '');
  }
});

document.getElementById('qty-increase')?.addEventListener('click', () => {
  if (currentQty < getMaxQty()) {
    currentQty++;
    const qtyDisplay = document.getElementById('qty-display');
    if (qtyDisplay) qtyDisplay.textContent = currentQty;
    updateProductLinks(currentProduct ? currentProduct.name : '');
  } else {
    /* Flash the note to signal the limit */
    const note = document.querySelector('.qty-max-note');
    if (note) {
      note.classList.add('qty-max-flash');
      setTimeout(() => note.classList.remove('qty-max-flash'), 800);
    }
  }
});

function updateProductLinks(productName) {
  const printPart = selectedPrint ? ', Print: ' + selectedPrint.name : '';
  const sizePart = selectedSize ? ', Size: ' + selectedSize : '';
  const colourPart = selectedColour ? ', Colour: ' + selectedColour : '';
  const qtyPart = ' x' + currentQty;

  const orderMsg = encodeURIComponent(
    'Hello, I would like to order:\n' +
      productName +
      printPart +
      sizePart +
      colourPart +
      qtyPart +
      ' from MOUN'
  );

  const waBtn = document.getElementById('whatsapp-order-btn');
  if (waBtn) {
    waBtn.href = 'https://wa.me/' + WA_NUMBER + '?text=' + orderMsg;
  }

  const shareMessage = encodeURIComponent(
    'Check out this product on MOUN: ' +
      productName +
      printPart +
      sizePart +
      colourPart
  );

  const shareUrl = encodeURIComponent(window.location.href);

  const shareWa = document.getElementById('share-whatsapp');
  if (shareWa) {
    shareWa.href = 'https://wa.me/?text=' + shareMessage + '%20' + shareUrl;
  }

  const shareFb = document.getElementById('share-facebook');
  if (shareFb) {
    shareFb.href = 'https://www.facebook.com/sharer/sharer.php?u=' + shareUrl;
  }

  const shareIg = document.getElementById('share-instagram');
  if (shareIg) {
    shareIg.href =
      'https://www.instagram.com/moun.rw';
  }
}

/* ----------------------------------------------------------------
   5. SHOP FILTER LOGIC
   ---------------------------------------------------------------- */
document.querySelectorAll('.filter-btn').forEach((btn) => {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
    this.classList.add('active');

    const filter = this.dataset.filter;
    const filtered =
      filter === 'all' ? PRODUCTS : PRODUCTS.filter((p) => p.category === filter);

    renderProductGrid('shop-products', filtered);
  });
});

/* ----------------------------------------------------------------
   6. NAVIGATION
   ---------------------------------------------------------------- */
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('nav-links');
const siteHeader = document.getElementById('site-header');

function closeMobileNav() {
  navLinks?.classList.remove('open');
  hamburger?.classList.remove('open');
}

hamburger?.addEventListener('click', () => {
  navLinks?.classList.toggle('open');
  hamburger?.classList.toggle('open');
});

window.addEventListener(
  'scroll',
  () => {
    siteHeader?.classList.toggle('scrolled', window.scrollY > 20);
  },
  { passive: true }
);

/* ----------------------------------------------------------------
   7. CONTACT FORM
   ---------------------------------------------------------------- */
const contactForm = document.getElementById('contact-form');
const formSuccess = document.getElementById('form-success');

contactForm?.addEventListener('submit', (e) => {
  e.preventDefault();

  const name = document.getElementById('c-name')?.value.trim() || '';
  const email = document.getElementById('c-email')?.value.trim() || '';
  const message = document.getElementById('c-message')?.value.trim() || '';

  if (!name || !email || !message) {
    alert('Please fill in all fields.');
    return;
  }

  /* Stricter email validation:
     - must have @ with non-empty local part
     - domain must have at least one dot
     - TLD must be at least 2 characters (e.g. .com, .mu, .org)
     - rejects things like "you.example.com" (no @) or "user@domain" (no TLD) */
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    alert('Please enter a valid email address (e.g. name@example.com).');
    return;
  }

  console.log('Form submission:', { name, email, message });
  contactForm.reset();

  if (formSuccess) {
    formSuccess.hidden = false;
    setTimeout(() => {
      formSuccess.hidden = true;
    }, 5000);
  }
});

/* ----------------------------------------------------------------
   8. SCROLL REVEAL
   ---------------------------------------------------------------- */
function setupRevealObserver() {
  const revealItems = document.querySelectorAll('.reveal');
  if (!revealItems.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  revealItems.forEach((el) => observer.observe(el));
}

document
  .querySelectorAll(
    '.category-card, .value-card, .campus__text, .campus__image, .brand-story__inner, .about-story__text, .about-story__image'
  )
  .forEach((el) => el.classList.add('reveal'));

setupRevealObserver();

/* ----------------------------------------------------------------
   9. INITIAL PAGE LOAD
   ---------------------------------------------------------------- */
(function init() {
  const hash = window.location.hash.replace('#', '') || 'home';
  const validPages = ['home', 'shop', 'product', 'about', 'contact'];
  showPage(validPages.includes(hash) ? hash : 'home');
})();

/* ----------------------------------------------------------------
   10. DARK MODE
   ---------------------------------------------------------------- */
const darkToggleBtn = document.getElementById('dark-toggle');

function setDarkMode(isDark) {
  document.body.classList.toggle('dark', isDark);
  localStorage.setItem('moun-dark', isDark ? '1' : '0');
}

darkToggleBtn?.addEventListener('click', () => {
  setDarkMode(!document.body.classList.contains('dark'));
});

(function initDarkMode() {
  const saved = localStorage.getItem('moun-dark');
  if (saved === '1') {
    setDarkMode(true);
  }
})();

/* ----------------------------------------------------------------
   11. QUOTATION DRAWER SYSTEM
   ---------------------------------------------------------------- */

const cartDrawer  = document.getElementById('cart-drawer');
const cartOverlay = document.getElementById('cart-overlay');

function openCart() {
  cartDrawer?.classList.add('open');
  cartOverlay?.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCart() {
  cartDrawer?.classList.remove('open');
  cartOverlay?.classList.remove('open');
  document.body.style.overflow = '';
}

window.closeCart = closeCart;

document.getElementById('cart-btn')?.addEventListener('click', openCart);
cartOverlay?.addEventListener('click', closeCart);
document.getElementById('cart-close')?.addEventListener('click', closeCart);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeCart();
});

/* "Add to Cart" button on product page now opens the quotation drawer */
document.getElementById('add-to-cart-btn')?.addEventListener('click', () => {
  openCart();
});

function resetQuoteForm() {
  ['q-name','q-email','q-phone','q-rooms','q-details'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  ['q-service','q-budget','q-timeline'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.selectedIndex = 0;
  });
  const errEl = document.getElementById('quote-form-error');
  if (errEl) { errEl.textContent = ''; errEl.hidden = true; }
  const wrap = document.getElementById('quote-form-wrap');
  const success = document.getElementById('quote-success');
  if (wrap) wrap.style.display = '';
  if (success) success.hidden = true;
}

window.resetQuoteForm = resetQuoteForm;

async function submitQuotation() {
  const name     = document.getElementById('q-name')?.value.trim()    || '';
  const email    = document.getElementById('q-email')?.value.trim()   || '';
  const phone    = document.getElementById('q-phone')?.value.trim()   || '';
  const service  = document.getElementById('q-service')?.value        || '';
  const rooms    = document.getElementById('q-rooms')?.value.trim()   || '';
  const budget   = document.getElementById('q-budget')?.value         || '';
  const timeline = document.getElementById('q-timeline')?.value       || '';
  const details  = document.getElementById('q-details')?.value.trim() || '';

  const errEl = document.getElementById('quote-form-error');
  const btn   = document.getElementById('quote-submit-btn');

  if (!name || !email || !phone || !service || !details) {
    if (errEl) { errEl.textContent = 'Please fill in all required fields (marked with *).'; errEl.hidden = false; }
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    if (errEl) { errEl.textContent = 'Please enter a valid email address.'; errEl.hidden = false; }
    return;
  }

  if (errEl) errEl.hidden = true;
  if (btn) { btn.textContent = 'Sending…'; btn.classList.add('loading'); }

  const payload = { name, email, phone, service, rooms, budget, timeline, details };

  try {
    const res  = await fetch(`${API_BASE}/api/quotations`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Server error');

    // Success — send WhatsApp notification AND show success screen
    const msg =
      `Hello MOUN! I'd like to request a quotation.\n\n` +
      `Name: ${name}\nEmail: ${email}\nPhone: ${phone}\n` +
      `Service: ${service}\n` +
      (rooms    ? `Rooms: ${rooms}\n`       : '') +
      (budget   ? `Budget: ${budget}\n`     : '') +
      (timeline ? `Timeline: ${timeline}\n` : '') +
      `\nProject Details: ${details}`;

    window.open('https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg), '_blank');

    const wrap    = document.getElementById('quote-form-wrap');
    const success = document.getElementById('quote-success');
    if (wrap) wrap.style.display = 'none';
    if (success) success.hidden = false;

  } catch (err) {
    // Fallback: open WhatsApp with form data if backend is unreachable
    const msg =
      `Hello MOUN! I'd like to request a quotation.\n\n` +
      `Name: ${name}\nEmail: ${email}\nPhone: ${phone}\n` +
      `Service: ${service}\n` +
      (rooms    ? `Rooms: ${rooms}\n`       : '') +
      (budget   ? `Budget: ${budget}\n`     : '') +
      (timeline ? `Timeline: ${timeline}\n` : '') +
      `\nProject Details: ${details}`;

    window.open('https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg), '_blank');

    const wrap    = document.getElementById('quote-form-wrap');
    const success = document.getElementById('quote-success');
    if (wrap) wrap.style.display = 'none';
    if (success) success.hidden = false;

  } finally {
    if (btn) { btn.textContent = 'Send Quotation Request'; btn.classList.remove('loading'); }
  }
}

window.submitQuotation = submitQuotation;

function parsePrice(priceStr) {
  return parseInt(String(priceStr).replace(/[^0-9]/g, ''), 10) || 0;
}

/* ================================================================
   CHECKOUT SYSTEM
   Flow:
   1. User clicks Checkout → openCheckout() → page-checkout shown
   2. User picks Pickup or Delivery + area
   3. User clicks "Bank Transfer" → if no shipping chosen, show error
      else show bank details
   4. User uploads receipt → confirm button activates
   5. User clicks confirm → WhatsApp opens with full order details
   ================================================================ */

/* Shipping state */
let coMethod     = null;   /* 'pickup' | 'delivery' */
let coArea       = null;   /* e.g. 'Port Louis' */
let coAreaPrice  = 0;      /* delivery fee in Rs */
let coReceiptFile = null;  /* the uploaded File object */

/**
 * openCheckout()
 * Called when user clicks Checkout in the cart drawer.
 * Populates the order summary and resets the form state.
 */
function openCheckout() {
  /* Don't open if cart is empty */
  if (!cart || cart.length === 0) {
    showPage('shop');
    return;
  }

  /* Reset state */
  coMethod      = null;
  coArea        = null;
  coAreaPrice   = 0;
  coReceiptFile = null;

  /* Uncheck all radios */
  document.querySelectorAll('input[name="co-method"]').forEach(r => r.checked = false);
  document.querySelectorAll('input[name="co-area"]').forEach(r => r.checked = false);

  /* Hide dynamic sections */
  const deliveryAreas = document.getElementById('co-delivery-areas');
  if (deliveryAreas) deliveryAreas.hidden = true;

  const bankDetails = document.getElementById('co-bank-details');
  if (bankDetails) bankDetails.hidden = true;

  const methodError = document.getElementById('co-method-error');
  if (methodError) methodError.hidden = true;

  /* Hide & reset customer details card */
  const customerCard = document.getElementById('co-customer-card');
  if (customerCard) customerCard.hidden = true;
  const deliveryFields = document.getElementById('co-delivery-fields');
  if (deliveryFields) deliveryFields.hidden = true;
  const customerError = document.getElementById('co-customer-error');
  if (customerError) customerError.hidden = true;
  ['co-fullname','co-phone','co-delivery-address','co-delivery-note'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  /* Reset receipt upload */
  const receiptInput = document.getElementById('co-receipt-input');
  if (receiptInput) receiptInput.value = '';
  const uploadText = document.getElementById('co-upload-text');
  if (uploadText) uploadText.textContent = 'Click here to upload payment receipt';
  const uploadSuccess = document.getElementById('co-upload-success');
  if (uploadSuccess) uploadSuccess.hidden = true;
  coReceiptFile = null;
  const confirmBtn = document.getElementById('co-confirm-btn');
  if (confirmBtn) confirmBtn.disabled = true;

  /* Populate order summary */
  renderCheckoutSummary();

  showPage('checkout');
}

/* Expose globally for inline onclick */
window.openCheckout = openCheckout;

/**
 * renderCheckoutSummary()
 * Fills the right-side order summary panel with current cart items.
 */
function renderCheckoutSummary() {
  const itemsEl    = document.getElementById('co-order-items');
  const subtotalEl = document.getElementById('co-subtotal');
  const shippingEl = document.getElementById('co-shipping-display');
  const totalEl    = document.getElementById('co-total');

  if (!itemsEl) return;

  itemsEl.innerHTML = '';

  cart.forEach(item => {
    const row = document.createElement('div');
    row.className = 'co-order-item';
    row.innerHTML =
      `<img class="co-order-item__img" src="${item.image}" alt="${item.name}" />` +
      `<div class="co-order-item__info">` +
        `<p class="co-order-item__name">${item.name}</p>` +
        `<p class="co-order-item__meta">${item.options}</p>` +
        `<p class="co-order-item__qty">Qty: ${item.qty}</p>` +
      `</div>` +
      `<p class="co-order-item__price">${item.price}</p>`;
    itemsEl.appendChild(row);
  });

  const subtotal = cart.reduce((sum, i) => sum + parsePrice(i.price) * i.qty, 0);
  if (subtotalEl) subtotalEl.textContent = `RWF ` + subtotal.toLocaleString();
  if (shippingEl) shippingEl.textContent = coMethod ? (coMethod === 'pickup' ? 'Free' : `RWF ` + coAreaPrice) : '—';
  if (totalEl)    totalEl.textContent    = `RWF ` + (subtotal + coAreaPrice).toLocaleString();
}

/* ── Shipping method radio listeners ── */

document.getElementById('co-pickup-radio')?.addEventListener('change', () => {
  coMethod     = 'pickup';
  coArea       = 'African Leadership Campus, Kongo 105';
  coAreaPrice  = 0;

  const deliveryAreas = document.getElementById('co-delivery-areas');
  if (deliveryAreas) deliveryAreas.hidden = true;

  document.querySelectorAll('input[name="co-area"]').forEach(r => r.checked = false);

  const customerCard = document.getElementById('co-customer-card');
  if (customerCard) customerCard.hidden = false;
  const deliveryFields = document.getElementById('co-delivery-fields');
  if (deliveryFields) deliveryFields.hidden = true;

  renderCheckoutSummary();
  hideMethodError();
});

document.getElementById('co-delivery-radio')?.addEventListener('change', () => {
  coMethod    = 'delivery';
  coArea      = null;
  coAreaPrice = 0;

  const deliveryAreas = document.getElementById('co-delivery-areas');
  if (deliveryAreas) deliveryAreas.hidden = false;

  const customerCard = document.getElementById('co-customer-card');
  if (customerCard) customerCard.hidden = false;
  const deliveryFields = document.getElementById('co-delivery-fields');
  if (deliveryFields) deliveryFields.hidden = false;

  renderCheckoutSummary();
  hideMethodError();
});

/* Delivery area radio listeners */
document.querySelectorAll('input[name="co-area"]').forEach(radio => {
  radio.addEventListener('change', () => {
    coArea      = radio.value;
    coAreaPrice = parseInt(radio.dataset.price, 10) || 0;
    renderCheckoutSummary();
    hideMethodError();
  });
});

function hideMethodError() {
  const el = document.getElementById('co-method-error');
  if (el) el.hidden = true;
}

/* ── Merchant Account button ── */

document.getElementById('co-merchant-btn')?.addEventListener('click', () => {
  const hasMethod = coMethod !== null;
  const hasArea   = coMethod === 'pickup' || (coMethod === 'delivery' && coArea !== null);

  if (!hasMethod || !hasArea) {
    const err = document.getElementById('co-method-error');
    if (err) {
      err.textContent = coMethod === 'delivery' && !coArea
        ? 'Please select a delivery area to continue.'
        : 'You must select a shipping method to place your order.';
      err.hidden = false;
    }
    return;
  }

  /* Validate customer details */
  const fullName = document.getElementById('co-fullname')?.value.trim() || '';
  const phone    = document.getElementById('co-phone')?.value.trim() || '';
  const address  = document.getElementById('co-delivery-address')?.value.trim() || '';
  const customerError = document.getElementById('co-customer-error');

  if (!fullName || !phone || (coMethod === 'delivery' && !address)) {
    if (customerError) {
      customerError.textContent = coMethod === 'delivery' && !address
        ? 'Please enter your full name, phone number, and delivery address.'
        : 'Please enter your full name and phone number.';
      customerError.hidden = false;
    }
    document.getElementById('co-customer-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  if (customerError) customerError.hidden = true;

  const bankDetails = document.getElementById('co-bank-details');
  if (bankDetails) bankDetails.hidden = false;
  bankDetails?.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

/* ── Receipt upload ── */

document.getElementById('co-receipt-input')?.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  coReceiptFile = file;

  const uploadText    = document.getElementById('co-upload-text');
  const uploadSuccess = document.getElementById('co-upload-success');
  const filenameEl    = document.getElementById('co-upload-filename');
  const confirmBtn    = document.getElementById('co-confirm-btn');

  if (uploadText)    uploadText.textContent = 'Receipt selected ✓';
  if (filenameEl)    filenameEl.textContent = file.name;
  if (uploadSuccess) uploadSuccess.hidden   = false;
  if (confirmBtn)    confirmBtn.disabled    = false;
});

/* File input is triggered naturally by the <label for="co-receipt-input"> HTML attribute.
   No manual click listener needed — adding one causes a double-open on desktop
   and can block the native file picker on mobile browsers. */

/* ================================================================
   BACKEND API URL
   The Flask backend is deployed in the same Vercel project as this
   website, so it is always on the same address.
   ================================================================ */
const API_BASE = window.location.origin;

document.getElementById('co-confirm-btn')?.addEventListener('click', async () => {
  if (!coReceiptFile) return;

  const confirmBtn = document.getElementById('co-confirm-btn');
  const fullName   = document.getElementById('co-fullname')?.value.trim()           || '';
  const phone      = document.getElementById('co-phone')?.value.trim()              || '';
  const address    = document.getElementById('co-delivery-address')?.value.trim()   || '';
  const note       = document.getElementById('co-delivery-note')?.value.trim()      || '';

  const subtotal = cart.reduce((sum, i) => sum + parsePrice(i.price) * i.qty, 0);
  const total    = subtotal + coAreaPrice;

  /* Build the order payload */
  const orderData = {
    customer_name:   fullName,
    phone:           phone,
    delivery_method: coMethod,
    address:         coMethod === 'delivery' ? address : 'African Leadership Campus, Kongo 105',
    delivery_note:   note || null,
    total_amount:    total,
    items: cart.map(item => ({
      name:      item.name,
      options:   item.options,
      qty:       item.qty,
      price_int: parsePrice(item.price),
    })),
  };

  /* Build multipart form — order data as JSON + receipt file */
  const formData = new FormData();
  formData.append('order_data', JSON.stringify(orderData));
  formData.append('receipt', coReceiptFile, coReceiptFile.name);

  /* Disable button and show loading state */
  confirmBtn.disabled     = true;
  confirmBtn.textContent  = 'Saving order...';

  try {
    const res  = await fetch(`${API_BASE}/api/orders`, {
      method: 'POST',
      body:   formData,
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Server error');
    }

    /* Order saved — now build and send the WhatsApp message */
    const itemLines = cart.map(item =>
      `- ${item.name} (${item.options}) x${item.qty} -- ${item.price}`
    ).join('\n');

    const shippingLine = coMethod === 'pickup'
      ? `Shipping: Pickup -- African Leadership Campus, Kongo 105 (Free)`
      : `Shipping: Delivery to ${coArea} -- RWF ${coAreaPrice}`;

    const customerLines = coMethod === 'delivery'
      ? `Name: ${fullName}\nPhone: ${phone}\nDelivery Address: ${address}` +
        (note ? `\nDelivery Note: ${note}` : '')
      : `Name: ${fullName}\nPhone: ${phone}`;

    const message =
      `Hello MOUN! I have made payment for my order.\n\n` +
      `ORDER #${data.order_id}\n\n` +
      `CUSTOMER DETAILS:\n${customerLines}\n\n` +
      `ORDER DETAILS:\n${itemLines}\n\n` +
      `${shippingLine}\n` +
      `Subtotal: RWF ${subtotal.toLocaleString()}\n` +
      `Total Paid: RWF ${total.toLocaleString()}\n\n` +
      `Receipt uploaded and saved. Please confirm my order. Thank you!`;

    window.open('https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(message), '_blank');

    /* Clear cart and go home */
    cart = [];
    saveCart(cart);
    updateCartBadge();
    setTimeout(() => showPage('home'), 500);

  } catch (err) {
    /* If API fails, still let the customer send via WhatsApp so they're not stuck */
    console.error('Order save failed:', err);

    const itemLines = cart.map(item =>
      `- ${item.name} (${item.options}) x${item.qty} -- ${item.price}`
    ).join('\n');

    const shippingLine = coMethod === 'pickup'
      ? `Shipping: Pickup -- African Leadership Campus, Kongo 105 (Free)`
      : `Shipping: Delivery to ${coArea} -- RWF ${coAreaPrice}`;

    const customerLines = coMethod === 'delivery'
      ? `Name: ${fullName}\nPhone: ${phone}\nDelivery Address: ${address}` +
        (note ? `\nDelivery Note: ${note}` : '')
      : `Name: ${fullName}\nPhone: ${phone}`;

    const message =
      `Hello MOUN! I have made payment for my order.\n\n` +
      `CUSTOMER DETAILS:\n${customerLines}\n\n` +
      `ORDER DETAILS:\n${itemLines}\n\n` +
      `${shippingLine}\n` +
      `Subtotal: RWF ${subtotal.toLocaleString()}\n` +
      `Total Paid: RWF ${total.toLocaleString()}\n\n` +
      `Receipt uploaded: ${coReceiptFile.name}\n` +
      `Please confirm my order. Thank you!`;

    window.open('https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(message), '_blank');

    cart = [];
    saveCart(cart);
    updateCartBadge();
    setTimeout(() => showPage('home'), 500);

  } finally {
    confirmBtn.disabled    = false;
    confirmBtn.textContent = "I've Made Payment -- Send Order via WhatsApp";
  }
});

/* ================================================================
   ADMIN LOGIN
   Eye icon in navbar opens a password modal.
   Password is verified against the Flask backend.
   If correct, opens the admin dashboard in a new tab.
   ================================================================ */

const adminBtn          = document.getElementById('admin-btn');
const adminModalOverlay = document.getElementById('admin-modal-overlay');
const adminModalClose   = document.getElementById('admin-modal-close');
const adminLoginBtn     = document.getElementById('admin-login-btn');
const adminPasswordInput = document.getElementById('admin-password-input');
const adminModalError   = document.getElementById('admin-modal-error');

/* Open modal when eye icon is clicked */
adminBtn?.addEventListener('click', () => {
  window.open(`${API_BASE}/admin`, '_blank', 'noopener');
});

/* Close modal */
function closeAdminModal() {
  adminModalOverlay.hidden = true;
  adminPasswordInput.value = '';
  adminModalError.hidden   = true;
}

adminModalClose?.addEventListener('click', closeAdminModal);
adminModalOverlay?.addEventListener('click', (e) => {
  if (e.target === adminModalOverlay) closeAdminModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAdminModal();
});

/* Allow pressing Enter in the password field */
adminPasswordInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') adminLoginBtn.click();
});

/* Verify password and open dashboard */
adminLoginBtn?.addEventListener('click', async () => {
  const password = adminPasswordInput.value.trim();
  if (!password) return;

  adminLoginBtn.textContent = 'Checking...';
  adminLoginBtn.disabled    = true;
  adminModalError.hidden    = true;

  try {
    /* Test the password by calling the API — if it returns 401 the password is wrong */
    const res = await fetch(`${API_BASE}/api/orders?password=${encodeURIComponent(password)}`);

    if (res.ok) {
      /* Password correct — open dashboard in new tab */
      window.open(`${API_BASE}/admin?password=${encodeURIComponent(password)}`, '_blank');
      closeAdminModal();
    } else {
      /* Wrong password */
      adminModalError.hidden = false;
      adminPasswordInput.select();
    }
  } catch (err) {
    adminModalError.textContent = 'Could not connect to server. Make sure the backend is running.';
    adminModalError.hidden = false;
  } finally {
    adminLoginBtn.textContent = 'Open Dashboard';
    adminLoginBtn.disabled    = false;
  }
});
/* ============================================================
   PORTFOLIO — filter + modal
============================================================ */
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.pf-filter');
  if (!btn) return;
  document.querySelectorAll('.pf-filter').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const filter = btn.dataset.filter;
  const cards  = document.querySelectorAll('.pf-card');
  let visible  = 0;
  cards.forEach(card => {
    const match = filter === 'all' || card.dataset.category === filter;
    card.classList.toggle('hidden', !match);
    if (match) visible++;
  });
  const el = document.getElementById('pf-showing');
  if (el) el.textContent = `Showing ${visible} of ${cards.length}`;
});

function openPfModal(card) {
  const imgDiv   = card.querySelector('.pf-card__img');
  const modalImg = document.getElementById('pf-modal-img');
  const video    = imgDiv ? imgDiv.querySelector('video') : null;

  /* Clear previous modal content */
  if (modalImg) {
    const prev = modalImg.querySelector('video');
    if (prev) { prev.pause(); prev.remove(); }
    modalImg.style.backgroundImage = '';
  }

  if (video && modalImg) {
    /* Card uses a video — clone it into the modal */
    const src = video.querySelector('source')?.src || '';
    const mv  = document.createElement('video');
    mv.autoplay   = true;
    mv.muted      = true;
    mv.loop       = true;
    mv.playsInline = true;
    mv.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;';
    const s   = document.createElement('source');
    s.src     = src;
    s.type    = 'video/mp4';
    mv.appendChild(s);
    modalImg.appendChild(mv);
  } else if (modalImg) {
    /* Card still uses a background image — use as before */
    modalImg.style.backgroundImage = imgDiv ? imgDiv.style.backgroundImage : '';
  }

  document.getElementById('pf-modal-badge').textContent = card.querySelector('.pf-card__badge')?.textContent || '';
  document.getElementById('pf-modal-title').textContent = card.querySelector('.pf-card__title')?.textContent || '';
  document.getElementById('pf-modal-meta').textContent  = card.querySelector('.pf-card__meta')?.textContent  || '';
  document.getElementById('pf-modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closePfModal() {
  const modalImg = document.getElementById('pf-modal-img');
  if (modalImg) {
    const v = modalImg.querySelector('video');
    if (v) { v.pause(); v.remove(); }
  }
  document.getElementById('pf-modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

/* ============================================================
   CINEMATIC INTRO — video plays then fades to homepage
============================================================ */

(function () {
  const screen   = document.getElementById('intro-screen');
  const video    = document.getElementById('intro-video');
  const content  = document.getElementById('intro-content');
  const tagline  = document.getElementById('intro-tagline');
  const bar      = document.getElementById('intro-bar');
  const skipBtn  = document.getElementById('intro-skip');

  if (!screen) return;

  // Prevent background scroll while intro plays
  document.body.classList.add('intro-active');

  function dismissIntro() {
    screen.classList.add('fade-out');
    document.body.classList.remove('intro-active');
    setTimeout(() => {
      screen.style.display = 'none';
    }, 1500);
  }

  // Animate logo in after 0.4s
  setTimeout(() => {
    content.classList.add('visible');
    tagline.classList.add('visible');
    bar.classList.add('animate');
  }, 400);

  // Auto dismiss after 5.5 seconds or when video ends
  const autoDismiss = setTimeout(dismissIntro, 5500);

  video.addEventListener('ended', () => {
    clearTimeout(autoDismiss);
    dismissIntro();
  });

  // Skip button
  skipBtn.addEventListener('click', () => {
    clearTimeout(autoDismiss);
    dismissIntro();
  });

  // Fallback — if video fails to load, dismiss after 4s
  video.addEventListener('error', () => {
    clearTimeout(autoDismiss);
    setTimeout(dismissIntro, 4000);
  });

})();

/* ============================================================
   RR LANDING + MENU SYSTEM
============================================================ */

// Prevent scroll while on landing
document.body.style.overflow = 'hidden';

// Open fullscreen menu overlay (video keeps playing underneath)
function openRRMenu() {
  document.getElementById('rr-menu-overlay').classList.add('open');
  // Hide centered content while menu is open
  const content = document.getElementById('rr-landing-content');
  if (content) content.style.opacity = '0';
  // Hide menu button while menu is open
  const menuBtn = document.getElementById('rr-menu-btn');
  if (menuBtn) menuBtn.style.opacity = '0';
}

// Close menu overlay — show landing content again
function closeRRMenu() {
  document.getElementById('rr-menu-overlay').classList.remove('open');
  const content = document.getElementById('rr-landing-content');
  if (content) content.style.opacity = '1';
  const menuBtn = document.getElementById('rr-menu-btn');
  if (menuBtn) menuBtn.style.opacity = '1';
}

// Enter site — Discover button
function enterSite() {
  const landing = document.getElementById('rr-landing');
  const site    = document.getElementById('rr-site');
  if (!landing || !site) return;
  landing.classList.add('exit');
  site.classList.add('visible');
  document.body.style.overflow = '';
  setTimeout(() => { landing.style.display = 'none'; }, 1400);
}

// Escape key closes menu
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeRRMenu();
});


/* ================================================================
   PRODUCTS FROM THE ADMIN DASHBOARD
   Loads the live catalogue from the backend. If the backend can't be
   reached, the built-in PRODUCTS list above stays on the page.
   ================================================================ */
function resolveProductImage(path) {
  if (!path) return '';
  if (path.startsWith('/api/')) return API_BASE + path;
  return path;
}

async function loadLiveProducts() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`${API_BASE}/api/products`, { signal: controller.signal });
    if (!res.ok) return;
    const data = await res.json();
    if (!Array.isArray(data.products) || data.products.length === 0) return;

    PRODUCTS = data.products.map((p) => ({
      ...p,
      image: resolveProductImage(p.image),
      sizes: p.sizes || [],
      prints: (p.prints || []).map((pr) => ({ ...pr, image: resolveProductImage(pr.image) || resolveProductImage(p.image) })),
    }));

    renderProductGrid('featured-products', PRODUCTS.slice(0, 4));
    const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
    renderProductGrid(
      'shop-products',
      activeFilter === 'all' ? PRODUCTS : PRODUCTS.filter((p) => p.category === activeFilter)
    );
  } catch (err) {
    /* Keep the built-in catalogue */
  } finally {
    clearTimeout(timer);
  }
}

loadLiveProducts();


/* ================================================================
   WEBSITE CONTENT FROM THE ADMIN DASHBOARD
   WhatsApp number, replaced photos and portfolio projects. If the
   backend can't be reached, the page keeps what is written in index.html.
   ================================================================ */
function applyWhatsAppNumber(number) {
  if (!number) return;
  WA_NUMBER = number;
  document.querySelectorAll('a[href*="wa.me/"]').forEach((a) => {
    a.href = a.href.replace(/wa\.me\/\d+/, 'wa.me/' + number);
  });
  if (typeof currentProduct !== 'undefined' && currentProduct) updateProductLinks(currentProduct.name);
}

function applySitePhotos(photos) {
  const paths = Object.keys(photos || {});
  if (!paths.length) return;
  const swap = (path) => {
    const decoded = decodeURI(path);
    return Object.prototype.hasOwnProperty.call(photos, decoded) ? resolveProductImage(photos[decoded]) : null;
  };
  document.querySelectorAll('img[src]').forEach((img) => {
    const next = swap(img.getAttribute('src'));
    if (next) img.src = next;
  });
  document.querySelectorAll('[style*="background-image"]').forEach((el) => {
    const m = el.style.backgroundImage.match(/url\(["']?([^"')]+)["']?\)/);
    const next = m && swap(m[1]);
    if (next) el.style.backgroundImage = `url("${next}")`;
  });
}

function renderPortfolio(items) {
  const grid = document.getElementById('pf-grid');
  if (!grid || !Array.isArray(items) || items.length === 0) return;
  const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  grid.innerHTML = items.map((it) => {
    const src = resolveProductImage(it.media);
    const media = it.mediaType === 'video'
      ? `<div class="pf-card__img" style="position:relative;overflow:hidden;">
           <video autoplay muted loop playsinline style="width:100%;height:100%;object-fit:cover;display:block;">
             <source src="${esc(src)}" type="video/mp4" />
           </video>`
      : `<div class="pf-card__img" style="background-image: url(&quot;${esc(src)}&quot;);">`;
    return `<article class="pf-card" data-category="${esc(it.category)}" onclick="openPfModal(this)">
        ${media}
          <div class="pf-card__overlay"><span class="pf-card__zoom">&#128269;</span></div>
          <span class="pf-card__badge">${esc(it.categoryLabel)}</span>
        </div>
        <div class="pf-card__body">
          <h3 class="pf-card__title">${esc(it.title)}</h3>
          <p class="pf-card__meta">${esc(it.meta)}</p>
        </div>
      </article>`;
  }).join('');

  /* Keep the filter buttons' counts and the active filter in step */
  document.querySelectorAll('.pf-filter').forEach((btn) => {
    const f = btn.dataset.filter;
    const n = f === 'all' ? items.length : items.filter((it) => it.category === f).length;
    btn.textContent = btn.textContent.replace(/\(\d+\)/, `(${n})`);
  });
  const active = document.querySelector('.pf-filter.active');
  if (active) active.click();
  else {
    const el = document.getElementById('pf-showing');
    if (el) el.textContent = `Showing ${items.length} of ${items.length}`;
  }
}

async function loadSiteContent() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`${API_BASE}/api/site`, { signal: controller.signal });
    if (!res.ok) return;
    const data = await res.json();
    applyWhatsAppNumber(data.settings && data.settings.whatsapp_number);
    applySitePhotos(data.photos);
    renderPortfolio(data.portfolio);
  } catch (err) {
    /* Keep the content written in index.html */
  } finally {
    clearTimeout(timer);
  }
}

loadSiteContent();
