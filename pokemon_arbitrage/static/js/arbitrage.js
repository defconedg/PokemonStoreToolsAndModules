/**
 * Main functionality for Pokemon Card Arbitrage Tool UI
 */
import API from "./api.js";

// DOM elements
let cardSearchForm, resultsContainer, loadingIndicator;

/**
 * Initialize the application
 */
function init() {
  // Get DOM elements
  cardSearchForm = document.getElementById("card-search-form");
  resultsContainer = document.getElementById("results-container");
  loadingIndicator = document.getElementById("loading-indicator");

  // Add event listeners
  cardSearchForm.addEventListener("submit", handleCardSearch);

  // Initialize any tooltips or UI components
  initUIComponents();
}

/**
 * Handle the card search form submission
 * @param {Event} event - Form submission event
 */
async function handleCardSearch(event) {
  event.preventDefault();
  showLoading(true);

  try {
    // Get form data
    const formData = new FormData(cardSearchForm);
    const cardName = formData.get("card-name");
    const setName = formData.get("set-name");
    const cardNumber = formData.get("card-number");

    // Get card data from an external API or local source
    const cardData = await fetchCardData(cardName, setName, cardNumber);

    if (!cardData) {
      displayError("Card not found. Please check your search criteria.");
      return;
    }

    // Get arbitrage data from our API
    const arbitrageData = await API.getCardPrices(cardData);

    // Display the results
    displayArbitrageResults(arbitrageData);
  } catch (error) {
    displayError(`Error: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Display arbitrage results in the UI
 * @param {Object} data - Arbitrage data from API
 */
function displayArbitrageResults(data) {
  if (!data.success) {
    displayError(data.error || "Failed to get arbitrage data");
    return;
  }

  resultsContainer.innerHTML = "";

  if (!data.has_arbitrage) {
    resultsContainer.innerHTML = `
            <div class="alert alert-info">
                No arbitrage opportunities found for ${data.card_name} (${data.set_name}).
            </div>
        `;
    return;
  }

  // Create results header
  const header = document.createElement("div");
  header.className = "results-header";
  header.innerHTML = `
        <h3>Arbitrage Opportunities for ${data.card_name}</h3>
        <p>Set: ${data.set_name} | Opportunities found: ${data.opportunities_count}</p>
    `;
  resultsContainer.appendChild(header);

  // Create opportunities table
  const table = document.createElement("table");
  table.className = "opportunities-table";

  // Add table header
  table.innerHTML = `
        <thead>
            <tr>
                <th>Buy From</th>
                <th>Buy Price</th>
                <th>Sell To</th>
                <th>Sell Price</th>
                <th>Profit</th>
                <th>Margin</th>
            </tr>
        </thead>
        <tbody id="opportunities-body">
        </tbody>
    `;
  resultsContainer.appendChild(table);

  const tbody = document.getElementById("opportunities-body");

  // Add each opportunity to the table
  data.opportunities.forEach((opp) => {
    const row = document.createElement("tr");
    row.innerHTML = `
            <td>${opp.buy_from.source} (${opp.buy_from.price_type})</td>
            <td>$${opp.buy_price.toFixed(2)}</td>
            <td>${opp.sell_to.source} (${opp.sell_to.price_type})</td>
            <td>$${opp.sell_price.toFixed(2)}</td>
            <td>$${opp.profit.toFixed(2)}</td>
            <td>${opp.profit_margin.toFixed(1)}%</td>
        `;
    tbody.appendChild(row);
  });
}

/**
 * Display error message
 * @param {string} message - Error message to display
 */
function displayError(message) {
  resultsContainer.innerHTML = `
        <div class="alert alert-danger">
            ${message}
        </div>
    `;
}

/**
 * Show or hide loading indicator
 * @param {boolean} isLoading - Whether loading is in progress
 */
function showLoading(isLoading) {
  loadingIndicator.style.display = isLoading ? "block" : "none";

  // Disable/enable forms during loading
  cardSearchForm.querySelectorAll("input, button").forEach((elem) => {
    elem.disabled = isLoading;
  });
}

/**
 * Initialize UI components like tooltips, etc.
 */
function initUIComponents() {
  // Initialize any UI libraries (e.g., tooltips, modals)
  // Code omitted for brevity
}

/**
 * Fetch card data from external API
 * @param {string} cardName - Name of the card
 * @param {string} setName - Name of the card set
 * @param {string} cardNumber - Card number in set
 * @returns {Object} Card data
 */
async function fetchCardData(cardName, setName, cardNumber) {
  try {
    const response = await fetch(
      `https://api.pokemontcg.io/v2/cards?q=name:"${cardName}" set.name:"${setName}" number:${cardNumber}`
    );
    const data = await response.json();
    return data.data && data.data.length > 0 ? data.data[0] : null;
  } catch (error) {
    console.error("Error fetching card data:", error);
    throw new Error("Failed to fetch card data from external API");
  }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", init);

// Export functions for testing or external use
export { handleCardSearch, displayArbitrageResults };
