// Получение CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Добавление товара в корзину через API
async function addToCart(productId) {
    const csrftoken = getCookie('csrftoken');
    const url = '/api/cartitems/';
    const data = {
        product_id: productId,
        quantity: 1
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            showToast('Товар добавлен в корзину!', 'success');
            updateCartBadge();
        } else {
            const error = await response.json();
            showToast('Ошибка: ' + (error.detail || 'Не удалось добавить товар'), 'danger');
        }
    } catch (error) {
        showToast('Ошибка сети. Попробуйте позже.', 'danger');
    }
}

// Загрузка товаров через API и рендеринг
async function loadProducts(filters = {}) {
    const container = document.getElementById('product-grid');
    const spinner = document.getElementById('spinner');
    
    // Показываем спиннер
    if (spinner) spinner.style.display = 'block';
    container.innerHTML = '';

    // Формируем URL с параметрами
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.maker) params.append('maker', filters.maker);
    if (filters.search) params.append('search', filters.search);
    if (filters.page) params.append('page', filters.page);

    const url = '/api/products/?' + params.toString();

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Ошибка загрузки товаров');
        const data = await response.json();

        // Отрисовка карточек
        if (data.results && data.results.length > 0) {
            data.results.forEach(product => {
                const col = document.createElement('div');
                col.className = 'col-sm-6 col-md-4 col-lg-4 mb-4';
                col.innerHTML = `
                    <div class="card product-card h-100">
                        ${product.photo ? `<img src="${product.photo}" class="card-img-top" alt="${product.name}">` : `<img src="/media/default.jpg" class="card-img-top" alt="Нет фото">`}
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">${product.name}</h5>
                            <p class="card-text text-muted">${product.definition ? product.definition.slice(0, 80) + '...' : ''}</p>
                            <p class="price mt-auto">${product.price} руб.</p>
                            <div class="mt-2">
                                <a href="/product/${product.id}/" class="btn btn-outline-primary btn-sm">Подробнее</a>
                                <button class="btn btn-primary btn-sm add-to-cart" data-id="${product.id}">В корзину</button>
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            });

            // Пагинация
            if (data.next) {
                // Кнопка "Загрузить ещё" или пагинация – реализуем простую кнопку
                // Можно добавить в конец контейнера
            }
        } else {
            container.innerHTML = '<p class="text-center">Товары не найдены</p>';
        }
    } catch (error) {
        container.innerHTML = '<p class="text-center text-danger">Ошибка загрузки товаров</p>';
    } finally {
        if (spinner) spinner.style.display = 'none';
    }

    // Навешиваем обработчики на кнопки "В корзину"
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.id;
            addToCart(productId);
        });
    });
}

// Обновление значка корзины (количество товаров)
async function updateCartBadge() {
    try {
        const response = await fetch('/api/carts/');
        if (response.ok) {
            const data = await response.json();
            if (data.results && data.results.length > 0) {
                const cart = data.results[0];
                const totalItems = cart.items ? cart.items.reduce((sum, item) => sum + item.quantity, 0) : 0;
                const badge = document.getElementById('cart-badge');
                if (badge) {
                    badge.textContent = totalItems;
                    badge.style.display = totalItems > 0 ? 'inline' : 'none';
                }
            }
        }
    } catch (e) {}
}

// Уведомления (Bootstrap Toast)
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
    toast.role = 'alert';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Если мы на странице каталога – загружаем товары
    const catalogContainer = document.getElementById('product-grid');
    if (catalogContainer) {
        const filters = {};
        // Читаем параметры из URL
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('category')) filters.category = urlParams.get('category');
        if (urlParams.has('maker')) filters.maker = urlParams.get('maker');
        if (urlParams.has('search')) filters.search = urlParams.get('search');
        loadProducts(filters);
    }

    // Обновляем значок корзины
    updateCartBadge();

    // Обработчик для формы фильтров на странице каталога
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const params = new URLSearchParams();
            for (let [key, value] of formData.entries()) {
                if (value) params.append(key, value);
            }
            window.location.search = params.toString();
        });
    }
});