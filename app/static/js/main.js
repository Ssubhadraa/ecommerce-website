document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-add-to-cart]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: formData,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        });
        const data = await response.json();
        if (data.success) {
          showToast(data.message);
          const badge = document.getElementById('cart-badge');
          if (badge) badge.textContent = data.cart_count;
        } else {
          showToast(data.message || 'Could not add to cart', true);
        }
      } catch (err) {
        showToast('Something went wrong', true);
      }
    });
  });

  document.querySelectorAll('[data-wishlist-toggle]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: formData,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        });
        const data = await response.json();
        if (data.success) {
          showToast(data.message);
          const badge = document.getElementById('wishlist-badge');
          if (badge) badge.textContent = data.wishlist_count;
          const btn = form.querySelector('button[type="submit"]');
          if (btn) {
            btn.classList.toggle('is-active', data.in_wishlist);
            btn.textContent = data.in_wishlist
              ? (btn.textContent.includes('Wishlisted') ? '♥ Wishlisted' : '♥ In Wishlist')
              : (btn.textContent.includes('Wishlisted') ? '♡ Wishlist' : '♡ Add to Wishlist');
          }
        } else {
          showToast(data.message || 'Could not update wishlist', true);
        }
      } catch (err) {
        showToast('Something went wrong', true);
      }
    });
  });
});

function showToast(message, isError = false) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  if (isError) toast.style.background = '#b12704';
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
