# State Management with MobX

This boilerplate utilizes MobX for managing application state, particularly for complex state shared across multiple pages or components. We use the `mobx-miniprogram` and `mobx-miniprogram-bindings` libraries.

## Core Concepts

*   **Observable State:** Data that, when changed, should trigger UI updates. Defined using `observable`.
*   **Actions:** Functions that modify observable state. Defined using `action`. It's crucial to only modify state within actions for predictability.
*   **Computed Values:** Values derived from observable state. They update automatically when the underlying state changes. Defined using `computed` (via getters).
*   **Store:** A module (typically a JavaScript object) that encapsulates related observable state, actions, and computed values.
*   **Bindings:** The `mobx-miniprogram-bindings` library connects MobX stores to WeChat Miniprogram Pages or Components, automatically updating the `data` object when observable state changes.

## Boilerplate Stores

*   **`stores/configStore.js`**: Manages global application configuration fetched during startup (Base URLs, API Key, Auth Token) and the application's initialization readiness state (`isReady`, `initializationError`). Pages should check `isReady` before relying on this config.
*   **`stores/userStore.js`**: An example store managing user information (fetched via `invokeService.getUser`) and related loading/error states.

## Creating a New Store

1.  Create a new file in the `stores/` directory (e.g., `stores/productStore.js`).
2.  Import `observable`, `action`, `computed` from `mobx-miniprogram`.
3.  Define your state, actions, and computed values within an `observable` object.

```javascript
// stores/productStore.js
import { observable, action, computed } from 'mobx-miniprogram';
import { fetchProducts } from '@/services/productService'; // Example service import

export const productStore = observable({
  // --- State ---
  products: [],
  isLoading: false,
  error: null,
  filter: 'all', // Example filter state

  // --- Actions ---
  setProducts: action(function (products) {
    this.products = products;
  }),

  setLoading: action(function (loading) {
    this.isLoading = loading;
  }),

  setError: action(function (error) {
    this.error = error;
  }),

  setFilter: action(function (newFilter) {
    this.filter = newFilter;
    // Optionally re-fetch or re-filter data when filter changes
  }),

  fetchProductList: action(async function () {
    if (this.isLoading) return;
    this.setLoading(true);
    this.setError(null);
    try {
      const productList = await fetchProducts({ filter: this.filter }); // Pass filter
      this.setProducts(productList);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.setError(`Failed to fetch products: ${message}`);
      this.setProducts([]); // Clear products on error
    } finally {
      this.setLoading(false);
    }
  }),

  // --- Computed ---
  get filteredProducts() {
    if (this.filter === 'all') {
      return this.products;
    }
    // Example filtering logic
    return this.products.filter(p => p.category === this.filter);
  },

  get productCount() {
    return this.products.length;
  }
});
```

## Binding Stores to Pages/Components

Use `createStoreBindings` from `mobx-miniprogram-bindings` within the `onLoad` lifecycle method of a Page or the `attached` lifecycle method of a Component. **Crucially, always clean up the bindings in `onUnload` (Page) or `detached` (Component).**

```javascript
// Example Page: pages/products/list.js
import { createStoreBindings } from 'mobx-miniprogram-bindings';
import { productStore } from '@/stores/productStore';
import { configStore } from '@/stores/configStore'; // May need configStore too

const app = getApp();

Page({
  data: {
    // Data fields mapped from the store
    productList: [],
    isLoadingProducts: false,
    productError: null,
    currentFilter: 'all',
    // Other page data
  },

  // Store bindings instance (will be assigned in onLoad)
  storeBindings: null,

  async onLoad() {
    // Optional: Wait for app config if needed for API calls
    // await app.ensureConfigReady();

    this.storeBindings = createStoreBindings(this, {
      store: null, // Bind multiple stores
      fields: {
        // Map store state/getters to page data
        // Use functions to access store properties
        productList: () => productStore.filteredProducts, // Use computed value
        isLoadingProducts: () => productStore.isLoading,
        productError: () => productStore.error,
        currentFilter: () => productStore.filter,
        isConfigReady: () => configStore.isReady, // Example binding config
      },
      actions: {
        // Map actions (optional, can call store actions directly)
        // setFilter: productStore.setFilter,
      },
    });

    // Initial data fetch
    if (!productStore.products.length && !productStore.isLoading) {
        productStore.fetchProductList(); // Call action directly
    }
  },

  onUnload() {
    // Clean up bindings
    if (this.storeBindings && typeof this.storeBindings.destroyStoreBindings === 'function') {
      this.storeBindings.destroyStoreBindings();
    }
  },

  // --- Event Handlers ---
  handleFilterChange(event) {
    const newFilter = event.currentTarget.dataset.filter;
    // Call action directly (recommended for clarity)
    productStore.setFilter(newFilter);
    // Optionally trigger fetch after filter change
    productStore.fetchProductList();

    // Or call mapped action if defined in bindings:
    // if (typeof this.setFilter === 'function') {
    //   this.setFilter(newFilter);
    // }
  },

  handleRetry() {
      if (!this.data.isLoadingProducts) {
          productStore.fetchProductList();
      }
  }
});
```

**Key Binding Points:**

*   **`store: null`**: Allows binding fields/actions from multiple imported stores.
*   **`fields`**: Maps store state or computed getters to page `data`. Use arrow functions (`() => store.property`) to ensure reactivity.
*   **`actions`**: Optionally maps store actions to page methods. Calling actions directly on the imported store (`productStore.fetchProductList()`) is often clearer.
*   **Cleanup:** `destroyStoreBindings()` in `onUnload`/`detached` is **mandatory** to prevent memory leaks and unexpected behavior.

Refer to the `mobx-miniprogram-bindings` documentation for more advanced usage patterns.
